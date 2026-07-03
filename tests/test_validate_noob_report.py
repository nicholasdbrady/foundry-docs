"""Tests for scripts/validate_noob_report.py — the noob-tester quality gate.

These are structural/placeholder-rejection tests only: they assert on the
deterministic validator's pass/fail behavior and specific rejection reasons,
not on agent prose quality.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from validate_noob_report import (  # noqa: E402
    DEFAULT_ALLOWED_URL_PREFIXES,
    extract_urls,
    validate_blocked_report,
    validate_report,
)

SITE = "https://hobbyist-e43fa225.mintlify.app"

VALID_FINDINGS_REPORT = f"""
### Summary

As a brand-new user I navigated the docs-vnext site and evaluated 4 pages,
following the quickstart step by step.

Pages visited:
- {SITE}/
- {SITE}/get-started/quickstart-create-foundry-resources
- {SITE}/agents/development/overview
- {SITE}/api-sdk/sdk-overview

### Critical Issues

The quickstart page links to a section that returns a 404 when followed,
which is a broken link that blocks a beginner from continuing.

### Confusing Areas

The SDK overview introduces "Responses API" without any explanation, which
was a confusing area that slowed down my attempt to follow the tutorial.

### What Worked Well

The home page role-based cards worked well and made the get-started tab easy
to find. The quickstart's Azure CLI tab was clear and complete.

### Recommendations

1. Fix the broken 404 link on the quickstart page.
2. Add a short explanation of "Responses API" before the comparison table.
3. Consider adding a short glossary entry near the SDK overview so a beginner
   does not need to look up "Responses API" elsewhere before continuing.

This report is scoped to docs-vnext only, and every page above was fetched
directly from the live site during this run rather than assumed from memory.
""".strip()

VALID_NO_ISSUES_REPORT = f"""
### Summary

I evaluated the docs-vnext site as a complete beginner, following the
quickstart and agent development tasks step by step.

Pages visited:
- {SITE}/
- {SITE}/get-started/quickstart-create-foundry-resources
- {SITE}/agents/development/overview

### Findings

No critical issues found during this run. I attempted every step in the
quickstart and did not run into broken links or missing prerequisites. Each
task, from creating the Foundry resource to running the first API call,
completed exactly as documented, and every code block ran without edits.

### What Worked Well

The tutorial flow worked well end to end and the code examples were clear.
The agent development overview page's step-by-step walkthrough was easy to
follow without any prior Foundry experience.

### Recommendations

No changes recommended this run — the docs-vnext content held up well for a
first-time user attempting the same three tasks that previous runs have
covered. A future run should still try the SDK overview and setup/planning
pages to keep coverage broad across the site.
""".strip()

PLACEHOLDER_REPORT = f"""
### Summary

As an AI language model, I do not have access to a real browser, so this is
a placeholder report. TODO: fill this out.

Pages visited: {SITE}/ {SITE}/get-started/quickstart-create-foundry-resources
{SITE}/agents/development/overview

### Critical Issues

[Insert critical issues here]

### What Worked Well

Recommendations: TBD
""".strip()

TOO_SHORT_REPORT = f"Visited {SITE}/. No critical issue. Worked well. Recommendation: none. docs-vnext looks fine."

MISSING_RECOMMENDATIONS_REPORT = f"""
As a new user I followed the quickstart step by step and attempted every task.

Pages visited:
- {SITE}/
- {SITE}/get-started/quickstart-create-foundry-resources
- {SITE}/agents/development/overview

### Critical Issues

I found a broken 404 link on the quickstart page which is a critical failure
for a beginner trying to follow along.

### What Worked Well

The home page worked well and the role-based cards made navigation easy for
a docs-vnext beginner.
""".strip()

TOO_FEW_URLS_REPORT = f"""
As a new user I followed the quickstart step by step and attempted the first
task on the docs-vnext home page.

Pages visited:
- {SITE}/

### Critical Issues

No critical issues found in this limited check.

### What Worked Well

The home page worked well.

### Recommendations

Evaluate more pages next run.
""".strip() * 3  # pad past the word-count floor while keeping only 1 URL

VALID_BLOCKED_REPORT = f"""
### Infrastructure Blocked

The Documentation Noob Tester could not complete this run.

Attempted URL: {SITE}/

Diagnostic: the web-fetch tool returned a network timeout after 30s and the
firewall log shows the request to hobbyist-e43fa225.mintlify.app was blocked.
Playwright browser launch also failed with a connection refused error.

