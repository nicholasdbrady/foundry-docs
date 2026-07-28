#!/usr/bin/env python3
"""Build and validate deterministic post-index regression results."""

from __future__ import annotations

import argparse
import base64
import binascii
import html
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
REPORT_SCHEMA_VERSION = "1.0"
DEFAULT_THRESHOLD = 0.85
INCIDENT_KEY = "post-index-search-quality:v1"
INCIDENT_TITLE = "[search-quality] Search Quality Regression Detected"
INCIDENT_MARKER = f"<!-- post-index-incident-key: {INCIDENT_KEY} -->"
INCIDENT_STATE_PREFIX = "<!-- post-index-incident-state: "
MAX_INCIDENT_HISTORY = 25
EXECUTED_STATUSES = frozenset({"passed", "failed"})
VALID_STATUSES = EXECUTED_STATUSES | {"blocked", "error"}
VALID_DECISIONS = frozenset({"pass", "fail", "skip"})
_INCIDENT_STATE_PATTERN = re.compile(
    rf"{re.escape(INCIDENT_STATE_PREFIX)}(?P<payload>[A-Za-z0-9_-]+) -->"
)
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


def should_invoke_agent(result: dict[str, Any]) -> bool:
    """Return whether optional summarization can run without changing a passing workflow."""
    errors = validation_errors(result)
    if errors:
        raise ValueError("; ".join(errors))
    return result["status"] == "failed"


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


def build_incident_selection(issues: object) -> dict[str, Any]:
    """Select one canonical open incident and identify duplicate candidates."""
    if not isinstance(issues, list):
        raise ValueError("incident candidates must be a JSON list")

    candidates: list[dict[str, Any]] = []
    for index, issue in enumerate(issues):
        if not isinstance(issue, dict):
            raise ValueError(f"incident candidate {index} must be an object")
        number = issue.get("number")
        title = issue.get("title")
        body = issue.get("body")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValueError(f"incident candidate {index}.number must be a positive integer")
        if not isinstance(title, str):
            raise ValueError(f"incident candidate {index}.title must be a string")
        if body is not None and not isinstance(body, str):
            raise ValueError(f"incident candidate {index}.body must be a string or null")
        candidates.append({"number": number, "title": title, "body": body or ""})

    keyed = sorted(
        (issue for issue in candidates if INCIDENT_MARKER in issue["body"]),
        key=lambda issue: issue["number"],
    )
    legacy = sorted(
        (
            issue
            for issue in candidates
            if issue["title"] == INCIDENT_TITLE and INCIDENT_MARKER not in issue["body"]
        ),
        key=lambda issue: issue["number"],
    )
    ordered = keyed + legacy
    if not ordered:
        return {
            "dedup_key": INCIDENT_KEY,
            "canonical_number": None,
            "duplicate_numbers": [],
        }

    return {
        "dedup_key": INCIDENT_KEY,
        "canonical_number": ordered[0]["number"],
        "duplicate_numbers": [issue["number"] for issue in ordered[1:]],
    }


