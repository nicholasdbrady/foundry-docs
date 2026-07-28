"""Focused tests for machine-readable search testbench output."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from run_testbench import evaluate_cases  # noqa: E402


def test_evaluate_cases_preserves_failed_query_evidence() -> None:
    cases = [
        {"query": "passing query", "expected_paths": ["expected/pass"]},
        {"query": "failing query", "expected_paths": ["expected/fail"]},
    ]

    def search(query: str, limit: int) -> list[dict]:
        assert limit == 10
        if query == "passing query":
            return [{"path": "expected/pass", "score": 0.9}]
        return [{"path": "actual/fail", "score": 0.2}]

    result = evaluate_cases(cases, search, top_k=10, threshold=0.85)

    assert result["total_tests"] == 2
    assert result["passed_tests"] == 1
    assert result["pass_rate"] == 0.5
    assert result["status"] == "failed"
    assert result["failed_queries"] == [
        {
            "query": "failing query",
            "expected_paths": ["expected/fail"],
            "returned_paths": ["actual/fail"],
            "score": 0.2,
        }
    ]
    assert result["scores"] == [
        {"query": "passing query", "score": 0.9, "passed": True},
        {"query": "failing query", "score": 0.2, "passed": False},
    ]