No pages could be evaluated this run. Retrying after the network allowlist is
confirmed is recommended before assuming docs-vnext content is at fault.
""".strip()

BLOCKED_MISSING_MARKER_REPORT = f"""
Attempted URL: {SITE}/

The request timed out and the firewall blocked the connection. Network error,
connection refused.
""".strip()

BLOCKED_MISSING_DIAGNOSTIC_REPORT = """
Infrastructure blocked: could not run this cycle.
""".strip()

BLOCKED_PLACEHOLDER_REPORT = f"""
Infrastructure blocked: TODO fill in diagnostic details. Network error.
Attempted URL: {SITE}/
""".strip()


class TestExtractUrls:
    def test_dedupes_and_strips_punctuation(self):
        text = f"See {SITE}/. Also see {SITE}/ again, and ({SITE}/get-started/quickstart-create-foundry-resources)."
        urls = extract_urls(text)
        assert urls == [
            f"{SITE}/",
            f"{SITE}/get-started/quickstart-create-foundry-resources",
        ]

    def test_filters_by_allowed_prefix(self):
        text = f"Visited {SITE}/ and also https://evil.example.com/phish"
        urls = extract_urls(text, allowed_prefixes=DEFAULT_ALLOWED_URL_PREFIXES)
        assert urls == [f"{SITE}/"]

    def test_no_urls(self):
        assert extract_urls("no links here") == []


class TestValidateReport:
    def test_valid_findings_report_passes(self):
        result = validate_report(VALID_FINDINGS_REPORT)
        assert result.ok, result.errors
        assert result.stats["url_count"] >= 3

    def test_valid_no_issues_report_passes(self):
        result = validate_report(VALID_NO_ISSUES_REPORT)
        assert result.ok, result.errors

    def test_placeholder_report_rejected(self):
        result = validate_report(PLACEHOLDER_REPORT)
        assert not result.ok
        assert any("placeholder" in err.lower() for err in result.errors)

    def test_too_short_report_rejected(self):
        result = validate_report(TOO_SHORT_REPORT)
        assert not result.ok
        assert any("too short" in err.lower() for err in result.errors)

    def test_missing_recommendations_rejected(self):
        result = validate_report(MISSING_RECOMMENDATIONS_REPORT)
        assert not result.ok
        assert any("recommendation" in err.lower() for err in result.errors)

    def test_too_few_urls_rejected(self):
        result = validate_report(TOO_FEW_URLS_REPORT)
        assert not result.ok
        assert any("url" in err.lower() for err in result.errors)

    def test_missing_scope_reference_rejected(self):
        text = VALID_FINDINGS_REPORT.replace("docs-vnext", "the site")
        result = validate_report(text)
        assert not result.ok
        assert any("docs-vnext scope" in err for err in result.errors)

    def test_custom_min_urls_and_words(self):
        # A short but otherwise well-formed report should pass with relaxed thresholds.
        text = (
            f"Followed the quickstart and attempted the first task on {SITE}/. "
            "No critical issue found. It worked well. Recommendation: keep monitoring "
            "the docs-vnext quickstart for regressions."
        )
        result = validate_report(text, min_urls=1, min_words=10)
        assert result.ok, result.errors


class TestValidateBlockedReport:
    def test_valid_blocked_report_passes(self):
        result = validate_blocked_report(VALID_BLOCKED_REPORT)
        assert result.ok, result.errors
        assert result.stats["url_count"] >= 1

    def test_missing_marker_rejected(self):
        result = validate_blocked_report(BLOCKED_MISSING_MARKER_REPORT)
        assert not result.ok
        assert any("blocked marker" in err.lower() for err in result.errors)

    def test_missing_diagnostic_rejected(self):
        result = validate_blocked_report(BLOCKED_MISSING_DIAGNOSTIC_REPORT)
        assert not result.ok
        assert any("diagnostic" in err.lower() for err in result.errors)

    def test_placeholder_blocked_report_rejected(self):
        result = validate_blocked_report(BLOCKED_PLACEHOLDER_REPORT)
        assert not result.ok
        assert any("placeholder" in err.lower() for err in result.errors)

    def test_no_attempted_url_rejected(self):
        text = "Infrastructure blocked: network error, connection timed out, firewall denied access."
        result = validate_blocked_report(text)
        assert not result.ok
        assert any("attempted url" in err.lower() for err in result.errors)
