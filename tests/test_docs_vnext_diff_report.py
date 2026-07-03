"""Tests for generate_docs_vnext_diff_report.py — bounded diff/stat artifact generator."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Import from scripts/ which isn't a package, so adjust path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from generate_docs_vnext_diff_report import (  # noqa: E402
    DiffReportError,
    MAX_MODIFIED_SAMPLE,
    analyze_directories,
    build_report,
    collect_recent_pr_activity,
    compare_file,
    list_doc_files,
    main,
    render_markdown,
)


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestListDocFiles:
    def test_lists_mdx_and_md_only(self, tmp_path):
        docs = tmp_path / "docs"
        _write(docs, "index.mdx", "hello\n")
        _write(docs, "guide/notes.md", "notes\n")
        _write(docs, "static/data/models.json", "{}")
        _write(docs, "images/logo.png", "binary")

        result = list_doc_files(docs)

        assert result == ["guide/notes.md", "index.mdx"]

    def test_missing_directory_raises(self, tmp_path):
        with pytest.raises(DiffReportError, match="Directory not found"):
            list_doc_files(tmp_path / "does-not-exist")

    def test_sorted_posix_paths(self, tmp_path):
        docs = tmp_path / "docs"
        _write(docs, "b/file.mdx", "b\n")
        _write(docs, "a/file.mdx", "a\n")
        result = list_doc_files(docs)
        assert result == ["a/file.mdx", "b/file.mdx"]


class TestCompareFile:
    def test_identical_files_return_none(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "a.mdx", "same content\nline two\n")
        _write(vnext, "a.mdx", "same content\nline two\n")

        assert compare_file("a.mdx", docs, vnext) is None

    def test_modified_file_reports_line_and_word_deltas(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "a.mdx", "one two three\nfour five\n")
        _write(vnext, "a.mdx", "one two three\nfour five six seven\nnew line here\n")

        delta = compare_file("a.mdx", docs, vnext)

        assert delta["path"] == "a.mdx"
        assert delta["linesRemoved"] >= 1
        assert delta["linesAdded"] >= 1
        assert delta["vnextWords"] > delta["docsWords"]
        assert delta["wordDelta"] == delta["vnextWords"] - delta["docsWords"]


class TestAnalyzeDirectories:
    def test_no_changes_reports_has_changes_false(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "a.mdx", "content\n")
        _write(vnext, "a.mdx", "content\n")

        result = analyze_directories(docs, vnext)

        assert result["hasChanges"] is False
        assert result["fileCounts"]["modified"] == 0
        assert result["fileCounts"]["vnextOnly"] == 0
        assert result["fileCounts"]["docsOnly"] == 0

    def test_unique_and_modified_files_are_detected(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "shared.mdx", "original\n")
        _write(vnext, "shared.mdx", "original\nplus more content here\n")
        _write(vnext, "only-in-vnext.mdx", "new glossary entry\n")
        _write(docs, "only-in-docs.mdx", "will be removed in vnext\n")

        result = analyze_directories(docs, vnext)

        assert result["hasChanges"] is True
        assert result["fileCounts"]["modified"] == 1
        assert result["fileCounts"]["vnextOnly"] == 1
        assert result["fileCounts"]["docsOnly"] == 1
        assert result["vnextOnlyFiles"]["sample"] == ["only-in-vnext.mdx"]
        assert result["docsOnlyFiles"]["sample"] == ["only-in-docs.mdx"]
        assert result["modifiedFiles"]["sample"][0]["path"] == "shared.mdx"

    def test_modified_files_are_bounded_and_sorted_by_churn(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        total_files = MAX_MODIFIED_SAMPLE + 5
        for i in range(total_files):
            _write(docs, f"file-{i:03d}.mdx", "base line\n")
            # Give file-000 the largest amount of churn so it sorts first.
            extra_lines = "\n".join(f"extra {j}" for j in range(i + 1))
            _write(vnext, f"file-{i:03d}.mdx", f"base line\n{extra_lines}\n")

        result = analyze_directories(docs, vnext)

        assert result["fileCounts"]["modified"] == total_files
        assert result["modifiedFiles"]["truncated"] is True
        assert len(result["modifiedFiles"]["sample"]) == MAX_MODIFIED_SAMPLE
        # Largest churn (highest index, most extra lines) should sort first.
        assert result["modifiedFiles"]["sample"][0]["path"] == f"file-{total_files - 1:03d}.mdx"

    def test_missing_directory_propagates_error(self, tmp_path):
        with pytest.raises(DiffReportError):
            analyze_directories(tmp_path / "docs", tmp_path / "docs-vnext")


class TestCollectRecentPrActivity:
    def test_no_repo_returns_skipped(self):
        result = collect_recent_pr_activity(None, days=7, limit=20)
        assert result["status"] == "skipped"
        assert result["pullRequests"] == []

    def test_dedupes_prs_seen_under_multiple_labels_and_filters_window(self):
        now = datetime(2026, 1, 15, tzinfo=timezone.utc)
        recent_pr = {
            "number": 1,
            "title": "Unbloat glossary",
            "url": "https://example.com/pull/1",
            "state": "MERGED",
            "createdAt": (now - timedelta(days=2)).isoformat(),
            "mergedAt": (now - timedelta(days=1)).isoformat(),
            "labels": [{"name": "docs-vnext"}, {"name": "documentation"}],
        }
        stale_pr = {
            "number": 2,
            "title": "Old change",
            "url": "https://example.com/pull/2",
            "state": "MERGED",
            "createdAt": (now - timedelta(days=30)).isoformat(),
            "mergedAt": (now - timedelta(days=29)).isoformat(),
            "labels": [{"name": "docs-vnext"}],
        }

        def fake_runner(args: list[str]) -> str:
            label = args[args.index("--search") + 1]
            if "docs-vnext" in label:
                return json.dumps([recent_pr, stale_pr])
            return json.dumps([])

        result = collect_recent_pr_activity("owner/repo", days=7, limit=20, runner=fake_runner, now=now)

        assert result["status"] == "ok"
        assert result["createdCount"] == 1
        assert result["mergedCount"] == 1
        assert result["mergeRatePercent"] == 100.0
        assert [pr["number"] for pr in result["pullRequests"]] == [1]
        assert result["pullRequests"][0]["labels"] == ["docs-vnext", "documentation"]

    def test_gh_failure_returns_blocked_without_raising(self):
        def failing_runner(_args: list[str]) -> str:
            raise subprocess.TimeoutExpired(cmd="gh", timeout=30)

        result = collect_recent_pr_activity("owner/repo", days=7, limit=20, runner=failing_runner)

        assert result["status"] == "blocked"
        assert "gh CLI" in result["error"]

    def test_malformed_json_returns_blocked(self):
        def bad_runner(_args: list[str]) -> str:
            return "not json"

        result = collect_recent_pr_activity("owner/repo", days=7, limit=20, runner=bad_runner)

        assert result["status"] == "blocked"

    def test_bounded_limit_truncates_and_flags(self):
        now = datetime(2026, 1, 15, tzinfo=timezone.utc)

        def fake_runner(args: list[str]) -> str:
            label = args[args.index("--search") + 1]
            if "docs-vnext" not in label:
                return json.dumps([])
            return json.dumps(
                [
                    {
                        "number": i,
                        "title": f"PR {i}",
                        "url": f"https://example.com/pull/{i}",
                        "state": "MERGED",
                        "createdAt": (now - timedelta(hours=i)).isoformat(),
                        "mergedAt": (now - timedelta(hours=i)).isoformat(),
                        "labels": [{"name": "docs-vnext"}],
                    }
                    for i in range(1, 6)
                ]
            )

        result = collect_recent_pr_activity("owner/repo", days=7, limit=2, runner=fake_runner, now=now)

        assert result["truncated"] is True
        assert len(result["pullRequests"]) == 2


class TestBuildReport:
    def test_empty_status_when_identical(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "a.mdx", "same\n")
        _write(vnext, "a.mdx", "same\n")

        report = build_report(docs, vnext, repo=None, pr_days=7, pr_limit=20)

        assert report["status"] == "empty"
        assert report["prActivity"]["status"] == "skipped"

    def test_ok_status_when_changed(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "a.mdx", "original\n")
        _write(vnext, "a.mdx", "changed\n")

        report = build_report(docs, vnext, repo=None, pr_days=7, pr_limit=20)

        assert report["status"] == "ok"

    def test_blocked_status_when_directory_missing(self, tmp_path):
        report = build_report(tmp_path / "docs", tmp_path / "docs-vnext", repo=None, pr_days=7, pr_limit=20)

        assert report["status"] == "blocked"
        assert "Directory not found" in report["error"]
        # A blocked report must not carry partial/unbounded file data.
        assert "fileCounts" not in report


class TestRenderMarkdown:
    def test_blocked_report_renders_minimal_markdown(self):
        report = {
            "status": "blocked",
            "error": "Directory not found: docs",
            "docsDir": "docs",
            "vnextDir": "docs-vnext",
            "generatedAt": "2026-01-01T00:00:00Z",
        }
        markdown = render_markdown(report)
        assert "Blocked" in markdown
        assert "Directory not found: docs" in markdown

    def test_empty_report_renders_no_changes_header(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "a.mdx", "same\n")
        _write(vnext, "a.mdx", "same\n")
        report = build_report(docs, vnext, repo=None, pr_days=7, pr_limit=20)

        markdown = render_markdown(report)

        assert "No Changes" in markdown
        assert "### Overview" in markdown

    def test_ok_report_includes_bounded_sections(self, tmp_path):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "shared.mdx", "original\n")
        _write(vnext, "shared.mdx", "original plus extra\n")
        _write(vnext, "new.mdx", "new content\n")
        report = build_report(docs, vnext, repo=None, pr_days=7, pr_limit=20)

        markdown = render_markdown(report)

        assert "Modified files" in markdown
        assert "new.mdx" in markdown
        assert "### Context" in markdown


class TestMain:
    def test_writes_json_and_markdown_artifacts(self, tmp_path, monkeypatch, capsys):
        docs = tmp_path / "docs"
        vnext = tmp_path / "docs-vnext"
        _write(docs, "a.mdx", "original\n")
        _write(vnext, "a.mdx", "changed content\n")
        json_out = tmp_path / "out" / "report.json"
        md_out = tmp_path / "out" / "report.md"

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "generate_docs_vnext_diff_report.py",
                "--docs-dir",
                str(docs),
                "--vnext-dir",
                str(vnext),
                "--skip-pr-activity",
                "--json-output",
                str(json_out),
                "--markdown-output",
                str(md_out),
            ],
        )

        exit_code = main()

        assert exit_code == 0
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        assert payload["status"] == "ok"
        assert md_out.read_text(encoding="utf-8").startswith("### 📊 Docs-vnext Diff Report")

    def test_returns_nonzero_exit_code_when_blocked(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "generate_docs_vnext_diff_report.py",
                "--docs-dir",
                str(tmp_path / "missing-docs"),
                "--vnext-dir",
                str(tmp_path / "missing-vnext"),
                "--skip-pr-activity",
            ],
        )

        assert main() == 2
