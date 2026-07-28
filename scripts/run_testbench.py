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
from post_index_regression import build_execution_result, write_result

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(os.environ.get("FOUNDRY_DOCS_DIR", PROJECT_ROOT / "docs"))
TEST_FILE = PROJECT_ROOT / "tests" / "search_testbench.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run search relevance testbench")
    parser.add_argument("--test-file", default=str(TEST_FILE), help="Path to testbench JSON file")
    parser.add_argument("--top-k", type=int, default=10, help="Top-k results to validate against")
    parser.add_argument("--min-pass-rate", type=float, default=1.0, help="Minimum required pass rate (0.0-1.0)")
    parser.add_argument("--min-tests", type=int, default=1, help="Minimum number of test cases required")
    parser.add_argument("--output-json", type=Path, help="Write the versioned machine-readable result to this path")
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


def evaluate_cases(cases: list[dict], search, *, top_k: int, threshold: float) -> dict:
    """Run test cases and return the versioned deterministic result."""
    passed = 0
    failed_queries = []
    scores = []
    for idx, case in enumerate(cases, start=1):
        query = case["query"]
        expected_paths = case.get("expected_paths", [])
        min_results = int(case.get("min_results", 1))

        results = search(query, limit=max(top_k, 1))
        paths = [row.get("path", "") for row in results]
        hit = any(expected in paths for expected in expected_paths)
        enough = len(results) >= min_results
        ok = hit and enough
        passed += 1 if ok else 0
        top_score = results[0].get("score") if results else None
        scores.append({"query": query, "score": top_score, "passed": ok})
        if not ok:
            failed_queries.append(
                {
                    "query": query,
                    "expected_paths": expected_paths,
                    "returned_paths": paths[:5],
                    "score": top_score,
                }
            )

        print(
            f"[{idx}/{len(cases)}] {'PASS' if ok else 'FAIL'} "
            f"query={query!r} expected={expected_paths} top={paths[:5]}"
        )

    pass_rate = passed / max(len(cases), 1)
    print(f"\nSummary: {passed}/{len(cases)} passed ({pass_rate * 100:.1f}%)")
    return build_execution_result(
        total_tests=len(cases),
        passed_tests=passed,
        threshold=threshold,
        failed_queries=failed_queries,
        scores=scores,
    )


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

    result = evaluate_cases(
        cases,
        build_search_runner(),
        top_k=args.top_k,
        threshold=args.min_pass_rate,
    )
    if args.output_json:
        write_result(args.output_json, result)

    if result["decision"] == "fail":
        print(
            f"Gate failed: pass_rate={result['pass_rate']:.3f} < min_pass_rate={args.min_pass_rate:.3f}",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
