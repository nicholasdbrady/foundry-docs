from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from validate_docs_vnext_navigation import main, validate_navigation  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "docs-vnext-source-navigation.yml"


def _write_page(docs_dir: Path, route: str, body: str = "Useful documentation.\n") -> None:
    path = docs_dir / f"{route}.mdx"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: Test\ndescription: Test page description.\n---\n\n{body}", encoding="utf-8")


def _write_navigation(docs_dir: Path, pages: list[object], **extra: object) -> Path:
    docs_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "$schema": "https://mintlify.com/docs.json",
        "navigation": {"groups": [{"group": "Docs", "pages": pages}]},
        **extra,
    }
    path = docs_dir / "docs.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_valid_routes_produce_ordered_publishable_inventory(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/second", "guide/first"])
    _write_page(docs_dir, "guide/second")
    _write_page(docs_dir, "guide/first")

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "passed"
    assert [entry["route"] for entry in result["routes"]] == ["/guide/second", "/guide/first"]
    assert [entry["candidateSourcePath"] for entry in result["routes"]] == [
        "docs-vnext/guide/second.mdx",
        "docs-vnext/guide/first.mdx",
    ]


def test_named_page_object_is_included_in_ordered_inventory(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(
        docs_dir,
        [{"name": "Enterprise Planning", "page": "setup/planning"}, "setup/create-projects"],
    )
    _write_page(docs_dir, "setup/planning")
    _write_page(docs_dir, "setup/create-projects")

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "passed"
    assert [entry["route"] for entry in result["routes"]] == ["/setup/planning", "/setup/create-projects"]
    assert result["routes"][0]["sourceNavigationEntry"] == "navigation.groups[0].pages[0].page"


def test_stale_internal_link_fails_with_bounded_route_diagnostic(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/start"])
    _write_page(docs_dir, "guide/start", "Continue with the [missing guide](/guide/missing).\n")

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "failed"
    assert result["diagnostics"] == [
        {
            "sourceNavigationEntry": "navigation.groups[0].pages[0]",
            "route": "/guide/missing",
            "failureClass": "stale_internal_link",
            "candidateSourcePath": "docs-vnext/guide/missing.mdx",
            "sourcePage": "docs-vnext/guide/start.mdx",
            "link": "/guide/missing",
        }
    ]


def test_redirect_alias_is_explicit_and_satisfies_internal_links(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(
        docs_dir,
        ["guide/current"],
        redirects=[{"source": "/guide/old", "destination": "/guide/current"}],
    )
    _write_page(docs_dir, "guide/current", "The legacy route is [documented](/guide/old).\n")

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "passed"
    assert result["aliases"] == [
        {
            "kind": "alias",
            "sourceNavigationEntry": "redirects[0]",
            "route": "/guide/old",
            "destination": "/guide/current",
            "candidateSourcePath": "docs-vnext/guide/current.mdx",
        }
    ]


def test_external_navigation_link_is_retained_explicitly(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    docs_dir.mkdir()
    navigation_path = docs_dir / "docs.json"
    navigation_path.write_text(
        json.dumps({"navigation": {"tabs": [{"tab": "Support", "href": "https://support.example.com"}]}}),
        encoding="utf-8",
    )

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "passed"
    assert result["externalNavigation"] == [
        {
            "kind": "external",
            "sourceNavigationEntry": "navigation.tabs[0].href",
            "route": "https://support.example.com",
            "candidateSourcePath": "",
        }
    ]


def test_missing_source_page_fails_with_navigation_entry_and_candidate(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/missing"])

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "failed"
    assert result["diagnostics"][0] == {
        "sourceNavigationEntry": "navigation.groups[0].pages[0]",
        "route": "/guide/missing",
        "failureClass": "missing_source_page",
        "candidateSourcePath": "docs-vnext/guide/missing.mdx",
    }


def test_empty_navigable_page_fails(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/empty"])
    _write_page(docs_dir, "guide/empty", "{/* placeholder only */}\n")

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "failed"
    assert result["diagnosticSummary"]["counts"] == {"empty_navigable_page": 1}


def test_unchanged_legacy_stale_link_is_explicitly_grandfathered(tmp_path: Path) -> None:
    docs_dir = tmp_path / "current" / "docs-vnext"
    base_docs_dir = tmp_path / "base" / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/legacy"])
    _write_navigation(base_docs_dir, ["guide/legacy"])
    _write_page(docs_dir, "guide/legacy", "Old [broken link](/guide/missing).\n")
    _write_page(base_docs_dir, "guide/legacy", "Old [broken link](/guide/missing).\n")

    result = validate_navigation(docs_dir, navigation_path, base_docs_dir=base_docs_dir)

    assert result["status"] == "passed"
    assert result["linkSummary"] == {
        "currentStale": 1,
        "baselineStale": 1,
        "grandfathered": 1,
        "introduced": 0,
    }


def test_removing_route_fails_when_unchanged_page_still_links_to_it(tmp_path: Path) -> None:
    docs_dir = tmp_path / "current" / "docs-vnext"
    base_docs_dir = tmp_path / "base" / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/start"])
    _write_navigation(base_docs_dir, ["guide/start", "guide/target"])
    _write_page(docs_dir, "guide/start", "Read the [target guide](/guide/target).\n")
    _write_page(base_docs_dir, "guide/start", "Read the [target guide](/guide/target).\n")
    _write_page(base_docs_dir, "guide/target")

    result = validate_navigation(docs_dir, navigation_path, base_docs_dir=base_docs_dir)

    assert result["status"] == "failed"
    assert result["diagnosticSummary"]["counts"] == {"stale_internal_link": 1}
    assert result["diagnostics"][0]["sourcePage"] == "docs-vnext/guide/start.mdx"


def test_removing_alias_fails_when_unchanged_page_still_links_to_it(tmp_path: Path) -> None:
    docs_dir = tmp_path / "current" / "docs-vnext"
    base_docs_dir = tmp_path / "base" / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/start", "guide/current"])
    _write_navigation(
        base_docs_dir,
        ["guide/start", "guide/current"],
        redirects=[{"source": "/guide/old", "destination": "/guide/current"}],
    )
    _write_page(docs_dir, "guide/start", "Read the [legacy route](/guide/old).\n")
    _write_page(docs_dir, "guide/current")
    _write_page(base_docs_dir, "guide/start", "Read the [legacy route](/guide/old).\n")
    _write_page(base_docs_dir, "guide/current")

    result = validate_navigation(docs_dir, navigation_path, base_docs_dir=base_docs_dir)

    assert result["status"] == "failed"
    assert result["diagnosticSummary"]["counts"] == {"stale_internal_link": 1}


def test_invalid_route_target_fails_before_source_lookup(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["../outside.mdx"])

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "failed"
    assert result["diagnostics"][0]["failureClass"] == "invalid_route_target"
    assert result["diagnostics"][0]["sourceNavigationEntry"] == "navigation.groups[0].pages[0]"


def test_diagnostics_are_counted_and_bounded(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/missing-one", "guide/missing-two"])

    result = validate_navigation(docs_dir, navigation_path, max_diagnostics=1)

    assert len(result["diagnostics"]) == 1
    assert result["diagnosticSummary"] == {
        "total": 2,
        "counts": {"missing_source_page": 2},
        "truncated": True,
    }


def test_cli_writes_byte_stable_inventory(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    _write_navigation(docs_dir, ["guide/start"])
    _write_page(docs_dir, "guide/start")
    output = tmp_path / "inventory.json"

    args = ["--docs-dir", str(docs_dir), "--output", str(output)]
    assert main(args) == 0
    first = output.read_bytes()
    assert main(args) == 0

    assert output.read_bytes() == first


@pytest.mark.parametrize(
    ("navigation_content", "expected_detail"),
    [
        ("{", "Expecting property name"),
        (b"\xff", "utf-8"),
        (None, "No such file"),
    ],
)
def test_cli_writes_bounded_failure_inventory_for_json_and_io_errors(
    tmp_path: Path,
    navigation_content: str | bytes | None,
    expected_detail: str,
) -> None:
    docs_dir = tmp_path / "docs-vnext"
    docs_dir.mkdir()
    if isinstance(navigation_content, bytes):
        (docs_dir / "docs.json").write_bytes(navigation_content)
    elif navigation_content is not None:
        (docs_dir / "docs.json").write_text(navigation_content, encoding="utf-8")
    output = tmp_path / "inventory.json"

    assert main(["--docs-dir", str(docs_dir), "--output", str(output)]) == 2

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert result["diagnosticSummary"]["counts"] == {"validator_error": 1}
    assert expected_detail in result["diagnostics"][0]["detail"]
    assert len(result["diagnostics"][0]["detail"]) <= 500


def test_cli_can_initialize_uploadable_failure_inventory(tmp_path: Path) -> None:
    output = tmp_path / "inventory.json"

    assert main(["--output", str(output), "--initialize-output"]) == 0

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert result["diagnosticSummary"]["counts"] == {"workflow_incomplete": 1}


def test_link_examples_inside_code_are_not_validated_as_navigation(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/start"])
    _write_page(
        docs_dir,
        "guide/start",
        "Use this syntax:\n\n```md\n[Example](/not-a-real-route)\n```\n\n"
        "Inline code also stays literal: `[Example](/also-not-a-route)`.\n",
    )

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "passed"


def test_reference_style_internal_link_is_validated(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/start"])
    _write_page(docs_dir, "guide/start", "Read the [missing guide][missing].\n\n[missing]: /guide/missing\n")

    result = validate_navigation(docs_dir, navigation_path)

    assert result["status"] == "failed"
    assert result["diagnosticSummary"]["counts"] == {"stale_internal_link": 1}


def test_missing_navigation_pages_do_not_cascade_into_link_failures(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs-vnext"
    navigation_path = _write_navigation(docs_dir, ["guide/start", "guide/missing"])
    _write_page(docs_dir, "guide/start", "Read the [missing guide](/guide/missing).\n")

    result = validate_navigation(docs_dir, navigation_path)

    assert result["diagnosticSummary"]["counts"] == {"missing_source_page": 1}


def test_workflow_creates_stable_check_for_every_pull_request() -> None:
    workflow = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert workflow["on"]["pull_request"] == {}
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["validate-source-navigation"]["name"] == "Validate source navigation"


def test_workflow_noops_irrelevant_changes_and_gates_relevant_work() -> None:
    workflow = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["validate-source-navigation"]["steps"]
    by_name = {step["name"]: step for step in steps if "name" in step}

    detector = by_name["Detect relevant changes"]
    assert detector["id"] == "changes"
    assert "git diff --no-renames --name-only -z" in detector["run"]
    for relevant_path in (
        "docs-vnext/*",
        "scripts/validate_docs_vnext_navigation.py",
        "tests/test_validate_docs_vnext_navigation.py",
        ".github/workflows/docs-vnext-source-navigation.yml",
    ):
        assert relevant_path in detector["run"]

    assert by_name["No relevant source navigation changes"]["if"] == "steps.changes.outputs.relevant != 'true'"
    for step_name in (
        "Initialize failure inventory",
        "Install test dependencies",
        "Run navigation validator tests",
        "Prepare baseline validation inputs",
        "Validate docs-vnext source navigation",
    ):
        assert by_name[step_name]["if"] == "steps.changes.outputs.relevant == 'true'"
    assert by_name["Upload route inventory"]["if"] == "always() && steps.changes.outputs.relevant == 'true'"
