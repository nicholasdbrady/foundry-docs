#!/usr/bin/env python3
"""Deterministic quality gate for Documentation Noob Tester reports.

The Documentation Noob Tester (`.github/workflows/docs-noob-tester.md`) is an
agentic workflow that browses the live docs-vnext site and files an issue with
its findings. Left unchecked, an agent can publish a generic, success-shaped
report even when browsing was blocked (network, firewall, rendering) or when it
never actually visited any pages. This script is the deterministic gate that
sits between "agent drafted a report" and "report gets published" — it rejects
placeholder/templated bodies and enforces that a report contains concrete,
checkable evidence.

Two report shapes are validated:

- ``report`` (default): the standard noob-test findings body, published via
  `create-issue` (when real findings exist) or `noop` (when the run was
  complete but found nothing worth reporting). Requires concrete URLs, a
  docs-vnext scope reference, task-attempt evidence, friction/failure
  evidence (or an explicit "no issues found" statement), a "what worked"
  section, and recommendations.
- ``blocked``: the infrastructure-blocked body published via
  `report-incomplete` when browser/network/rendering access failed. Requires
  an explicit blocked marker, a diagnostic reason, and at least one attempted
  URL — placeholder text is rejected here too.

Usage:
    python3 scripts/validate_noob_report.py <report_path> [--mode report|blocked]

Prints a JSON object ``{"ok": bool, "mode": str, "errors": [...], "stats": {...}}``
to stdout and exits 0 if the report passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field

DEFAULT_MIN_URLS = 3
DEFAULT_MIN_WORDS = 150
DEFAULT_MIN_BLOCKED_URLS = 1

# The live docs-vnext deployment. Kept in sync with the `network.allowed`
# entry and page list in `.github/workflows/docs-noob-tester.md`.
DEFAULT_ALLOWED_URL_PREFIXES = ("https://hobbyist-e43fa225.mintlify.app/",)

# Phrases that indicate templated/unfilled or non-committal agent output
# rather than a genuine, evidence-backed report. Matched case-insensitively.
PLACEHOLDER_PATTERNS = [
    r"\blorem ipsum\b",
    r"\btodo\b",
    r"\btbd\b",
    r"\[insert[^\]]*\]",
    r"<insert[^>]*>",
    r"as an ai (language model|assistant)",
    r"\bi (do not|don't) have (access|the ability)\b",
    r"\bplaceholder\b",
    r"\bexample\.com\b",
    r"\bxxx+\b",
    r"page name here",
    r"issue description here",
    r"\bfill (this|it) (out|in)\b",
    r"\blorem\b.{0,20}\bipsum\b",
]

# Evidence categories required by the "report" mode. Each is a list of
# keyword/phrase substrings — a match on any one satisfies the category.
TASK_KEYWORDS = ["task", "attempt", "follow", "step", "tried", "navigat"]
FRICTION_KEYWORDS = ["confus", "friction", "unclear", "difficult", "hard to"]
NONE_FOUND_KEYWORDS = ["no critical issue", "no issues found", "no user-facing"]
FAILURE_KEYWORDS = [
    "critical issue",
    "broken",
    "404",
    "fail",
    "error",
    "bug",
    *NONE_FOUND_KEYWORDS,
]
WHAT_WORKED_KEYWORDS = ["what worked", "worked well", "positive feedback", "good stuff"]
RECOMMENDATION_KEYWORDS = ["recommendation", "suggest"]
SCOPE_KEYWORDS = ["docs-vnext"]

BLOCKED_MARKER_KEYWORDS = ["infrastructure blocked", "infrastructure-blocked", "blocked:"]
# Deliberately excludes "blocked" — that word alone is already covered by
# BLOCKED_MARKER_KEYWORDS, so including it here would let a bare marker with
# no real diagnostic detail satisfy both checks.
DIAGNOSTIC_KEYWORDS = [
    "timeout",
    "timed out",
    "denied",
    "unreachable",
    "refused",
    "403",
    "network",
    "firewall",
    "playwright",
    "browser",
    "dns",
    "connection",
]

URL_PATTERN = re.compile(r"https?://[^\s)\]}\"'>]+")
_TRAILING_PUNCTUATION = ").,;:*_"


@dataclass
class ValidationResult:
    """Result of validating a noob-tester report body."""

    ok: bool
    mode: str
    errors: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {"ok": self.ok, "mode": self.mode, "errors": self.errors, "stats": self.stats},
            indent=2,
        )


def _find_placeholder_matches(text: str) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in PLACEHOLDER_PATTERNS if re.search(pattern, lowered)]


def extract_urls(text: str, allowed_prefixes: tuple[str, ...] | None = None) -> list[str]:
    """Extract distinct absolute URLs referenced in the report body.

    Trailing markdown/punctuation is stripped so a URL followed by a period,
    closing paren, or markdown emphasis marker isn't mangled. When
    `allowed_prefixes` is given, only URLs starting with one of those
    prefixes are counted — this is how we distinguish "actually visited the
    live docs-vnext site" from an incidental link to an unrelated domain.
    """
    raw_matches = URL_PATTERN.findall(text)
    cleaned = [url.rstrip(_TRAILING_PUNCTUATION) for url in raw_matches]
    if allowed_prefixes:
        cleaned = [url for url in cleaned if any(url.startswith(prefix) for prefix in allowed_prefixes)]

    seen: set[str] = set()
    unique: list[str] = []
    for url in cleaned:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def _contains_any(text_lower: str, keywords: list[str]) -> bool:
    return any(keyword in text_lower for keyword in keywords)


def validate_report(
    text: str,
    min_urls: int = DEFAULT_MIN_URLS,
    min_words: int = DEFAULT_MIN_WORDS,
    allowed_url_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_URL_PREFIXES,
) -> ValidationResult:
    """Validate a standard noob-test findings/no-issues report body."""
    errors: list[str] = []
    lowered = text.lower()
    word_count = len(text.split())

    placeholder_hits = _find_placeholder_matches(text)
    if placeholder_hits:
        errors.append(f"Contains placeholder/templated language: {placeholder_hits}")

    if word_count < min_words:
        errors.append(f"Report too short ({word_count} words, need >= {min_words})")

    urls = extract_urls(text, allowed_url_prefixes)
    if len(urls) < min_urls:
        errors.append(f"Only {len(urls)} concrete docs-vnext site URL(s) found, need >= {min_urls}")

    if not _contains_any(lowered, SCOPE_KEYWORDS):
        errors.append("Report does not reference the docs-vnext scope")

    if not _contains_any(lowered, TASK_KEYWORDS):
        errors.append("Missing evidence of task attempts (e.g. 'followed', 'tried', 'navigated')")

    if not _contains_any(lowered, FRICTION_KEYWORDS) and not _contains_any(lowered, NONE_FOUND_KEYWORDS):
        errors.append("Missing evidence of observed friction, or an explicit none-found statement")

    if not _contains_any(lowered, FAILURE_KEYWORDS):
        errors.append("Missing a failures/critical-issues section (or explicit no-critical-issues statement)")

    if not _contains_any(lowered, WHAT_WORKED_KEYWORDS):
        errors.append("Missing a 'what worked well' section")

    if not _contains_any(lowered, RECOMMENDATION_KEYWORDS):
        errors.append("Missing an actionable recommendations section")

    stats = {"word_count": word_count, "url_count": len(urls), "urls": urls}
    return ValidationResult(ok=not errors, mode="report", errors=errors, stats=stats)


def validate_blocked_report(
    text: str,
    min_urls: int = DEFAULT_MIN_BLOCKED_URLS,
) -> ValidationResult:
    """Validate an infrastructure-blocked report body (published via `report-incomplete`)."""
    errors: list[str] = []
    lowered = text.lower()
    word_count = len(text.split())

    placeholder_hits = _find_placeholder_matches(text)
    if placeholder_hits:
        errors.append(f"Contains placeholder/templated language: {placeholder_hits}")

    if not _contains_any(lowered, BLOCKED_MARKER_KEYWORDS):
        errors.append("Missing an explicit infrastructure-blocked marker (e.g. 'Infrastructure blocked:')")

    if not _contains_any(lowered, DIAGNOSTIC_KEYWORDS):
        errors.append("Missing diagnostic detail (e.g. timeout, network, firewall, blocked, HTTP status)")

    urls = extract_urls(text)
    if len(urls) < min_urls:
        errors.append(f"No attempted URL referenced (need >= {min_urls})")

    stats = {"word_count": word_count, "url_count": len(urls), "urls": urls}
    return ValidationResult(ok=not errors, mode="blocked", errors=errors, stats=stats)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Documentation Noob Tester report body")
    parser.add_argument("report_path", help="Path to the draft report markdown file")
    parser.add_argument("--mode", choices=["report", "blocked"], default="report")
    parser.add_argument("--min-urls", type=int, default=None, help="Override the minimum required URL count")
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument(
        "--allowed-url-prefix",
        action="append",
        dest="allowed_url_prefixes",
        help="Restrict counted URLs to those starting with this prefix (repeatable)",
    )
    args = parser.parse_args(argv)

    with open(args.report_path, encoding="utf-8") as f:
        text = f.read()

    if args.mode == "blocked":
        min_urls = args.min_urls if args.min_urls is not None else DEFAULT_MIN_BLOCKED_URLS
        result = validate_blocked_report(text, min_urls=min_urls)
    else:
        min_urls = args.min_urls if args.min_urls is not None else DEFAULT_MIN_URLS
        prefixes = tuple(args.allowed_url_prefixes) if args.allowed_url_prefixes else DEFAULT_ALLOWED_URL_PREFIXES
        result = validate_report(text, min_urls=min_urls, min_words=args.min_words, allowed_url_prefixes=prefixes)

    print(result.to_json())
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
