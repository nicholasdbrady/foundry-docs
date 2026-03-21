#!/usr/bin/env python3
"""A/B/C/D evaluation harness for comparing documentation MCP servers.

Runs the same search queries against four backends and compares relevance
and content completeness:

  A — Microsoft Docs remote API (learn.microsoft.com)
  B — Mintlify built-in search API
  C — Local foundry-docs index  (docs/)
  D — Local foundry-docs-vnext index  (docs-vnext/)

Usage:
    python scripts/run_abcd_eval.py [--test-file tests/search_testbench.json] [--top-k 10]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Protocol

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from foundry_docs_mcp.indexer import AzureSearchIndex, SearchIndex  # noqa: E402
from foundry_docs_mcp.foundry_client import FoundryProjectOpenAI  # noqa: E402

try:
    import httpx
except ImportError:
    httpx = None

TEST_FILE = PROJECT_ROOT / "tests" / "search_testbench.json"
OUTPUT_FILE = PROJECT_ROOT / "telemetry" / "abcd_eval_results.json"


# ---------------------------------------------------------------------------
# Backend protocol
# ---------------------------------------------------------------------------

class SearchBackend(Protocol):
    name: str
    label: str

    def search(self, query: str, limit: int) -> list[dict]:
        """Return list of dicts with at least 'path', 'title', and 'snippet_chars' keys.

        'snippet_chars' is the total character count of content returned inline
        with the search results (descriptions, content excerpts, etc.).
        """
        ...

    def get_content(self, path: str) -> str | None:
        """Return the full content of a doc page (or None if unavailable).

        For remote backends, this may involve a web fetch (simulating an
        agent's second tool call).
        """
        ...


# ---------------------------------------------------------------------------
# Backend implementations
# ---------------------------------------------------------------------------

class LocalDocsBackend:
    """Searches the local TF-IDF index for a given docs directory."""

    def __init__(self, docs_dir: str | Path, docs_json: str | Path, *, label: str, name: str):
        self.name = name
        self.label = label
        self.docs_dir = Path(docs_dir)
        self.docs_json_path = Path(docs_json)
        self._index: SearchIndex | None = None

    def _ensure_index(self) -> SearchIndex:
        if self._index is None:
            self._index = SearchIndex()
            self._index.load_from_directory(self.docs_dir)
        return self._index

    def search(self, query: str, limit: int) -> list[dict]:
        idx = self._ensure_index()
        results = idx.search(query, limit=limit)
        # Local backends return full content inline — measure it
        for r in results:
            content = self.get_content(r.get("path", ""))
            r["snippet_chars"] = len(content) if content else 0
        return results

    def get_content(self, path: str) -> str | None:
        idx = self._ensure_index()
        clean = path.lstrip("/").removesuffix(".mdx")
        doc = idx.docs.get(clean)
        if doc:
            return doc["content"]
        # Fuzzy match on filename stem
        target = clean.split("/")[-1]
        for doc_path, doc_data in idx.docs.items():
            if doc_path.endswith(f"/{target}") or doc_path == target:
                return doc_data["content"]
        return None


class MicrosoftDocsBackend:
    """Calls the Microsoft Learn search API, scoped to Foundry docs."""

    SEARCH_URL = "https://learn.microsoft.com/api/search"
    name = "microsoft-docs"
    label = "A: Microsoft Docs"

    def search(self, query: str, limit: int) -> list[dict]:
        if httpx is None:
            return []
        try:
            resp = httpx.get(
                self.SEARCH_URL,
                params={
                    "search": f"foundry {query}",
                    "locale": "en-us",
                    "facet": "category",
                    "$filter": "category eq 'Documentation'",
                    "$top": limit,
                    "scope": "Azure",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        results = []
        for item in data.get("results", []):
            url = item.get("url", "")
            title = item.get("title", "")
            description = _strip_html(item.get("description", ""))
            path = _extract_path_from_ms_url(url)
            results.append({
                "path": path,
                "title": _strip_html(title),
                "description": description,
                "url": url,
                "snippet_chars": len(description),
                "score": 0.0,
            })
        return results[:limit]

    def get_content(self, path: str) -> str | None:
        """Fetch the full page from learn.microsoft.com (simulates agent web fetch)."""
        if httpx is None:
            return None
        url = f"https://learn.microsoft.com/en-us/azure/foundry/{path}"
        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            text = resp.text
            # Extract main content — strip HTML to approximate what an agent sees
            main_match = re.search(r'<main[^>]*>(.*?)</main>', text, re.DOTALL)
            if main_match:
                text = main_match.group(1)
            text = _strip_html(text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text if len(text) > 200 else None
        except Exception:
            return None


class MintlifyBackend:
    """Calls the Mintlify MCP search tool via JSON-RPC over HTTP."""

    name = "mintlify"
    label = "B: Mintlify"

    def __init__(self):
        self.subdomain = os.environ.get("MINTLIFY_SUBDOMAIN", "")

    def search(self, query: str, limit: int) -> list[dict]:
        if not self.subdomain or httpx is None:
            return []
        try:
            resp = httpx.post(
                f"https://{self.subdomain}.mintlify.app/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "search_microsoft_foundry_docs",
                        "arguments": {"query": query},
                    },
                    "id": 1,
                },
                timeout=15,
            )
            resp.raise_for_status()
            # Response is SSE: "event: message\ndata: {json}\n\n"
            raw = resp.text
            data_line = ""
            for line in raw.splitlines():
                if line.startswith("data: "):
                    data_line = line[6:]
                    break
            if not data_line:
                return []
            data = json.loads(data_line)
        except Exception:
            return []

        results = []
        for content_item in data.get("result", {}).get("content", []):
            text = content_item.get("text", "")
            # Extract title, link, and content snippet from structured text
            title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
            link_match = re.search(r"^Link:\s*(.+)$", text, re.MULTILINE)
            content_match = re.search(r"^Content:\s*(.+)", text, re.MULTILINE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            link = link_match.group(1).strip() if link_match else ""
            snippet = _strip_html(content_match.group(1).strip()) if content_match else ""
            # Extract path from the Mintlify URL
            path = ""
            if link:
                url_match = re.search(r"mintlify\.app/(.+?)(?:\?|#|$)", link)
                if url_match:
                    path = url_match.group(1).rstrip("/")
            if path:
                results.append({
                    "path": path,
                    "title": title,
                    "description": snippet,
                    "snippet_chars": len(snippet),
                    "score": 0.0,
                })
        return results[:limit]

    def get_content(self, path: str) -> str | None:
        """Fetch the full page from Mintlify (simulates agent web fetch)."""
        if not self.subdomain or httpx is None:
            return None
        url = f"https://{self.subdomain}.mintlify.app/{path}"
        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            text = resp.text
            # Extract main content area
            main_match = re.search(r'<main[^>]*>(.*?)</main>', text, re.DOTALL)
            if main_match:
                text = main_match.group(1)
            text = _strip_html(text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text if len(text) > 200 else None
        except Exception:
            return None


class AzureHybridBackend:
    """Searches the Azure AI Search hybrid index (keyword + vector + semantic)."""

    def __init__(self, docs_dir: Path, *, label: str, name: str, index_name: str):
        self.name = name
        self.label = label
        self.docs_dir = docs_dir
        self._index_name = index_name
        self._local_index: SearchIndex | None = None
        self._azure_index: AzureSearchIndex | None = None
        self._foundry_client: FoundryProjectOpenAI | None = None

    def _ensure(self):
        if self._azure_index is not None:
            return
        self._azure_index = AzureSearchIndex(
            endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
            index_name=self._index_name,
            api_key=os.environ.get("AZURE_SEARCH_API_KEY"),
        )
        self._foundry_client = FoundryProjectOpenAI(
            project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            embedding_model=os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
            api_key=os.environ.get("AZURE_AI_PROJECT_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY"),
        )
        self._local_index = SearchIndex()
        self._local_index.load_from_directory(self.docs_dir)

    def search(self, query: str, limit: int) -> list[dict]:
        self._ensure()
        results = self._azure_index.search(
            query=query, limit=limit, embedding_fn=self._foundry_client.embed_query,
        )
        for r in results:
            content = self.get_content(r.get("path", ""))
            r["snippet_chars"] = len(content) if content else 0
        return results

    def get_content(self, path: str) -> str | None:
        self._ensure()
        clean = path.lstrip("/").removesuffix(".mdx")
        doc = self._local_index.docs.get(clean)
        if doc:
            return doc["content"]
        target = clean.split("/")[-1]
        for doc_path, doc_data in self._local_index.docs.items():
            if doc_path.endswith(f"/{target}") or doc_path == target:
                return doc_data["content"]
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def _extract_path_from_ms_url(url: str) -> str:
    """Extract a doc-relative path from a learn.microsoft.com URL."""
    # e.g. https://learn.microsoft.com/en-us/azure/ai-foundry/agents/development/overview
    match = re.search(r"/azure/(?:ai-foundry|foundry)/(.+?)(?:\?|#|$)", url)
    if match:
        return match.group(1).rstrip("/")
    return url


# ---------------------------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------------------------

@dataclass
class QueryResult:
    query: str
    expected_paths: list[str]
    backend: str
    paths_returned: list[str]
    hit: bool
    rank: int | None  # 1-based rank of first expected hit, None if miss
    result_count: int
    latency_ms: float
    snippet_chars: int = 0  # total inline content chars from search results


@dataclass
class ContentComparisonResult:
    path: str
    backend: str
    available: bool
    char_count: int = 0
    heading_count: int = 0
    code_block_count: int = 0


@dataclass
class RetrievalSufficiencyResult:
    """Measures whether the LLM can answer from search alone vs needing a second fetch."""
    query: str
    backend: str
    hit: bool  # did search find an expected path?
    snippet_chars: int = 0  # inline content chars from the search response
    one_step_sufficient: bool = False  # hit + substantial inline content (≥500 chars)
    two_step_content: bool = False  # can get_content() fetch the full doc?
    two_step_chars: int = 0  # char count from get_content()
    two_step_sufficient: bool = False  # hit + get_content() succeeded


@dataclass
class EvalReport:
    test_count: int = 0
    backend_results: dict[str, list[dict]] = field(default_factory=dict)
    content_comparisons: list[dict] = field(default_factory=list)
    summary: dict[str, dict] = field(default_factory=dict)


def _count_headings(content: str) -> int:
    return len(re.findall(r"^#{1,6}\s+", content, re.MULTILINE))


def _count_code_blocks(content: str) -> int:
    return len(re.findall(r"```", content)) // 2


def compute_hit_at_k(results: list[QueryResult]) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results if r.hit) / len(results)


def compute_mrr(results: list[QueryResult]) -> float:
    if not results:
        return 0.0
    total = 0.0
    for r in results:
        if r.rank is not None:
            total += 1.0 / r.rank
    return total / len(results)


def compute_retrieval_sufficiency(results: list[RetrievalSufficiencyResult], *, two_step: bool = False) -> float:
    """Fraction of queries where retrieval was sufficient.

    one_step: search found the doc AND returned substantial inline content (≥500 chars).
    two_step: search found the doc AND a subsequent fetch retrieved the full page.
    """
    if not results:
        return 0.0
    attr = "two_step_sufficient" if two_step else "one_step_sufficient"
    return sum(1 for r in results if getattr(r, attr)) / len(results)


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def build_backends() -> list[SearchBackend]:
    backends: list[SearchBackend] = []

    # A: Microsoft Docs
    if httpx is not None:
        backends.append(MicrosoftDocsBackend())

    # B: Mintlify
    mintlify = MintlifyBackend()
    if mintlify.subdomain:
        backends.append(mintlify)

    # C: Local docs/
    docs_dir = Path(os.environ.get("FOUNDRY_DOCS_DIR", PROJECT_ROOT / "docs"))
    docs_json = Path(os.environ.get("FOUNDRY_DOCS_JSON", PROJECT_ROOT / "docs.json"))
    if docs_dir.is_dir():
        backends.append(LocalDocsBackend(docs_dir, docs_json, label="C: foundry-docs", name="foundry-docs"))

    # D: Local docs-vnext/
    vnext_dir = Path(os.environ.get("FOUNDRY_VNEXT_DOCS_DIR", PROJECT_ROOT / "docs-vnext"))
    vnext_json = Path(os.environ.get("FOUNDRY_VNEXT_DOCS_JSON", PROJECT_ROOT / "docs-vnext" / "docs.json"))
    if vnext_dir.is_dir():
        backends.append(
            LocalDocsBackend(vnext_dir, vnext_json, label="D: foundry-docs-vnext", name="foundry-docs-vnext")
        )

    # E/F: Azure hybrid search (when credentials are available)
    if os.environ.get("AZURE_SEARCH_ENDPOINT") and os.environ.get("AZURE_AI_PROJECT_ENDPOINT"):
        if docs_dir.is_dir():
            backends.append(AzureHybridBackend(
                docs_dir, label="E: foundry-docs-hybrid", name="foundry-docs-hybrid",
                index_name=os.environ.get("AZURE_SEARCH_INDEX_NAME", "foundry-docs"),
            ))
        if vnext_dir.is_dir():
            backends.append(AzureHybridBackend(
                vnext_dir, label="F: foundry-docs-vnext-hybrid", name="foundry-docs-vnext-hybrid",
                index_name=os.environ.get("AZURE_SEARCH_VNEXT_INDEX_NAME", "foundry-docs-vnext"),
            ))

    return backends


def run_search_eval(
    backends: list[SearchBackend],
    cases: list[dict],
    top_k: int,
) -> dict[str, list[QueryResult]]:
    """Run all test cases against all backends, return results grouped by backend."""
    all_results: dict[str, list[QueryResult]] = {b.name: [] for b in backends}

    for case in cases:
        query = case["query"]
        expected_paths = case.get("expected_paths", [])

        for backend in backends:
            started = time.perf_counter()
            try:
                results = backend.search(query, limit=top_k)
            except Exception:
                results = []
            latency_ms = (time.perf_counter() - started) * 1000

            paths = [r.get("path", "") for r in results]
            total_snippet_chars = sum(r.get("snippet_chars", 0) for r in results)
            rank = None
            hit = False
            for expected in expected_paths:
                for idx, p in enumerate(paths):
                    if p == expected or p.endswith(f"/{expected.split('/')[-1]}"):
                        hit = True
                        candidate_rank = idx + 1
                        if rank is None or candidate_rank < rank:
                            rank = candidate_rank
                        break
                if hit:
                    break

            all_results[backend.name].append(QueryResult(
                query=query,
                expected_paths=expected_paths,
                backend=backend.name,
                paths_returned=paths[:5],
                hit=hit,
                rank=rank,
                result_count=len(results),
                latency_ms=round(latency_ms, 1),
                snippet_chars=total_snippet_chars,
            ))

    return all_results


def run_content_eval(
    backends: list[SearchBackend],
    cases: list[dict],
) -> list[ContentComparisonResult]:
    """Compare content availability and richness across backends."""
    comparisons: list[ContentComparisonResult] = []
    paths_seen: set[str] = set()

    for case in cases:
        for path in case.get("expected_paths", []):
            if path in paths_seen:
                continue
            paths_seen.add(path)

            for backend in backends:
                content = backend.get_content(path)
                if content:
                    comparisons.append(ContentComparisonResult(
                        path=path,
                        backend=backend.name,
                        available=True,
                        char_count=len(content),
                        heading_count=_count_headings(content),
                        code_block_count=_count_code_blocks(content),
                    ))
                else:
                    comparisons.append(ContentComparisonResult(
                        path=path,
                        backend=backend.name,
                        available=False,
                    ))

    return comparisons


def run_retrieval_sufficiency_eval(
    backends: list[SearchBackend],
    cases: list[dict],
    search_results: dict[str, list[QueryResult]],
) -> dict[str, list[RetrievalSufficiencyResult]]:
    """For each query×backend, measure 1-step and 2-step retrieval sufficiency.

    1-step: Did the search response alone provide enough content (≥500 chars)?
    2-step: Can a follow-up get_content() fetch retrieve the full page?
    """
    one_step_threshold = 500  # chars — enough context for a useful LLM answer
    all_results: dict[str, list[RetrievalSufficiencyResult]] = {b.name: [] for b in backends}

    for case in cases:
        query = case["query"]
        expected_paths = case.get("expected_paths", [])

        for backend in backends:
            qr = next(
                (r for r in search_results.get(backend.name, []) if r.query == query),
                None,
            )
            hit = qr.hit if qr else False
            snippet_chars = qr.snippet_chars if qr else 0

            # 1-step: search returned a hit with substantial inline content
            one_step = hit and snippet_chars >= one_step_threshold

            # 2-step: simulate agent fetching the full page after search
            two_step_content = False
            two_step_chars = 0
            if hit:
                for expected in expected_paths:
                    content = backend.get_content(expected)
                    if content:
                        two_step_content = True
                        two_step_chars = len(content)
                        break

            all_results[backend.name].append(RetrievalSufficiencyResult(
                query=query,
                backend=backend.name,
                hit=hit,
                snippet_chars=snippet_chars,
                one_step_sufficient=one_step,
                two_step_content=two_step_content,
                two_step_chars=two_step_chars,
                two_step_sufficient=hit and two_step_content,
            ))

    return all_results


def print_summary(
    backends: list[SearchBackend],
    search_results: dict[str, list[QueryResult]],
    content_results: list[ContentComparisonResult],
    sufficiency_results: dict[str, list[RetrievalSufficiencyResult]],
):
    """Print a summary table to stdout."""
    print("\n" + "=" * 80)
    print("A/B/C/D EVALUATION SUMMARY")
    print("=" * 80)

    # Search relevance table
    print("\n--- Search Relevance ---\n")
    header = f"{'Backend':<30} {'Hit@K':>8} {'MRR':>8} {'Avg Latency':>12} {'Queries':>8}"
    print(header)
    print("-" * len(header))

    for backend in backends:
        results = search_results.get(backend.name, [])
        if not results:
            continue
        hit_rate = compute_hit_at_k(results)
        mrr = compute_mrr(results)
        avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0
        print(
            f"{backend.label:<30} {hit_rate:>7.1%} {mrr:>8.3f} "
            f"{avg_latency:>10.1f}ms {len(results):>8}"
        )

    # Retrieval sufficiency table
    print("\n--- Retrieval Sufficiency ---\n")
    print("  1-step: search hit + ≥500 chars inline content (no second tool call needed)")
    print("  2-step: search hit + full page via follow-up fetch (agent does a second call)")
    print()
    header = (
        f"{'Backend':<30} {'Hit@K':>8} {'1-Step':>8} {'2-Step':>8} "
        f"{'Snip Chars':>11} {'Fetch Chars':>11}"
    )
    print(header)
    print("-" * len(header))

    for backend in backends:
        items = sufficiency_results.get(backend.name, [])
        if not items:
            continue
        hit_rate = sum(1 for r in items if r.hit) / len(items) if items else 0
        one_step = compute_retrieval_sufficiency(items, two_step=False)
        two_step = compute_retrieval_sufficiency(items, two_step=True)
        hit_items = [r for r in items if r.hit]
        avg_snippet = sum(r.snippet_chars for r in hit_items) / max(len(hit_items), 1)
        fetched_items = [r for r in items if r.two_step_content]
        avg_fetch = sum(r.two_step_chars for r in fetched_items) / max(len(fetched_items), 1)
        print(
            f"{backend.label:<30} {hit_rate:>7.1%} {one_step:>7.1%} {two_step:>7.1%} "
            f"{avg_snippet:>11.0f} {avg_fetch:>11.0f}"
        )

    # Content completeness table
    print("\n--- Content Completeness ---\n")
    header = f"{'Backend':<30} {'Available':>10} {'Avg Chars':>10} {'Avg Headings':>13} {'Avg Code':>9}"
    print(header)
    print("-" * len(header))

    for backend in backends:
        items = [c for c in content_results if c.backend == backend.name]
        if not items:
            continue
        avail = sum(1 for c in items if c.available)
        avail_items = [c for c in items if c.available]
        avg_chars = sum(c.char_count for c in avail_items) / max(len(avail_items), 1)
        avg_heads = sum(c.heading_count for c in avail_items) / max(len(avail_items), 1)
        avg_code = sum(c.code_block_count for c in avail_items) / max(len(avail_items), 1)
        print(
            f"{backend.label:<30} {avail:>5}/{len(items):<4} {avg_chars:>10.0f} "
            f"{avg_heads:>13.1f} {avg_code:>9.1f}"
        )

    # Per-query detail
    print("\n--- Per-Query Results ---\n")
    for backend in backends:
        results = search_results.get(backend.name, [])
        for r in results:
            status = "PASS" if r.hit else "FAIL"
            rank_str = f"rank={r.rank}" if r.rank else "miss"
            print(
                f"  [{backend.label}] {status} query={r.query!r} "
                f"expected={r.expected_paths} {rank_str} top={r.paths_returned[:3]}"
            )

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="A/B/C/D documentation MCP server evaluation")
    parser.add_argument("--test-file", default=str(TEST_FILE), help="Path to testbench JSON file")
    parser.add_argument("--top-k", type=int, default=10, help="Top-K results to evaluate against")
    parser.add_argument("--output", default=str(OUTPUT_FILE), help="Path for JSON output report")
    args = parser.parse_args()

    test_file = Path(args.test_file)
    if not test_file.exists():
        print(f"Error: test file not found: {test_file}", file=sys.stderr)
        raise SystemExit(1)

    cases = json.loads(test_file.read_text(encoding="utf-8"))
    print(f"Loaded {len(cases)} test cases from {test_file}")

    backends = build_backends()
    if not backends:
        print("Error: no backends available", file=sys.stderr)
        raise SystemExit(1)

    print(f"Active backends: {', '.join(b.label for b in backends)}")

    # Run evaluations
    search_results = run_search_eval(backends, cases, args.top_k)
    content_results = run_content_eval(backends, cases)
    sufficiency_results = run_retrieval_sufficiency_eval(backends, cases, search_results)

    # Print summary
    print_summary(backends, search_results, content_results, sufficiency_results)

    # Build JSON report
    report = EvalReport(
        test_count=len(cases),
        backend_results={
            name: [asdict(r) for r in results]
            for name, results in search_results.items()
        },
        content_comparisons=[asdict(c) for c in content_results],
        summary={
            b.name: {
                "label": b.label,
                "hit_at_k": round(compute_hit_at_k(search_results.get(b.name, [])), 4),
                "mrr": round(compute_mrr(search_results.get(b.name, [])), 4),
                "one_step_sufficiency": round(
                    compute_retrieval_sufficiency(sufficiency_results.get(b.name, []), two_step=False), 4
                ),
                "two_step_sufficiency": round(
                    compute_retrieval_sufficiency(sufficiency_results.get(b.name, []), two_step=True), 4
                ),
                "queries": len(search_results.get(b.name, [])),
            }
            for b in backends
        },
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    print(f"\nFull report written to: {output_path}")


if __name__ == "__main__":
    main()
