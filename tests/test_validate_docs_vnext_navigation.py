from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from validate_docs_vnext_navigation import main, validate_navigation  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "docs-vnext-source-navigation.yml"
REQUIRED_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "docs-vnext-source-navigation-required.yml"


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


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _extract_git_tree(repo: Path, ref: str, destination: Path) -> Path:
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", ref, "docs-vnext"],
        check=True,
        capture_output=True,
    ).stdout
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        if sys.version_info >= (3, 12):
            tar.extractall(destination, filter="data")
        else:
            tar.extractall(destination)
    return destination / "docs-vnext"


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
    assert workflow["jobs"]["validate-source-navigation"]["name"] == "Run source navigation validation"


def test_workflow_noops_irrelevant_changes_and_gates_relevant_work() -> None:
    workflow = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["validate-source-navigation"]["steps"]
    by_name = {step["name"]: step for step in steps if "name" in step}

    detector = by_name["Detect relevant changes"]
    assert detector["id"] == "changes"
    assert 'if ! merge_base="$(git merge-base "$BASE_SHA" "$HEAD_SHA")"' in detector["run"]
    assert 'if ! git diff --no-renames --name-only -z "$merge_base" "$HEAD_SHA"' in detector["run"]
    assert '> "$changed_paths"' in detector["run"]
    assert 'done < "$changed_paths"' in detector["run"]
    assert "< <(" not in detector["run"]
    for relevant_path in (
        "docs-vnext/*",
        "scripts/validate_docs_vnext_navigation.py",
        "tests/test_validate_docs_vnext_navigation.py",
        ".github/workflows/docs-vnext-source-navigation.yml",
        ".github/workflows/docs-vnext-source-navigation-required.yml",
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


def test_workflow_fails_closed_when_path_diff_generation_fails() -> None:
    workflow = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["validate-source-navigation"]["steps"]
    detector = next(step for step in steps if step.get("name") == "Detect relevant changes")

    assert "Unable to determine the pull request merge base." in detector["run"]
    assert "Unable to enumerate pull request paths." in detector["run"]
    assert detector["run"].count("exit 1") >= 2


def test_required_context_uses_current_trusted_base_and_head_objects() -> None:
    workflow = yaml.load(REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    sentinel = workflow["jobs"]["require-source-navigation"]

    assert workflow["on"]["pull_request_target"]["types"] == [
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
        "edited",
    ]
    assert workflow["permissions"] == {"contents": "read"}
    assert sentinel["name"] == "Validate source navigation"
    checkout = sentinel["steps"][0]
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.base.sha }}"
    assert checkout["with"]["fetch-depth"] == "0"

    by_name = {step["name"]: step for step in sentinel["steps"] if "name" in step}
    classifier = by_name["Fetch and classify proposed changes"]["run"]
    assert '$(git rev-parse HEAD)" != "$BASE_SHA"' in classifier
    assert 'git fetch --no-tags origin "refs/pull/$PR_NUMBER/head"' in classifier
    assert '$(git rev-parse FETCH_HEAD)" != "$HEAD_SHA"' in classifier
    assert 'git merge-base "$BASE_SHA" "$HEAD_SHA"' in classifier
    assert 'git diff --no-renames --name-only -z "$merge_base" "$HEAD_SHA"' in classifier
    assert '> "$changed_paths"' in classifier
    assert 'git merge-tree --write-tree "$BASE_SHA" "$HEAD_SHA"' in classifier
    assert 'git cat-file -e "$merge_tree^{tree}"' in classifier
    assert 'echo "merge_tree=$merge_tree" >> "$GITHUB_OUTPUT"' in classifier
    assert 'done < "$changed_paths"' in classifier
    assert classifier.count("exit 1") >= 7


