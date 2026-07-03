#!/usr/bin/env python3
"""
Deterministic docs-vnext diff/stat report generator.

Walks `docs/` (canonical) and `docs-vnext/` (agent-improved) to compute bounded,
machine-readable statistics comparing the two trees, and renders both JSON and
Markdown artifacts consumed by the `docs-vnext-diff-report` gh-aw workflow.

Design goals (see .github/agent-harness-map.md, issue #469):
  - All diffing/statistics happen here, deterministically, outside the agent
    prompt — no process substitution or unbounded shell loops in the workflow.
  - Every list of files is bounded (sample + total) so the report can never
    grow unbounded even if thousands of files differ.
  - Recent agentic PR activity is fetched via the `gh` CLI with a hard limit
    and a bounded timeout; failures degrade to an explicit "blocked"
    sub-status without failing the whole report (file diffing still
    succeeds and is reported).
  - No differences at all between docs/ and docs-vnext/ -> top-level status
    "empty" (the workflow should call `noop`).
  - Failure to read docs/docs-vnext -> top-level status "blocked" (the
    workflow should call `report_incomplete`).

Usage:
  python scripts/generate_docs_vnext_diff_report.py \\
      --docs-dir docs --vnext-dir docs-vnext \\
      --repo owner/repo --pr-days 7 --pr-limit 20 \\
      --json-output /tmp/gh-aw/agent/docs-vnext-diff-report.json \\
      --markdown-output /tmp/gh-aw/agent/docs-vnext-diff-report.md
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DOC_EXTENSIONS = (".mdx", ".md")

# Bounds so no artifact can grow unbounded, regardless of repo size.
MAX_DOCS_ONLY_SAMPLE = 200
MAX_VNEXT_ONLY_SAMPLE = 200
MAX_MODIFIED_SAMPLE = 50
DEFAULT_PR_DAYS = 7
DEFAULT_PR_LIMIT = 20
MAX_PR_LIMIT = 50
PR_SEARCH_LABELS = ("docs-vnext", "documentation", "automation")
GH_TIMEOUT_SECONDS = 30


class DiffReportError(RuntimeError):
    """Raised when the docs/docs-vnext trees cannot be read."""


def list_doc_files(root: Path) -> list[str]:
    """Return sorted, POSIX-style relative paths of doc files under root."""
    if not root.is_dir():
        raise DiffReportError(f"Directory not found: {root}")
    files = [
        p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.suffix.lower() in DOC_EXTENSIONS
    ]
    return sorted(files)


def _bounded_sample(items: list[Any], limit: int) -> dict[str, Any]:
    return {
        "total": len(items),
        "sample": items[:limit],
        "truncated": len(items) > limit,
    }


def compare_file(rel_path: str, docs_root: Path, vnext_root: Path) -> dict[str, Any] | None:
    """Compare a file present in both trees; return a bounded delta, or None if identical."""
    docs_lines = (docs_root / rel_path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    vnext_lines = (vnext_root / rel_path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    if docs_lines == vnext_lines:
        return None

    lines_added = 0
    lines_removed = 0
    matcher = difflib.SequenceMatcher(a=docs_lines, b=vnext_lines, autojunk=False)
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            lines_removed += a2 - a1
        if tag in ("replace", "insert"):
            lines_added += b2 - b1

    docs_words = sum(len(line.split()) for line in docs_lines)
    vnext_words = sum(len(line.split()) for line in vnext_lines)

    return {
        "path": rel_path,
        "linesAdded": lines_added,
        "linesRemoved": lines_removed,
        "docsWords": docs_words,
        "vnextWords": vnext_words,
        "wordDelta": vnext_words - docs_words,
    }


def analyze_directories(docs_dir: Path, vnext_dir: Path) -> dict[str, Any]:
    """Compute bounded file-count, unique-file, and modified-file statistics."""
    docs_files = list_doc_files(docs_dir)
    vnext_files = list_doc_files(vnext_dir)
    docs_set = set(docs_files)
    vnext_set = set(vnext_files)

    docs_only = sorted(docs_set - vnext_set)
    vnext_only = sorted(vnext_set - docs_set)
    common = sorted(docs_set & vnext_set)

    modified: list[dict[str, Any]] = []
    for rel_path in common:
        delta = compare_file(rel_path, docs_dir, vnext_dir)
        if delta is not None:
            modified.append(delta)

    # Largest churn first, so the bounded sample surfaces the most impactful changes.
    modified.sort(key=lambda d: abs(d["linesAdded"]) + abs(d["linesRemoved"]), reverse=True)

    totals = {
        "linesAdded": sum(d["linesAdded"] for d in modified),
        "linesRemoved": sum(d["linesRemoved"] for d in modified),
        "wordDelta": sum(d["wordDelta"] for d in modified),
    }

    return {
        "fileCounts": {
            "docs": len(docs_files),
            "vnext": len(vnext_files),
            "common": len(common),
            "docsOnly": len(docs_only),
            "vnextOnly": len(vnext_only),
            "modified": len(modified),
        },
        "docsOnlyFiles": _bounded_sample(docs_only, MAX_DOCS_ONLY_SAMPLE),
        "vnextOnlyFiles": _bounded_sample(vnext_only, MAX_VNEXT_ONLY_SAMPLE),
        "modifiedFiles": _bounded_sample(modified, MAX_MODIFIED_SAMPLE),
        "totals": totals,
        "hasChanges": bool(docs_only or vnext_only or modified),
    }


def _default_gh_runner(args: list[str]) -> str:
    """Run `gh <args>` with a bounded timeout and return stdout."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=GH_TIMEOUT_SECONDS,
        check=True,
    )
    return result.stdout


