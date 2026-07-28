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
            if isinstance(scores, list) and len(scores) != total:
                errors.append("scores must contain one entry per executed test")
            if isinstance(failed_queries, list) and len(failed_queries) != total - passed:
                errors.append("failed_queries must contain one entry per failed test")
            expected_status = "passed" if pass_rate >= threshold else "failed"
            expected_decision = "pass" if expected_status == "passed" else "fail"
            if status != expected_status:
                errors.append(f"status must be {expected_status!r} for the numerical result")
            if decision != expected_decision:
                errors.append(f"decision must be {expected_decision!r} for the numerical result")
        elif status == "blocked":
            if decision != "skip":
                errors.append("blocked results must use decision 'skip'")
            if total != 0 or passed != 0:
                errors.append("blocked results cannot report executed tests")
        elif status == "error":
            if decision != "fail":
                errors.append("error results must use decision 'fail'")
            if not diagnostics:
                errors.append("error results must include diagnostics")

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
        return 1 if result["status"] in {"blocked", "error"} else 0
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

    raise ValueError(f"Cannot render a safe output for status {result['status']!r}")


def write_safe_outputs_jsonl(path: Path, result: dict[str, Any]) -> None:
    """Append deterministic safe outputs and a noop engine short-circuit."""
    safe_output = build_safe_output(result)
    items = list(safe_output["items"])
    if not any(item["type"] == "noop" for item in items):
        items.append(
            {
                "type": "noop",
                "message": "Machine-owned regression decision prepared; no model invocation is required.",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        for item in items:
            output.write(json.dumps(item, sort_keys=True) + "\n")


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

    render_jsonl = subparsers.add_parser("render-safe-outputs-jsonl")
    render_jsonl.add_argument("--input", type=Path, required=True)
    render_jsonl.add_argument("--output", type=Path, required=True)
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
    if args.command == "render-safe-outputs-jsonl":
        try:
            write_safe_outputs_jsonl(args.output, result)
        except ValueError as exc:
            print(f"Cannot render post-index safe outputs: {exc}", file=sys.stderr)
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
