"""Tests for explicit generated-report identity and cleanup protection."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from generated_report_cleanup import (  # noqa: E402
    CleanupError,
    build_marker,
    cleanup_generated_reports,
    inspect_marker,
)

WORKFLOW_IDENTITY = "docs-eval-harness"
REPORT_KIND = "docs-evaluation"


def _body(*, workflow: str = WORKFLOW_IDENTITY, kind: str = REPORT_KIND, report_date: str = "2026-07-28") -> str:
    marker = build_marker(workflow, kind, report_date)
    return f"{marker}\n\n### Summary\nGenerated evaluation results."


def test_marker_contains_complete_machine_readable_identity():
    marker = build_marker(WORKFLOW_IDENTITY, REPORT_KIND, "2026-07-28")

    inspection = inspect_marker(marker)

    assert inspection.status == "valid"
    assert inspection.marker is not None
    assert inspection.marker.workflow_identity == WORKFLOW_IDENTITY
    assert inspection.marker.report_kind == REPORT_KIND
    assert inspection.marker.report_date == "2026-07-28"


def test_cleanup_rotates_generated_report_but_preserves_durable_same_label_issue():
    open_issues = [
        {"number": 625, "body": _body(report_date="2026-07-20")},
        {
            "number": 470,
            "body": "## Objective\nDurable evaluation harness implementation tracker without a generated-report marker.",
        },
    ]
    closed: list[int] = []

    first = cleanup_generated_reports(
        open_issues,
        workflow_identity=WORKFLOW_IDENTITY,
        report_kind=REPORT_KIND,
        close_issue=closed.append,
    )

    assert closed == [625]
    assert first.counts() == {"selected": 1, "closed": 1, "skipped": 1, "invalid_markers": 0}
    assert first.decisions[1].issue_number == 470
    assert first.decisions[1].outcome == "skipped"

    still_open = [issue for issue in open_issues if issue["number"] not in closed]
    second = cleanup_generated_reports(
        still_open,
        workflow_identity=WORKFLOW_IDENTITY,
        report_kind=REPORT_KIND,
        close_issue=closed.append,
    )

    assert closed == [625]
    assert second.counts() == {"selected": 0, "closed": 0, "skipped": 1, "invalid_markers": 0}


def test_missing_malformed_and_mismatched_markers_are_reported_and_not_closed():
    issues = [
        {"number": 1, "body": "durable tracker with no marker"},
        {"number": 2, "body": "<!-- generated-report: not-json -->"},
        {"number": 3, "body": _body(workflow="other-workflow")},
        {"number": 4, "body": _body(kind="other-report")},
    ]
    closed: list[int] = []

    result = cleanup_generated_reports(
        issues,
        workflow_identity=WORKFLOW_IDENTITY,
        report_kind=REPORT_KIND,
        close_issue=closed.append,
    )

    assert closed == []
    assert result.counts() == {"selected": 0, "closed": 0, "skipped": 4, "invalid_markers": 1}
    assert [decision.outcome for decision in result.decisions] == [
        "skipped",
        "invalid-marker",
        "skipped",
        "skipped",
    ]


def test_close_failure_is_audited_and_remains_retryable():
    issues = [{"number": 625, "body": _body()}]

    def failing_close(_issue_number: int) -> None:
        raise CleanupError("GitHub CLI command failed: gh issue close")

    first = cleanup_generated_reports(
        issues,
        workflow_identity=WORKFLOW_IDENTITY,
        report_kind=REPORT_KIND,
        close_issue=failing_close,
    )

    assert first.counts() == {"selected": 1, "closed": 0, "skipped": 1, "invalid_markers": 0}
    assert first.decisions[0].outcome == "close-failed"

    closed: list[int] = []
    second = cleanup_generated_reports(
        issues,
        workflow_identity=WORKFLOW_IDENTITY,
        report_kind=REPORT_KIND,
        close_issue=closed.append,
    )

    assert closed == [625]
    assert second.counts() == {"selected": 1, "closed": 1, "skipped": 0, "invalid_markers": 0}


def test_non_text_body_is_invalid_and_not_closed():
    closed: list[int] = []

    result = cleanup_generated_reports(
        [{"number": 10, "body": {"unexpected": "object"}}],
        workflow_identity=WORKFLOW_IDENTITY,
        report_kind=REPORT_KIND,
        close_issue=closed.append,
    )

    assert closed == []
    assert result.counts() == {"selected": 0, "closed": 0, "skipped": 1, "invalid_markers": 1}


def test_invalid_marker_contract_is_not_selected():
    invalid_bodies = [
        '<!-- generated-report: {"workflow_identity":"docs-eval-harness"} -->',
        (
            '<!-- generated-report: {"workflow_identity":"docs-eval-harness",'
            '"report_kind":"docs-evaluation","report_date":"07/28/2026"} -->'
        ),
        f"{_body()}\n{build_marker(WORKFLOW_IDENTITY, REPORT_KIND, '2026-07-27')}",
    ]

    for body in invalid_bodies:
        inspection = inspect_marker(body)
        assert inspection.status == "invalid"
