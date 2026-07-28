"""Create and enforce machine-readable identities for generated report issues."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

MARKER_PREFIX = "<!-- generated-report:"
MARKER_PATTERN = re.compile(r"^\s*<!-- generated-report:\s*(\{[^\r\n]*\})\s*-->\s*$")
IDENTITY_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
REQUIRED_MARKER_KEYS = {"workflow_identity", "report_kind", "report_date"}


class CleanupError(RuntimeError):
    """Raised when generated-report cleanup cannot complete safely."""


@dataclass(frozen=True, slots=True)
class GeneratedReportMarker:
    workflow_identity: str
    report_kind: str
    report_date: str


@dataclass(frozen=True, slots=True)
class MarkerInspection:
    status: str
    marker: GeneratedReportMarker | None
    reason: str


@dataclass(frozen=True, slots=True)
class CleanupDecision:
    issue_number: int
    outcome: str
    reason: str


@dataclass(frozen=True, slots=True)
class CleanupResult:
    selected: int
    closed: int
    skipped: int
    invalid_markers: int
    decisions: tuple[CleanupDecision, ...]

    def counts(self) -> dict[str, int]:
        return {
            "selected": self.selected,
            "closed": self.closed,
            "skipped": self.skipped,
            "invalid_markers": self.invalid_markers,
        }


GhRunner = Callable[[list[str]], str]
IssueCloser = Callable[[int], None]


def _validate_identity(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not IDENTITY_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase machine identity")
    return value


def _validate_report_date(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("report_date must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("report_date must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise ValueError("report_date must be an ISO date")
    return value


def build_marker(workflow_identity: str, report_kind: str, report_date: str) -> str:
    """Build the canonical generated-report marker."""
    payload = {
        "workflow_identity": _validate_identity(workflow_identity, "workflow_identity"),
        "report_kind": _validate_identity(report_kind, "report_kind"),
        "report_date": _validate_report_date(report_date),
    }
    return f"{MARKER_PREFIX} {json.dumps(payload, separators=(',', ':'), sort_keys=True)} -->"


def inspect_marker(body: str) -> MarkerInspection:
    """Inspect a report body without treating a broad issue label as identity."""
    marker_lines = [line for line in body.splitlines() if MARKER_PREFIX in line]
    if not marker_lines:
        return MarkerInspection(status="missing", marker=None, reason="generated-report marker is missing")
    if len(marker_lines) != 1:
        return MarkerInspection(status="invalid", marker=None, reason="expected exactly one generated-report marker")

    match = MARKER_PATTERN.fullmatch(marker_lines[0])
    if match is None:
        return MarkerInspection(status="invalid", marker=None, reason="generated-report marker is malformed")

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return MarkerInspection(status="invalid", marker=None, reason="generated-report marker contains invalid JSON")

    if not isinstance(payload, dict) or set(payload) != REQUIRED_MARKER_KEYS:
        return MarkerInspection(
            status="invalid",
            marker=None,
            reason="generated-report marker must contain only workflow_identity, report_kind, and report_date",
        )

    try:
        marker = GeneratedReportMarker(
            workflow_identity=_validate_identity(payload["workflow_identity"], "workflow_identity"),
            report_kind=_validate_identity(payload["report_kind"], "report_kind"),
            report_date=_validate_report_date(payload["report_date"]),
        )
    except ValueError as exc:
        return MarkerInspection(status="invalid", marker=None, reason=str(exc))
    return MarkerInspection(status="valid", marker=marker, reason="generated-report marker is valid")


def cleanup_generated_reports(
    issues: Iterable[dict[str, Any]],
    *,
    workflow_identity: str,
    report_kind: str,
    close_issue: IssueCloser,
) -> CleanupResult:
    """Close only issues with a valid marker matching the expected report identity."""
    expected_workflow = _validate_identity(workflow_identity, "workflow_identity")
    expected_kind = _validate_identity(report_kind, "report_kind")
    selected = closed = skipped = invalid_markers = 0
    decisions: list[CleanupDecision] = []

    for issue in issues:
        issue_number = issue.get("number")
        body = issue.get("body")
        if not isinstance(issue_number, int):
            raise CleanupError("GitHub returned an issue without an integer number")
        if body is None:
            body = ""
        if not isinstance(body, str):
            skipped += 1
            invalid_markers += 1
            decisions.append(CleanupDecision(issue_number, "invalid-marker", "issue body is not text"))
            continue

        inspection = inspect_marker(body)
        if inspection.status == "missing":
            skipped += 1
            decisions.append(CleanupDecision(issue_number, "skipped", inspection.reason))
            continue
        if inspection.status == "invalid":
            skipped += 1
            invalid_markers += 1
            decisions.append(CleanupDecision(issue_number, "invalid-marker", inspection.reason))
            continue

        marker = inspection.marker
        if marker is None:
            raise CleanupError("valid marker inspection did not return marker data")
        if marker.workflow_identity != expected_workflow or marker.report_kind != expected_kind:
            skipped += 1
            decisions.append(
                CleanupDecision(
                    issue_number,
                    "skipped",
                    "generated-report marker does not match the expected workflow identity and report kind",
                )
            )
            continue

        selected += 1
        try:
            close_issue(issue_number)
        except CleanupError as exc:
            skipped += 1
            decisions.append(CleanupDecision(issue_number, "close-failed", str(exc)))
            continue
        closed += 1
        decisions.append(CleanupDecision(issue_number, "closed", "matching generated report was superseded"))

    return CleanupResult(
        selected=selected,
        closed=closed,
        skipped=skipped,
        invalid_markers=invalid_markers,
        decisions=tuple(decisions),
    )


def run_gh(args: list[str]) -> str:
    """Run a bounded GitHub CLI command and return stdout."""
    try:
        completed = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise CleanupError(f"GitHub CLI command failed: {' '.join(args[:3])}") from exc
    return completed.stdout


def _load_open_issues(repo: str, label: str, runner: GhRunner) -> list[dict[str, Any]]:
    raw = runner(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--label",
            label,
            "--state",
            "open",
            "--limit",
            "1000",
            "--json",
            "number,body",
        ]
    )
    try:
        issues = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CleanupError("GitHub CLI returned invalid issue JSON") from exc
    if not isinstance(issues, list) or not all(isinstance(issue, dict) for issue in issues):
        raise CleanupError("GitHub CLI returned an unexpected issue list")
    return issues


def _write_summary(path: Path, result: CleanupResult) -> None:
    counts = result.counts()
    rows = [
        "### Generated report cleanup",
        "",
        "| Selected | Closed | Skipped | Invalid markers |",
        "| ---: | ---: | ---: | ---: |",
        (
            f"| {counts['selected']} | {counts['closed']} | "
            f"{counts['skipped']} | {counts['invalid_markers']} |"
        ),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as summary:
        summary.write("\n".join(rows))


def _run_cleanup(args: argparse.Namespace, runner: GhRunner = run_gh) -> CleanupResult:
    issues = _load_open_issues(args.repo, args.label, runner)

    def close_issue(issue_number: int) -> None:
        runner(
            [
                "gh",
                "issue",
                "close",
                str(issue_number),
                "--repo",
                args.repo,
                "--comment",
                "Superseded by a newer generated evaluation report.",
            ]
        )

    result = cleanup_generated_reports(
        issues,
        workflow_identity=args.workflow_identity,
        report_kind=args.report_kind,
        close_issue=close_issue,
    )
    for decision in result.decisions:
        print(f"#{decision.issue_number}: {decision.outcome} - {decision.reason}")
    print(json.dumps(result.counts(), sort_keys=True))
    if args.summary:
        _write_summary(args.summary, result)
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    marker_parser = subparsers.add_parser("marker", help="print a canonical generated-report marker")
    marker_parser.add_argument("--workflow-identity", required=True)
    marker_parser.add_argument("--report-kind", required=True)
    marker_parser.add_argument("--report-date", required=True)

    cleanup_parser = subparsers.add_parser("cleanup", help="close matching generated report issues")
    cleanup_parser.add_argument("--repo", required=True)
    cleanup_parser.add_argument("--label", required=True)
    cleanup_parser.add_argument("--workflow-identity", required=True)
    cleanup_parser.add_argument("--report-kind", required=True)
    cleanup_parser.add_argument("--summary", type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        if args.command == "marker":
            print(build_marker(args.workflow_identity, args.report_kind, args.report_date))
        else:
            _run_cleanup(args)
    except (CleanupError, ValueError) as exc:
        print(f"generated-report cleanup failed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
