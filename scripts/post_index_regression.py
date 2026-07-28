#!/usr/bin/env python3
"""Build and validate deterministic post-index regression results."""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
DEFAULT_THRESHOLD = 0.85
EXECUTED_STATUSES = frozenset({"passed", "failed"})
VALID_STATUSES = EXECUTED_STATUSES | {"blocked", "error"}
VALID_DECISIONS = frozenset({"pass", "fail", "skip"})
REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "decision",
        "total_tests",
        "passed_tests",
        "pass_rate",
        "threshold",
        "failed_queries",
        "scores",
        "diagnostics",
    }
)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def build_execution_result(
    *,
    total_tests: int,
    passed_tests: int,
    threshold: float,
    failed_queries: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    diagnostics: list[str] | None = None,
) -> dict[str, Any]:
    """Build the result produced by a completed testbench run."""
    pass_rate = passed_tests / total_tests if total_tests else 0.0
    passed = pass_rate >= threshold
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if passed else "failed",
        "decision": "pass" if passed else "fail",
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "pass_rate": pass_rate,
        "threshold": threshold,
        "failed_queries": failed_queries,
        "scores": scores,
        "diagnostics": list(diagnostics or []),
    }


def build_blocked_result(parent_conclusion: str, *, threshold: float = DEFAULT_THRESHOLD) -> dict[str, Any]:
    """Build the explicit result used when the parent workflow did not succeed."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "blocked",
        "decision": "skip",
        "total_tests": 0,
        "passed_tests": 0,
        "pass_rate": 0.0,
        "threshold": threshold,
        "failed_queries": [],
        "scores": [],
        "diagnostics": [f"Parent index workflow conclusion was {parent_conclusion!r}; regression execution was skipped."],
    }


def build_error_result(stage: str, message: str, *, threshold: float = DEFAULT_THRESHOLD) -> dict[str, Any]:
    """Build the explicit result used when deterministic setup or execution fails."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "error",
        "decision": "fail",
        "total_tests": 0,
        "passed_tests": 0,
        "pass_rate": 0.0,
        "threshold": threshold,
        "failed_queries": [],
        "scores": [],
        "diagnostics": [f"{stage} failure: {message}"],
    }