def fetch_label_pull_requests(
    repo: str,
    label: str,
    limit: int,
    runner: Callable[[list[str]], str],
) -> list[dict[str, Any]]:
    """Fetch a bounded list of PRs for a single label via `gh pr list`."""
    args = [
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "all",
        "--search",
        f"label:{label}",
        "--json",
        "number,title,url,state,createdAt,mergedAt,labels",
        "--limit",
        str(limit),
    ]
    raw = runner(args)
    data = json.loads(raw)
    if not isinstance(data, list):
        raise DiffReportError(f"Unexpected `gh pr list` output for label {label!r}")
    return data


def collect_recent_pr_activity(
    repo: str | None,
    days: int,
    limit: int,
    runner: Callable[[list[str]], str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Fetch bounded, recent agentic PR activity, tolerating gh CLI/API failures."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    result: dict[str, Any] = {
        "status": "skipped",
        "windowDays": days,
        "repo": repo,
        "createdCount": 0,
        "mergedCount": 0,
        "mergeRatePercent": None,
        "pullRequests": [],
        "truncated": False,
        "error": None,
    }
    if not repo:
        result["error"] = "No repository specified; skipping PR activity lookup."
        return result

    active_runner = runner or _default_gh_runner
    by_number: dict[int, dict[str, Any]] = {}
    try:
        for label in PR_SEARCH_LABELS:
            for pr in fetch_label_pull_requests(repo, label, limit, active_runner):
                number = pr.get("number")
                if number is not None:
                    by_number[number] = pr
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError, DiffReportError) as exc:
        result["status"] = "blocked"
        result["error"] = f"Could not fetch recent PR activity via gh CLI: {exc}"
        return result

    def _within_window(pr: dict[str, Any]) -> bool:
        for key in ("mergedAt", "createdAt"):
            value = pr.get(key)
            if not value:
                continue
            try:
                timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                continue
            if timestamp >= cutoff:
                return True
        return False

    recent = [pr for pr in by_number.values() if _within_window(pr)]
    recent.sort(key=lambda pr: pr.get("mergedAt") or pr.get("createdAt") or "", reverse=True)

    truncated = len(recent) > limit
    bounded = recent[:limit]
    created_count = len(bounded)
    merged_count = sum(1 for pr in bounded if pr.get("state") == "MERGED")
    merge_rate = round((merged_count / created_count) * 100, 1) if created_count else None

    result.update(
        {
            "status": "ok",
            "createdCount": created_count,
            "mergedCount": merged_count,
            "mergeRatePercent": merge_rate,
            "pullRequests": [
                {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "url": pr.get("url"),
                    "state": pr.get("state"),
                    "mergedAt": pr.get("mergedAt"),
                    "labels": sorted({lbl.get("name") for lbl in pr.get("labels", []) if isinstance(lbl, dict) and lbl.get("name")}),
                }
                for pr in bounded
            ],
            "truncated": truncated,
        }
    )
    return result