def _incident_state_marker(state: dict[str, Any]) -> str:
    payload = json.dumps(state, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"{INCIDENT_STATE_PREFIX}{encoded} -->"


def _load_incident_state(existing_body: str) -> dict[str, Any] | None:
    match = _INCIDENT_STATE_PATTERN.search(existing_body)
    if match is None:
        return None

    encoded = match.group("payload")
    encoded += "=" * (-len(encoded) % 4)
    try:
        state = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
    except (binascii.Error, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(state, dict):
        return None
    if not isinstance(state.get("history"), list):
        return None
    current = state.get("current")
    if current is not None and not isinstance(current, dict):
        return None
    return state


def _occurrence_summary(
    result: dict[str, Any],
    *,
    repository: str,
    run_id: str,
    artifact_name: str,
    artifact_url: str,
    server_url: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "run_url": f"{server_url.rstrip('/')}/{repository}/actions/runs/{run_id}",
        "artifact_name": artifact_name,
        "artifact_url": artifact_url,
        "pass_rate": result["pass_rate"],
        "threshold": result["threshold"],
        "passed_tests": result["passed_tests"],
        "total_tests": result["total_tests"],
        "failed_query_count": len(result["failed_queries"]),
    }


def _updated_incident_state(
    existing_body: str,
    current: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    previous = _load_incident_state(existing_body)
    legacy_adopted = bool(existing_body.strip()) and previous is None
    history: list[dict[str, Any]] = []
    if previous is not None:
        previous_current = previous.get("current")
        if isinstance(previous_current, dict):
            history.append(previous_current)
        history.extend(item for item in previous["history"] if isinstance(item, dict))
        legacy_adopted = bool(previous.get("legacy_adopted"))

    current_run_id = current["run_id"]
    history = [item for item in history if item.get("run_id") != current_run_id]
    history = history[:MAX_INCIDENT_HISTORY]
    return {
        "current": current,
        "history": history,
        "legacy_adopted": legacy_adopted,
    }, legacy_adopted


def _render_history(history: list[dict[str, Any]], legacy_adopted: bool) -> list[str]:
    lines = ["### Occurrence History", ""]
    if not history and not legacy_adopted:
        lines.append("No earlier keyed failures have been recorded.")
        return lines

    if legacy_adopted:
        lines.extend(
            [
                "> [!NOTE]",
                "> This incident adopted an earlier unkeyed report. Its run metadata was not available for the history table.",
                "",
            ]
        )
    if not history:
        return lines

    lines.extend(
        [
            "| Run | Pass rate | Passed | Failed queries | Evidence |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for occurrence in history:
        run_id = html.escape(str(occurrence.get("run_id", "unknown")))
        run_url = html.escape(str(occurrence.get("run_url", "")), quote=True)
        artifact_name = html.escape(str(occurrence.get("artifact_name", "artifact")))
        artifact_url = html.escape(str(occurrence.get("artifact_url", "")), quote=True)
        pass_rate = occurrence.get("pass_rate")
        pass_rate_text = f"{pass_rate * 100:.1f}%" if _is_number(pass_rate) else "unknown"
        passed = occurrence.get("passed_tests", "unknown")
        total = occurrence.get("total_tests", "unknown")
        failed = occurrence.get("failed_query_count", "unknown")
        lines.append(
            f"| [§{run_id}]({run_url}) | {pass_rate_text} | {passed}/{total} | {failed} | "
            f"[{artifact_name}]({artifact_url}) |"
        )
    return lines


def _render_result_summary(
    result: dict[str, Any],
    current: dict[str, Any],
    *,
    include_failed_queries: bool,
    history: list[dict[str, Any]] | None = None,
    legacy_adopted: bool = False,
) -> str:
    status = result["status"]
    alert = "WARNING" if result["decision"] == "fail" else "NOTE"
    lines = [
        "### Validated Post-Index Result",
        "",
        f"> [!{alert}]",
        f"> Machine status: **{status}**; decision: **{result['decision']}**.",
        "",
        f"**Run**: [§{current['run_id']}]({current['run_url']})",
        f"**Artifact**: [{current['artifact_name']}]({current['artifact_url']})",
        f"**Threshold**: {result['threshold'] * 100:.1f}%",
        f"**Actual pass rate**: {result['pass_rate'] * 100:.1f}%",
        f"**Totals**: {result['passed_tests']}/{result['total_tests']} passed",
        f"**Failed queries**: {len(result['failed_queries'])}",
        "",
        "### Diagnostics",
        "",
    ]
    if result["diagnostics"]:
        lines.extend(f"- {diagnostic}" for diagnostic in result["diagnostics"])
    else:
        lines.append("No diagnostics were emitted.")

    if include_failed_queries:
        evidence = html.escape(json.dumps(result["failed_queries"], indent=2, sort_keys=True))
        lines.extend(
            [
                "",
                "### Failed-Query Evidence",
                "",
                "<details>",
                f"<summary>View all {len(result['failed_queries'])} failed queries</summary>",
                "",
                f"<pre>{evidence}</pre>",
                "",
                "</details>",
            ]
        )
    if history is not None:
        lines.extend(["", *_render_history(history, legacy_adopted)])
    return "\n".join(lines)


def build_report_output(
    result: dict[str, Any],
    *,
    repository: str,
    run_id: str,
    artifact_name: str,
    artifact_url: str,
    server_url: str = "https://github.com",
    existing_body: str = "",
) -> dict[str, Any]:
    """Build an incident upsert or concrete no-action record from a validated result."""
    errors = validation_errors(result)
    if errors:
        raise ValueError("; ".join(errors))
    for field, value in (
        ("repository", repository),
        ("run_id", run_id),
        ("artifact_name", artifact_name),
        ("artifact_url", artifact_url),
        ("server_url", server_url),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")

    current = _occurrence_summary(
        result,
        repository=repository,
        run_id=run_id,
        artifact_name=artifact_name,
        artifact_url=artifact_url,
        server_url=server_url,
    )
    if result["status"] != "failed":
        summary = _render_result_summary(result, current, include_failed_queries=False)
        summary += "\n\n> [!NOTE]\n> No incident was created or updated for this result."
        return {
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "dedup_key": INCIDENT_KEY,
            "action": "noop",
            "status": result["status"],
            "decision": result["decision"],
            "summary": summary,
            "incident": None,
        }

    state, legacy_adopted = _updated_incident_state(existing_body, current)
    summary = _render_result_summary(
        result,
        current,
        include_failed_queries=True,
        history=state["history"],
        legacy_adopted=legacy_adopted,
    )
    body = "\n".join(
        [
            INCIDENT_MARKER,
            _incident_state_marker(state),
            "",
            summary,
            "",
            "### Recommended Actions",
            "",
            "- Review the index sync for data issues.",
            "- Check whether new or modified documents have correct metadata.",
            "- Consider running a full index rebuild.",
            "",
            "> [!NOTE]",
            "> The pass/fail conclusion and evidence above are machine-owned. Agent summaries cannot change them.",
        ]
    )
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "dedup_key": INCIDENT_KEY,
        "action": "upsert_incident",
        "status": result["status"],
        "decision": result["decision"],
        "summary": summary,
        "incident": {
            "title": INCIDENT_TITLE,
            "body": body,
        },
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def write_report_output(
    path: Path,
    report: dict[str, Any],
    *,
    summary_path: Path,
    incident_title_path: Path | None = None,
    incident_body_path: Path | None = None,
) -> None:
    """Write the validated report contract and materialized Markdown outputs."""
    _write_text(path, json.dumps(report, indent=2, sort_keys=True) + "\n")
    _write_text(summary_path, str(report["summary"]).rstrip() + "\n")
    incident = report["incident"]
    if incident is None:
        return
    if incident_title_path is None or incident_body_path is None:
        raise ValueError("incident output paths are required for a failed result")
    _write_text(incident_title_path, str(incident["title"]))
    _write_text(incident_body_path, str(incident["body"]).rstrip() + "\n")


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

    select = subparsers.add_parser("select-incident")
    select.add_argument("--input", type=Path, required=True)
    select.add_argument("--output", type=Path, required=True)

    report = subparsers.add_parser("render-report")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--repository", required=True)
    report.add_argument("--run-id", required=True)
    report.add_argument("--artifact-name", required=True)
    report.add_argument("--artifact-url", required=True)
    report.add_argument("--server-url", default="https://github.com")
    report.add_argument("--existing-body", type=Path)
    report.add_argument("--output", type=Path, required=True)
    report.add_argument("--summary-output", type=Path, required=True)
    report.add_argument("--incident-title-output", type=Path)
    report.add_argument("--incident-body-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "write-blocked":
        write_result(args.output, build_blocked_result(args.parent_conclusion, threshold=args.threshold))
        return 0
    if args.command == "write-error":
        write_result(args.output, build_error_result(args.stage, args.message, threshold=args.threshold))
        return 0
    if args.command == "select-incident":
        try:
            issues = json.loads(args.input.read_text(encoding="utf-8"))
            selection = build_incident_selection(issues)
            _write_text(args.output, json.dumps(selection, indent=2, sort_keys=True) + "\n")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Cannot select post-index incident: {exc}", file=sys.stderr)
            return 2
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
            output.write(f"invoke_agent={'true' if should_invoke_agent(result) else 'false'}\n")
        return 0
    if args.command == "render-decision-output":
        try:
            write_decision_output(args.output, result)
        except ValueError as exc:
            print(f"Cannot render post-index decision output: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "render-report":
        try:
            existing_body = args.existing_body.read_text(encoding="utf-8") if args.existing_body else ""
            report = build_report_output(
                result,
                repository=args.repository,
                run_id=args.run_id,
                artifact_name=args.artifact_name,
                artifact_url=args.artifact_url,
                server_url=args.server_url,
                existing_body=existing_body,
            )
            write_report_output(
                args.output,
                report,
                summary_path=args.summary_output,
                incident_title_path=args.incident_title_output,
                incident_body_path=args.incident_body_output,
            )
        except (OSError, ValueError) as exc:
            print(f"Cannot render post-index report: {exc}", file=sys.stderr)
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