def validation_errors(result: object) -> list[str]:
    """Return all schema and consistency errors for a result."""
    if not isinstance(result, dict):
        return ["result must be a JSON object"]

    errors: list[str] = []
    missing = sorted(REQUIRED_KEYS - result.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return errors

    if result["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    status = result["status"]
    decision = result["decision"]
    if status not in VALID_STATUSES:
        errors.append(f"status must be one of {sorted(VALID_STATUSES)}")
    if decision not in VALID_DECISIONS:
        errors.append(f"decision must be one of {sorted(VALID_DECISIONS)}")

    total = result["total_tests"]
    passed = result["passed_tests"]
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        errors.append("total_tests must be a non-negative integer")
    if not isinstance(passed, int) or isinstance(passed, bool) or passed < 0:
        errors.append("passed_tests must be a non-negative integer")
    if (
        isinstance(total, int)
        and not isinstance(total, bool)
        and isinstance(passed, int)
        and not isinstance(passed, bool)
        and passed > total
    ):
        errors.append("passed_tests cannot exceed total_tests")

    pass_rate = result["pass_rate"]
    threshold = result["threshold"]
    if not _is_number(pass_rate) or not 0.0 <= pass_rate <= 1.0:
        errors.append("pass_rate must be a finite number between 0.0 and 1.0")
    if not _is_number(threshold) or not 0.0 <= threshold <= 1.0:
        errors.append("threshold must be a finite number between 0.0 and 1.0")

    failed_queries = result["failed_queries"]
    scores = result["scores"]
    diagnostics = result["diagnostics"]
    if not isinstance(failed_queries, list):
        errors.append("failed_queries must be a list")
    else:
        for index, item in enumerate(failed_queries):
            errors.extend(_validate_failed_query(item, index))
    if not isinstance(scores, list):
        errors.append("scores must be a list")
    else:
        for index, item in enumerate(scores):
            errors.extend(_validate_score(item, index))
    if not isinstance(diagnostics, list) or not all(isinstance(item, str) for item in diagnostics):
        errors.append("diagnostics must be a list of strings")

    numeric_counts = (
        isinstance(total, int)
        and not isinstance(total, bool)
        and isinstance(passed, int)
        and not isinstance(passed, bool)
        and 0 <= passed <= total
    )
    numeric_rates = _is_number(pass_rate) and _is_number(threshold)
    if numeric_counts and numeric_rates:
        expected_rate = passed / total if total else 0.0
        if not math.isclose(pass_rate, expected_rate, rel_tol=0.0, abs_tol=1e-12):
            errors.append("pass_rate must equal passed_tests / total_tests")

        if status in EXECUTED_STATUSES:
            if total == 0:
                errors.append("executed results must contain at least one test")
            if isinstance(scores, list):
                if len(scores) != total:
                    errors.append("scores must contain one entry per executed test")
                errors.extend(_score_consistency_errors(scores, failed_queries, total, passed, pass_rate))
            expected_status = "passed" if pass_rate >= threshold else "failed"
            expected_decision = "pass" if expected_status == "passed" else "fail"
            if status != expected_status:
                errors.append(f"status must be {expected_status!r} for the numerical result")
            if decision != expected_decision:
                errors.append(f"decision must be {expected_decision!r} for the numerical result")
        elif status == "blocked":
            if decision != "skip":
                errors.append("blocked results must use decision 'skip'")
            errors.extend(_nonexecuted_evidence_errors(result, "blocked"))
        elif status == "error":
            if decision != "fail":
                errors.append("error results must use decision 'fail'")
            if not diagnostics:
                errors.append("error results must include diagnostics")
            errors.extend(_nonexecuted_evidence_errors(result, "error"))

    return errors


def _validate_failed_query(item: object, index: int) -> list[str]:
    prefix = f"failed_queries[{index}]"
    if not isinstance(item, dict):
        return [f"{prefix} must be an object"]
    errors = []
    if not isinstance(item.get("query"), str) or not item["query"]:
        errors.append(f"{prefix}.query must be a non-empty string")
    for field in ("expected_paths", "returned_paths"):
        if not isinstance(item.get(field), list) or not all(isinstance(path, str) for path in item[field]):
            errors.append(f"{prefix}.{field} must be a list of strings")
    score = item.get("score")
    if score is not None and not _is_number(score):
        errors.append(f"{prefix}.score must be a finite number or null")
    return errors


def _validate_score(item: object, index: int) -> list[str]:
    prefix = f"scores[{index}]"
    if not isinstance(item, dict):
        return [f"{prefix} must be an object"]
    errors = []
    if not isinstance(item.get("query"), str) or not item["query"]:
        errors.append(f"{prefix}.query must be a non-empty string")
    score = item.get("score")
    if score is not None and not _is_number(score):
        errors.append(f"{prefix}.score must be a finite number or null")
    if not isinstance(item.get("passed"), bool):
        errors.append(f"{prefix}.passed must be a boolean")
    return errors


def _score_consistency_errors(
    scores: list[object],
    failed_queries: object,
    total: int,
    passed: int,
    pass_rate: float,
) -> list[str]:
    """Cross-check aggregate and failed-query evidence against score records."""
    if not all(isinstance(item, dict) for item in scores):
        return []

    score_queries = [item.get("query") for item in scores]
    if not all(isinstance(query, str) and query for query in score_queries):
        return []

    errors: list[str] = []
    if len(set(score_queries)) != len(score_queries):
        errors.append("scores must contain unique query identities")

    derived_passed = sum(item.get("passed") is True for item in scores)
    if derived_passed != passed:
        errors.append("passed_tests must equal the number of scores with passed=true")
    derived_rate = derived_passed / total if total else 0.0
    if not math.isclose(pass_rate, derived_rate, rel_tol=0.0, abs_tol=1e-12):
        errors.append("pass_rate must equal the pass rate derived from scores")

    failed_scores = {item["query"]: item.get("score") for item in scores if item.get("passed") is False}
    if len(failed_scores) != total - derived_passed:
        errors.append("failed score count must equal total_tests minus passed_tests")

    if not isinstance(failed_queries, list) or not all(isinstance(item, dict) for item in failed_queries):
        return errors
    failed_query_names = [item.get("query") for item in failed_queries]
    if not all(isinstance(query, str) and query for query in failed_query_names):
        return errors
    if len(set(failed_query_names)) != len(failed_query_names):
        errors.append("failed_queries must contain unique query identities")
    if set(failed_query_names) != set(failed_scores):
        errors.append("failed_queries must exactly match queries whose scores have passed=false")
        return errors

    for item in failed_queries:
        query = item["query"]
        if item.get("score") != failed_scores[query]:
            errors.append(f"failed_queries score must match scores entry for query {query!r}")
    return errors


def _nonexecuted_evidence_errors(result: dict[str, Any], status: str) -> list[str]:
    errors = []
    if result["total_tests"] != 0 or result["passed_tests"] != 0 or result["pass_rate"] != 0.0:
        errors.append(f"{status} results cannot report executed test aggregates")
    if result["scores"]:
        errors.append(f"{status} results cannot contain scores")
    if result["failed_queries"]:
        errors.append(f"{status} results cannot contain failed_queries")
    return errors


def write_result(path: Path, result: dict[str, Any]) -> None:
    """Validate and atomically write a result."""
    errors = validation_errors(result)
    if errors:
        raise ValueError("; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_result(path: Path) -> dict[str, Any]:
    """Load a JSON result without accepting a non-object root."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("result must be a JSON object")
    return data


def phase_exit_code(result: dict[str, Any], phase: str) -> int:
    """Return the machine-owned exit code for a validation phase."""
    errors = validation_errors(result)
    if errors:
        return 2
    if phase == "schema":
        return 0
    if phase == "prepare":
        return 1 if result["status"] == "error" else 0
    if phase == "final":
        return 0 if result["decision"] in {"pass", "skip"} else 1
    raise ValueError(f"Unknown validation phase: {phase}")


def build_safe_output(result: dict[str, Any]) -> dict[str, Any]:
    """Build the only safe output permitted by the machine decision."""
    errors = validation_errors(result)
    if errors:
        raise ValueError("; ".join(errors))

    if result["status"] == "passed":
        message = (
            f"Search quality check passed. {result['passed_tests']}/{result['total_tests']} tests passed "
            f"({result['pass_rate'] * 100:.1f}%). Index update is clean."
        )
        return {"items": [{"type": "noop", "message": message}]}

    if result["status"] == "failed":
        evidence = html.escape(json.dumps(result["failed_queries"], indent=2, sort_keys=True))
        body = "\n".join(
            [
                "### Search Quality Regression Detected",
                "",
                "**Trigger**: Post-index-sync check",
                (
                    f"**Pass rate**: {result['pass_rate'] * 100:.1f}% "
                    f"(machine threshold: {result['threshold'] * 100:.1f}%)"
                ),
                f"**Passed tests**: {result['passed_tests']}/{result['total_tests']}",
                "",
                "### Failed Queries",
                "",
                f"<pre>{evidence}</pre>",
                "",
                "### Recommended Actions",
                "",
                "- Review the index sync for data issues.",
                "- Check whether new or modified documents have correct metadata.",
                "- Consider running a full index rebuild.",
            ]
        )
        return {
            "items": [
                {
                    "type": "create_issue",
                    "title": "Search Quality Regression Detected",
                    "body": body,
                }
            ]
        }

    if result["status"] in {"blocked", "error"}:
        message = " ".join(result["diagnostics"]) or f"Post-index regression status: {result['status']}."
        return {"items": [{"type": "noop", "message": message}]}

    raise ValueError(f"Cannot render a decision output for status {result['status']!r}")


def write_decision_output(path: Path, result: dict[str, Any]) -> None:
    """Write the deterministic issue/noop rendering for host-side processing."""
    safe_output = build_safe_output(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(safe_output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    blocked = subparsers.add_parser("write-blocked")
    blocked.add_argument("--parent-conclusion", required=True)
    blocked.add_argument("--output", type=Path, required=True)
    blocked.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)

    error = subparsers.add_parser("write-error")
    error.add_argument("--stage", required=True)
    error.add_argument("--message", required=True)
    error.add_argument("--output", type=Path, required=True)
    error.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--input", type=Path, required=True)
    validate.add_argument("--phase", choices=("schema", "prepare", "final"), required=True)

    classify = subparsers.add_parser("classify")
    classify.add_argument("--input", type=Path, required=True)
    classify.add_argument("--github-output", type=Path, required=True)

    render = subparsers.add_parser("render-decision-output")
    render.add_argument("--input", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "write-blocked":
        write_result(args.output, build_blocked_result(args.parent_conclusion, threshold=args.threshold))
        return 0
    if args.command == "write-error":
        write_result(args.output, build_error_result(args.stage, args.message, threshold=args.threshold))
        return 0

    try:
        result = load_result(args.input)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid post-index result: {exc}", file=sys.stderr)
        return 2

    errors = validation_errors(result)
    if errors:
        for error in errors:
            print(f"Invalid post-index result: {error}", file=sys.stderr)
        return 2

    if args.command == "classify":
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"status={result['status']}\n")
            output.write(f"decision={result['decision']}\n")
            output.write(f"invoke_agent={'true' if result['status'] in EXECUTED_STATUSES else 'false'}\n")
        return 0
    if args.command == "render-decision-output":
        try:
            write_decision_output(args.output, result)
        except ValueError as exc:
            print(f"Cannot render post-index decision output: {exc}", file=sys.stderr)
            return 2
        return 0

    exit_code = phase_exit_code(result, args.phase)
    print(
        f"Post-index result: status={result['status']} decision={result['decision']} "
        f"pass_rate={result['pass_rate']:.3f} threshold={result['threshold']:.3f}"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