def build_report(
    docs_dir: Path,
    vnext_dir: Path,
    repo: str | None,
    pr_days: int,
    pr_limit: int,
    pr_runner: Callable[[list[str]], str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build the full bounded report, combining directory analysis and PR activity."""
    now = now or datetime.now(timezone.utc)
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        analysis = analyze_directories(docs_dir, vnext_dir)
    except DiffReportError as exc:
        return {
            "generatedAt": generated_at,
            "docsDir": str(docs_dir),
            "vnextDir": str(vnext_dir),
            "status": "blocked",
            "error": str(exc),
        }

    pr_activity = collect_recent_pr_activity(repo, pr_days, pr_limit, pr_runner, now=now)
    status = "ok" if analysis["hasChanges"] else "empty"

    report: dict[str, Any] = {
        "generatedAt": generated_at,
        "docsDir": str(docs_dir),
        "vnextDir": str(vnext_dir),
        "status": status,
        "error": None,
    }
    report.update(analysis)
    report["prActivity"] = pr_activity
    return report


def render_markdown(report: dict[str, Any]) -> str:
    """Render the human-readable Markdown artifact for the report."""
    if report["status"] == "blocked":
        return (
            "### 🚧 Docs-vnext Diff Report — Blocked\n\n"
            f"Could not generate the diff report: {report.get('error')}\n\n"
            f"- Canonical docs directory: `{report.get('docsDir')}`\n"
            f"- docs-vnext directory: `{report.get('vnextDir')}`\n"
            f"- Generated at: {report.get('generatedAt')}\n"
        )

    counts = report["fileCounts"]
    totals = report["totals"]
    pr_activity = report["prActivity"]
    lines: list[str] = []

    if report["status"] == "empty":
        lines += [
            "### 📊 Docs-vnext Diff Report — No Changes",
            "",
            "`docs/` and `docs-vnext/` are identical. Agentic workflows have not yet changed docs-vnext.",
            "",
        ]
    else:
        lines += ["### 📊 Docs-vnext Diff Report", ""]

    lines += [
        "### Overview",
        "",
        f"- **Canonical docs**: {counts['docs']} doc files",
        f"- **docs-vnext**: {counts['vnext']} doc files ({counts['vnextOnly']} unique to vnext)",
        f"- **Modified files**: {counts['modified']} files changed by agents",
        f"- **Total line changes**: +{totals['linesAdded']} / -{totals['linesRemoved']}",
        f"- **Total word delta**: {totals['wordDelta']:+d}",
        "",
        "### Agent Activity",
        "",
    ]

    if pr_activity["status"] == "ok":
        merge_rate = pr_activity["mergeRatePercent"]
        merge_rate_str = f"{merge_rate}%" if merge_rate is not None else "n/a"
        lines.append(f"- PRs in the last {pr_activity['windowDays']} days: {pr_activity['createdCount']}")
        lines.append(f"- Merged: {pr_activity['mergedCount']} ({merge_rate_str} merge rate)")
        if pr_activity["pullRequests"]:
            lines += [
                "",
                "<details><summary><b>Recent pull requests</b></summary>",
                "",
                "| PR | Title | State |",
                "| --- | --- | --- |",
            ]
            lines += [f"| [#{pr['number']}]({pr['url']}) | {pr['title']} | {pr['state']} |" for pr in pr_activity["pullRequests"]]
            lines += ["", "</details>"]
        if pr_activity.get("truncated"):
            lines.append(f"\n_Showing the {len(pr_activity['pullRequests'])} most recent matching PRs._")
    elif pr_activity["status"] == "skipped":
        lines.append(f"- PR activity lookup skipped: {pr_activity.get('error')}")
    else:
        lines.append(f"- ⚠️ PR activity lookup blocked: {pr_activity.get('error')}")
    lines.append("")

    if report["vnextOnlyFiles"]["total"]:
        sample = report["vnextOnlyFiles"]
        lines += [f"<details><summary><b>📚 New content unique to docs-vnext ({sample['total']} files)</b></summary>", ""]
        lines += [f"- `{path}`" for path in sample["sample"]]
        if sample["truncated"]:
            lines.append(f"- _...and {sample['total'] - len(sample['sample'])} more_")
        lines += ["", "</details>", ""]

    if report["modifiedFiles"]["total"]:
        sample = report["modifiedFiles"]
        lines += [
            f"<details><summary><b>📝 Modified files ({sample['total']} files)</b></summary>",
            "",
            "| File | Lines +/- | Word delta |",
            "| --- | --- | --- |",
        ]
        lines += [f"| `{item['path']}` | +{item['linesAdded']}/-{item['linesRemoved']} | {item['wordDelta']:+d} |" for item in sample["sample"]]
        if sample["truncated"]:
            lines.append(f"| _...and {sample['total'] - len(sample['sample'])} more_ | | |")
        lines += ["", "</details>", ""]

    if report["docsOnlyFiles"]["total"]:
        sample = report["docsOnlyFiles"]
        lines += [f"<details><summary><b>📄 Files only in canonical docs ({sample['total']} files)</b></summary>", ""]
        lines += [f"- `{path}`" for path in sample["sample"]]
        if sample["truncated"]:
            lines.append(f"- _...and {sample['total'] - len(sample['sample'])} more_")
        lines += ["", "</details>", ""]

    lines += [
        "### Context",
        "",
        f"- Generated at: {report['generatedAt']}",
        f"- Canonical docs directory: `{report['docsDir']}`",
        f"- docs-vnext directory: `{report['vnextDir']}`",
    ]

    return "\n".join(lines) + "\n"


def _write(path: str | None, content: str) -> None:
    if not path:
        return
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs-dir", default="docs", help="Canonical docs directory")
    parser.add_argument("--vnext-dir", default="docs-vnext", help="Agent-improved docs directory")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"), help="owner/repo for PR activity lookup")
    parser.add_argument("--pr-days", type=int, default=DEFAULT_PR_DAYS, help="Lookback window in days for PR activity")
    parser.add_argument("--pr-limit", type=int, default=DEFAULT_PR_LIMIT, help="Max PRs to include (bounded)")
    parser.add_argument("--skip-pr-activity", action="store_true", help="Skip the gh CLI PR activity lookup entirely")
    parser.add_argument("--json-output", default=None, help="Path to write the JSON artifact")
    parser.add_argument("--markdown-output", default=None, help="Path to write the Markdown artifact")
    args = parser.parse_args()

    pr_limit = min(max(args.pr_limit, 1), MAX_PR_LIMIT)
    repo = None if args.skip_pr_activity else args.repo

    report = build_report(Path(args.docs_dir), Path(args.vnext_dir), repo, args.pr_days, pr_limit)

    json_text = json.dumps(report, indent=2, sort_keys=True)
    markdown_text = render_markdown(report)

    _write(args.json_output, json_text + "\n")
    _write(args.markdown_output, markdown_text)

    # Some consoles (e.g. Windows cp1252 terminals) can't encode the emoji used
    # in the Markdown headers; fall back to a safe encoding rather than crash
    # after the artifacts have already been written successfully.
    for stream_text in (json_text, "", markdown_text):
        try:
            print(stream_text)
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or "utf-8"
            print(stream_text.encode(encoding, errors="replace").decode(encoding))

    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
