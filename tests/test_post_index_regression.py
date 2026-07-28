"""Tests for deterministic post-index regression results and gating."""

from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from post_index_regression import (  # noqa: E402
    build_blocked_result,
    build_error_result,
    build_execution_result,
    build_safe_output,
    phase_exit_code,
    validation_errors,
    write_decision_output,
)


def _scores(total: int, passed: int) -> list[dict]:
    return [
        {"query": f"query-{index}", "score": 1.0 - index / 100, "passed": index < passed}
        for index in range(total)
    ]


def _failed_queries(total: int, passed: int) -> list[dict]:
    return [
        {
            "query": f"query-{index}",
            "expected_paths": [f"expected/{index}"],
            "returned_paths": [f"actual/{index}"],
            "score": 1.0 - index / 100,
        }
        for index in range(passed, total)
    ]


def _result(total: int, passed: int, threshold: float = 0.85) -> dict:
    return build_execution_result(
        total_tests=total,
        passed_tests=passed,
        threshold=threshold,
        failed_queries=_failed_queries(total, passed),
        scores=_scores(total, passed),
    )


def test_failed_or_cancelled_parent_is_blocked_before_agent() -> None:
    for conclusion in ("failure", "cancelled"):
        result = build_blocked_result(conclusion)

        assert result["status"] == "blocked"
        assert result["decision"] == "skip"
        assert conclusion in result["diagnostics"][0]
        assert phase_exit_code(result, "prepare") == 0
        assert validation_errors(result) == []


def test_setup_failure_is_machine_failure() -> None:
    result = build_error_result("setup", "dependency installation failed")

    assert result["status"] == "error"
    assert result["decision"] == "fail"
    assert phase_exit_code(result, "prepare") == 1
    assert phase_exit_code(result, "final") == 1
    assert validation_errors(result) == []
    assert build_safe_output(result)["items"][0]["type"] == "noop"


def test_schema_invalid_output_fails_validation() -> None:
    result = _result(1, 1)
    del result["scores"]

    assert "missing required fields: scores" in validation_errors(result)
    assert phase_exit_code(result, "schema") == 2


def test_threshold_boundary_is_inclusive() -> None:
    below = _result(1000, 849)
    at_threshold = _result(100, 85)

    assert below["status"] == "failed"
    assert phase_exit_code(below, "final") == 1
    assert at_threshold["status"] == "passed"
    assert phase_exit_code(at_threshold, "final") == 0


def test_failed_queries_and_scores_are_preserved() -> None:
    result = _result(3, 2)

    assert result["failed_queries"] == [
        {
            "query": "query-2",
            "expected_paths": ["expected/2"],
            "returned_paths": ["actual/2"],
            "score": 0.98,
        }
    ]
    assert result["scores"] == _scores(3, 2)
    assert validation_errors(result) == []


def test_passing_result_cannot_be_reinterpreted() -> None:
    result = _result(20, 17)
    tampered = copy.deepcopy(result)
    tampered["decision"] = "fail"

    assert result["pass_rate"] == 0.85
    assert phase_exit_code(result, "final") == 0
    assert "decision must be 'pass' for the numerical result" in validation_errors(tampered)


def test_safe_output_is_derived_only_from_machine_decision() -> None:
    passed = build_safe_output(_result(20, 17))
    failed = build_safe_output(_result(20, 16))

    assert passed == {
        "items": [
            {
                "type": "noop",
                "message": "Search quality check passed. 17/20 tests passed (85.0%). Index update is clean.",
            }
        ]
    }
    assert failed["items"][0]["type"] == "create_issue"
    assert failed["items"][0]["title"] == "Search Quality Regression Detected"
    assert "query-16" in failed["items"][0]["body"]
    assert "80.0% (machine threshold: 85.0%)" in failed["items"][0]["body"]


def test_decision_output_preserves_deterministic_issue_rendering(tmp_path) -> None:
    output = tmp_path / "decision-output.json"
    write_decision_output(output, _result(20, 16))
    items = json.loads(output.read_text(encoding="utf-8"))["items"]

    assert [item["type"] for item in items] == ["create_issue"]
    assert items[0]["title"] == "Search Quality Regression Detected"


def test_passed_count_must_match_score_evidence() -> None:
    result = _result(20, 17)
    for item in result["scores"]:
        item["passed"] = False

    errors = validation_errors(result)

    assert "passed_tests must equal the number of scores with passed=true" in errors
    assert "pass_rate must equal the pass rate derived from scores" in errors
    assert phase_exit_code(result, "final") == 2


def test_failed_queries_must_match_failed_score_identities() -> None:
    result = _result(3, 2)
    result["failed_queries"][0]["query"] = "different-query"

    errors = validation_errors(result)
    assert "failed_queries must exactly match queries whose scores have passed=false" in errors
    assert phase_exit_code(result, "final") == 2


def test_failed_query_score_must_match_score_evidence() -> None:
    result = _result(3, 2)
    result["failed_queries"][0]["score"] = 0.9

    errors = validation_errors(result)
    assert "failed_queries score must match scores entry for query 'query-2'" in errors
    assert phase_exit_code(result, "final") == 2


def test_blocked_and_error_results_reject_execution_evidence() -> None:
    for result in (build_blocked_result("cancelled"), build_error_result("setup", "failed")):
        status = result["status"]
        result["scores"] = [{"query": "contradiction", "score": 0.1, "passed": False}]
        result["failed_queries"] = [
            {
                "query": "contradiction",
                "expected_paths": ["expected"],
                "returned_paths": ["actual"],
                "score": 0.1,
            }
        ]

        errors = validation_errors(result)

        assert f"{status} results cannot contain scores" in errors
        assert f"{status} results cannot contain failed_queries" in errors
        assert phase_exit_code(result, "final") == 2
