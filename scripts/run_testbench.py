#!/usr/bin/env python3
"""Run search evaluation testbench against local or Azure-backed search."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from foundry_docs_mcp.foundry_client import FoundryProjectOpenAI
from foundry_docs_mcp.indexer import AzureSearchIndex, SearchIndex

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(os.environ.get("FOUNDRY_DOCS_DIR", PROJECT_ROOT / "docs"))
TEST_FILE = PROJECT_ROOT / "tests" / "search_testbench.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run search relevance testbench")
    parser.add_argument("--test-file", default=str(TEST_FILE), help="Path to testbench JSON file")
    parser.add_argument("--top-k", type=int, default=10, help="Top-k results to validate against")
    parser.add_argument("--min-pass-rate", type=float, default=1.0, help="Minimum required pass rate (0.0-1.0)")
    parser.add_argument("--min-tests", type=int, default=1, help="Minimum number of test cases required")
    return parser.parse_args()


def build_search_runner():
    if os.environ.get("AZURE_SEARCH_ENDPOINT"):
        endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
        index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "foundry-docs")
        api_key = os.environ.get("AZURE_SEARCH_API_KEY")
        project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
        embedding_model = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        foundry_client = FoundryProjectOpenAI(
            project_endpoint=project_endpoint,
            embedding_model=embedding_model,
            api_key=os.environ.get("AZURE_AI_PROJECT_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY"),
        )

        azure_index = AzureSearchIndex(endpoint=endpoint, index_name=index_name, api_key=api_key)

        def embed_query(query: str) -> list[float]:
            return foundry_client.embed_query(query)

        return lambda q, limit: azure_index.search(q, limit=limit, embedding_fn=embed_query)

    local = SearchIndex()
    local.load_from_directory(DOCS_DIR)
    return lambda q, limit: local.search(q, limit=limit)


def main():
    args = _parse_args()
    test_file = Path(args.test_file)

    if not test_file.exists():
        raise FileNotFoundError(f"Missing testbench file: {test_file}")

    cases = json.loads(test_file.read_text(encoding="utf-8"))
    if len(cases) < args.min_tests:
        print(
            f"\nSummary: insufficient tests ({len(cases)}) < min-tests ({args.min_tests})",
            file=sys.stderr,
        )
        raise SystemExit(2)

    search = build_search_runner()

    passed = 0
    for idx, case in enumerate(cases, start=1):
        query = case["query"]
        expected_paths = case.get("expected_paths", [])
        min_results = int(case.get("min_results", 1))

        results = search(query, limit=max(args.top_k, 1))
        paths = [row.get("path", "") for row in results]
        hit = any(expected in paths for expected in expected_paths)
        enough = len(results) >= min_results
        ok = hit and enough
        passed += 1 if ok else 0

        print(
            f"[{idx}/{len(cases)}] {'PASS' if ok else 'FAIL'} "
            f"query={query!r} expected={expected_paths} top={paths[:5]}"
        )

    pass_rate = passed / max(len(cases), 1)
    print(f"\nSummary: {passed}/{len(cases)} passed ({pass_rate * 100:.1f}%)")

    if pass_rate < args.min_pass_rate:
        print(
            f"Gate failed: pass_rate={pass_rate:.3f} < min_pass_rate={args.min_pass_rate:.3f}",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
