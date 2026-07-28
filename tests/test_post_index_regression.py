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
    write_safe_outputs_jsonl,
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
            "score": 0.1,
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
        assert phase_exit_code(result, "prepare") == 1
        assert validation_errors(result) == []


def test_setup_failure_is_machine_failure() -> None:
    result = build_error_result("setup", "dependency installation failed")

    assert result["status"] == "error"
    assert result["decision"] == "fail"
    assert phase_exit_code(result, "prepare") == 1
    assert phase_exit_code(result, "final") == 1
    assert validation_errors(result) == []


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
            "score": 0.1,
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


def test_jsonl_safe_outputs_always_short_circuit_model_invocation(tmp_path) -> None:
    output = tmp_path / "safe-outputs.jsonl"
    write_safe_outputs_jsonl(output, _result(20, 16))
    items = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert [item["type"] for item in items] == ["create_issue", "noop"]
    assert items[0]["title"] == "Search Quality Regression Detected"