def test_required_context_never_checks_out_or_executes_untrusted_pr_code() -> None:
    workflow = yaml.load(REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["require-source-navigation"]["steps"]
    by_name = {step["name"]: step for step in steps if "name" in step}

    checkout_steps = [step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@")]
    assert len(checkout_steps) == 1
    assert checkout_steps[0]["with"]["ref"] == "${{ github.event.pull_request.base.sha }}"
    assert "GH_TOKEN" not in str(workflow)
    assert "github.event.pull_request.head.repo" not in str(workflow)
    assert "pip install" not in str(workflow)
    assert "pytest" not in str(workflow)
    assert "actions/setup-python" not in str(workflow)

    extraction = by_name["Extract proposed documentation as data"]["run"]
    assert 'git archive -o "$base_archive" "$BASE_SHA" docs-vnext' in extraction
    assert 'git archive -o "$merged_archive" "$MERGE_TREE" docs-vnext' in extraction
    assert 'git archive "$HEAD_SHA" docs-vnext' not in extraction
    assert 'tar -xf "$base_archive" -C "$base_dir"' in extraction
    assert 'tar -xf "$merged_archive" -C "$merged_dir"' in extraction
    assert 'find "$merged_dir/docs-vnext" -type l' in extraction
    validation = by_name["Validate merged docs-vnext source navigation"]["run"]
    assert "python3 -I scripts/validate_docs_vnext_navigation.py" in validation
    assert '--docs-dir "$RUNNER_TEMP/source-navigation-merged/docs-vnext"' in validation
    assert '--base-docs-dir "$RUNNER_TEMP/source-navigation-base/docs-vnext"' in validation
    assert "source-navigation-head/scripts" not in str(workflow)
    python_commands = [
        line.strip()
        for step in steps
        for line in str(step.get("run", "")).splitlines()
        if "python" in line
    ]
    assert python_commands
    assert all("python3 -I scripts/validate_docs_vnext_navigation.py" in command for command in python_commands)


def test_required_context_noops_irrelevant_and_runs_trusted_gate_for_relevant_changes() -> None:
    workflow = yaml.load(REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["require-source-navigation"]["steps"]
    by_name = {step["name"]: step for step in steps if "name" in step}

    assert "if [[ \"$relevant\" == \"true\" ]]" in by_name["Fetch and classify proposed changes"]["run"]
    assert 'echo "irrelevant=true" >> "$GITHUB_OUTPUT"' in by_name["Fetch and classify proposed changes"]["run"]
    assert by_name["No relevant source navigation changes"]["if"] == "steps.changes.outputs.irrelevant == 'true'"
    for step_name in (
        "Extract proposed documentation as data",
        "Validate merged docs-vnext source navigation",
    ):
        assert by_name[step_name]["if"] == "steps.changes.outputs.relevant == 'true'"
    assert "Install trusted test dependencies" not in by_name
    assert "Run trusted navigation validator tests" not in by_name
    assert by_name["Upload trusted route inventory"]["if"] == (
        "always() && (steps.changes.outputs.irrelevant != 'true' || steps.freshness.outputs.failure == 'true')"
    )


def test_required_context_initializes_failure_before_classification_and_uploads_failures() -> None:
    workflow = yaml.load(REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["require-source-navigation"]["steps"]
    names = [step.get("name") for step in steps]
    by_name = {step["name"]: step for step in steps if "name" in step}

    assert names.index("Initialize failure inventory") < names.index("Fetch and classify proposed changes")
    assert "if" not in by_name["Initialize failure inventory"]
    assert "$RUNNER_TEMP/source-navigation-failure-inventory.json" in by_name["Initialize failure inventory"]["run"]
    assert by_name["Upload trusted route inventory"]["if"].startswith(
        "always() && (steps.changes.outputs.irrelevant != 'true'"
    )
    classifier = by_name["Fetch and classify proposed changes"]["run"]
    assert classifier.count("exit 1") >= 7


def test_required_context_skips_successful_irrelevant_artifact() -> None:
    workflow = yaml.load(REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["require-source-navigation"]["steps"]
    by_name = {step["name"]: step for step in steps if "name" in step}

    assert by_name["No relevant source navigation changes"]["if"] == "steps.changes.outputs.irrelevant == 'true'"
    assert 'echo "irrelevant=true" >> "$GITHUB_OUTPUT"' in by_name["Fetch and classify proposed changes"]["run"]
    assert "steps.changes.outputs.irrelevant != 'true'" in by_name["Upload trusted route inventory"]["if"]


def test_stale_base_failure_rewrites_passed_inventory_before_upload() -> None:
    workflow = yaml.load(REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["require-source-navigation"]["steps"]
    by_name = {step["name"]: step for step in steps if "name" in step}
    freshness = by_name["Confirm current base branch"]

    assert freshness["id"] == "freshness"
    script = freshness["run"]
    assert 'cp "$RUNNER_TEMP/source-navigation-failure-inventory.json"' in script
    assert "tests/eval_results/docs-vnext-route-inventory.json" in script
    assert 'echo "failure=true" >> "$GITHUB_OUTPUT"' in script
    assert script.index("rewrite_failure_inventory") < script.index("exit 1")
    assert "steps.freshness.outputs.failure == 'true'" in by_name["Upload trusted route inventory"]["if"]


def test_synthetic_merge_catches_failure_that_raw_behind_head_misses(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    docs_dir = repo / "docs-vnext"
    _write_navigation(docs_dir, ["guide/start", "guide/target"])
    _write_page(docs_dir, "guide/start")
    _write_page(docs_dir, "guide/target")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "common")
    common_sha = _git(repo, "rev-parse", "HEAD")

    _git(repo, "switch", "-c", "feature")
    _write_page(docs_dir, "guide/start", "Read the [target](/guide/target).\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feature links target")
    head_sha = _git(repo, "rev-parse", "HEAD")

    _git(repo, "switch", "main")
    _write_navigation(docs_dir, ["guide/start"])
    (docs_dir / "guide" / "target.mdx").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base removes target")
    base_sha = _git(repo, "rev-parse", "HEAD")

    merge_tree = _git(repo, "merge-tree", "--write-tree", base_sha, head_sha).splitlines()[0]
    raw_docs = _extract_git_tree(repo, head_sha, tmp_path / "raw")
    common_docs = _extract_git_tree(repo, common_sha, tmp_path / "common")
    merged_docs = _extract_git_tree(repo, merge_tree, tmp_path / "merged")
    base_docs = _extract_git_tree(repo, base_sha, tmp_path / "base")

    assert validate_navigation(raw_docs, raw_docs / "docs.json", base_docs_dir=common_docs)["status"] == "passed"
    merged = validate_navigation(merged_docs, merged_docs / "docs.json", base_docs_dir=base_docs)
    assert merged["status"] == "failed"
    assert merged["diagnosticSummary"]["counts"] == {"stale_internal_link": 1}


@pytest.mark.parametrize("operation", ["modify", "delete"])
def test_trusted_surface_changes_are_rejected_even_when_renames_are_disabled(
    tmp_path: Path,
    operation: str,
) -> None:
    repo = tmp_path / operation
    trusted_path = repo / ".github" / "workflows" / "docs-vnext-source-navigation-required.yml"
    trusted_path.parent.mkdir(parents=True)
    trusted_path.write_text("trusted\n", encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "trusted base")
    base_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "switch", "-c", "feature")
    if operation == "modify":
        trusted_path.write_text("untrusted change\n", encoding="utf-8")
    else:
        trusted_path.unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", operation)
    head_sha = _git(repo, "rev-parse", "HEAD")

    changed = subprocess.run(
        ["git", "-C", str(repo), "diff", "--no-renames", "--name-only", "-z", base_sha, head_sha],
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    assert b".github/workflows/docs-vnext-source-navigation-required.yml" in changed

    workflow = yaml.load(REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    classifier = next(
        step["run"]
        for step in workflow["jobs"]["require-source-navigation"]["steps"]
        if step.get("name") == "Fetch and classify proposed changes"
    )
    assert ".github/workflows/docs-vnext-source-navigation-required.yml" in classifier
    assert "Trusted source navigation enforcement cannot be changed" in classifier
    assert "repository-admin ruleset bypass" in classifier


def test_required_context_encodes_strict_up_to_date_ruleset_prerequisite() -> None:
    workflow_text = REQUIRED_WORKFLOW_PATH.read_text(encoding="utf-8")
    workflow = yaml.load(workflow_text, Loader=yaml.BaseLoader)
    by_name = {
        step["name"]: step
        for step in workflow["jobs"]["require-source-navigation"]["steps"]
        if "name" in step
    }

    assert "REQUIRED RULESET PREREQUISITE" in workflow_text
    assert "require branches to be up to date" in workflow_text
    final_check = by_name["Confirm current base branch"]["run"]
    assert 'git ls-remote --exit-code origin "refs/heads/$BASE_REF"' in final_check
    assert '"$remote_base" != "$BASE_SHA"' in final_check
    assert "must require branches to be up to date before merging" in final_check
