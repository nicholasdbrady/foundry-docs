from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from check_hosted_docs_routes import HttpResult, check_hosted_routes, load_targets, main  # noqa: E402
from validate_docs_vnext_navigation import validate_navigation  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "docs-vnext-hosted-routes.yml"
BASE_URL = "https://docs.example.test"
SHA = "a" * 40


def _write_inventory(tmp_path: Path, routes: list[str]) -> Path:
    entries = []
    for index, route in enumerate(routes):
        source_path = tmp_path / "docs-vnext" / f"{route}.mdx"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(
            "---\n"
            f'title: "Title {index}"\n'
            f'description: "Current description for route {index}."\n'
            "---\n\n"
            f"Current hosted body marker for route {index} with enough useful documentation content.\n\n"
            f"Middle source marker for route {index} that must remain synchronized after deployment.\n\n"
            f"Final source marker for route {index} that detects stale content near the end of the page.\n",
            encoding="utf-8",
        )
        entries.append(
            {
                "kind": "page",
                "sourceNavigationEntry": f"navigation.groups[0].pages[{index}]",
                "route": f"/{route}",
                "candidateSourcePath": f"docs-vnext/{route}.mdx",
            }
        )
    inventory = {
        "schemaVersion": 1,
        "status": "passed",
        "navigationSource": "docs-vnext/docs.json",
        "routes": entries,
        "openapi": [],
    }
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    return path


def _write_openapi_inventory(tmp_path: Path, *, include_page_collision: bool = False) -> tuple[Path, dict]:
    page_routes = ["api/widgets/widgets/list-widgets"] if include_page_collision else ["guide/one"]
    inventory_path = _write_inventory(tmp_path, page_routes)
    specification = {
        "openapi": "3.1.0",
        "info": {"title": "Widgets", "version": "1.0.0"},
        "paths": {
            "/widgets": {
                "get": {
                    "operationId": "listWidgets",
                    "summary": "List widgets",
                    "tags": ["Widgets"],
                    "responses": {"200": {"description": "OK"}},
                },
                "post": {
                    "operationId": "createWidget",
                    "tags": ["Widgets"],
                    "responses": {"201": {"description": "Created"}},
                },
            }
        },
    }
    source_path = tmp_path / "docs-vnext" / "openapi" / "widgets.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(json.dumps(specification), encoding="utf-8")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory["openapi"] = [
        {
            "kind": "openapi",
            "sourceNavigationEntry": "navigation.tabs[1].groups[0].openapi",
            "route": "/api/widgets",
            "candidateSourcePath": "docs-vnext/openapi/widgets.json",
        }
    ]
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    return inventory_path, specification


def _html(index: int, body: str | None = None) -> str:
    content = body or (
        f"Current hosted body marker for route {index} with enough useful documentation content."
        f"</p><p>Middle source marker for route {index} that must remain synchronized after deployment."
        f"</p><p>Final source marker for route {index} that detects stale content near the end of the page."
    )
    return (
        "<html><head><title>"
        f"Title {index}"
        "</title></head><body><main><h1>"
        f"Title {index}"
        "</h1><p>"
        f"Current description for route {index}."
        "</p><p>"
        f"{content}"
        "</p></main></body></html>"
    )


def _run(tmp_path: Path, fetcher, routes: list[str] | None = None, **overrides):
    routes = routes or ["guide/one", "guide/two"]
    inventory = _write_inventory(tmp_path, routes)
    args = {
        "inventory_path": inventory,
        "repository_root": tmp_path,
        "base_url": BASE_URL,
        "expected_source_sha": SHA,
        "deployed_source_sha": SHA,
        "deployment_state": "success",
        "expected_environment": "staging - docs-vnext",
        "deployment_environment": "staging - docs-vnext",
        "observed_base_url": BASE_URL,
        "fetcher": fetcher,
        "workers": 2,
    }
    args.update(overrides)
    return check_hosted_routes(**args)


def test_all_inventory_routes_are_checked(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        calls.append(url)
        if url == f"{BASE_URL}/":
            return HttpResult(200, "<html><main>Healthy host preflight content.</main></html>", url)
        index = 0 if url.endswith("/guide/one") else 1
        return HttpResult(200, _html(index), url)

    report = _run(tmp_path, fetcher)

    assert report["status"] == "passed"
    assert report["routeSummary"] == {"required": 2, "checked": 2, "passed": 2, "failed": 0}
    assert sorted(calls) == sorted([f"{BASE_URL}/", f"{BASE_URL}/guide/one", f"{BASE_URL}/guide/two"])


def test_openapi_sources_and_operations_are_expanded_and_deduped_with_pages(tmp_path: Path) -> None:
    inventory, specification = _write_openapi_inventory(tmp_path, include_page_collision=True)
    calls: list[str] = []

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        calls.append(url)
        if url.endswith("/openapi/widgets.json"):
            return HttpResult(200, json.dumps(specification), url)
        if url.endswith("/api/widgets/widgets/post-widgets"):
            return HttpResult(
                200,
                "<html><body><main><h1>POST /widgets</h1><p>"
                + ("Create a widget through this operation. " * 6)
                + "</p></main></body></html>",
                url,
            )
        return HttpResult(200, _html(0), url)

    report = check_hosted_routes(
        inventory_path=inventory,
        repository_root=tmp_path,
        base_url=BASE_URL,
        expected_source_sha=SHA,
        deployed_source_sha=SHA,
        deployment_state="success",
        expected_environment="staging - docs-vnext",
        deployment_environment="staging - docs-vnext",
        observed_base_url=BASE_URL,
        fetcher=fetcher,
    )

    assert report["status"] == "passed"
    assert report["targetSummary"] == {
        "pageEntries": 1,
        "uniquePageRoutes": 1,
        "openapiSources": 1,
        "openapiOperations": 2,
        "requiredTargets": 3,
    }
    assert report["routeSummary"] == {"required": 3, "checked": 3, "passed": 3, "failed": 0}
    assert calls.count(f"{BASE_URL}/api/widgets/widgets/list-widgets") == 1
    assert sorted(calls) == sorted(
        [
            f"{BASE_URL}/",
            f"{BASE_URL}/api/widgets/widgets/list-widgets",
            f"{BASE_URL}/openapi/widgets.json",
            f"{BASE_URL}/api/widgets/widgets/post-widgets",
        ]
    )


def test_stale_hosted_openapi_source_fails_readiness(tmp_path: Path) -> None:
    inventory, _specification = _write_openapi_inventory(tmp_path)

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url.endswith("/openapi/widgets.json"):
            return HttpResult(200, json.dumps({"openapi": "3.1.0", "paths": {}}), url)
        if url.endswith("/api/widgets/widgets/list-widgets"):
            return HttpResult(
                200,
                "<html><body><main><h1>List widgets</h1><p>GET /widgets</p>"
                + ("Current API operation content. " * 6)
                + "</main></body></html>",
                url,
            )
        if url.endswith("/api/widgets/widgets/post-widgets"):
            return HttpResult(
                200,
                "<html><body><main><h1>POST /widgets</h1><p>"
                + ("Current API operation content. " * 6)
                + "</p></main></body></html>",
                url,
            )
        return HttpResult(200, _html(0), url)

    report = check_hosted_routes(
        inventory_path=inventory,
        repository_root=tmp_path,
        base_url=BASE_URL,
        expected_source_sha=SHA,
        deployed_source_sha=SHA,
        deployment_state="success",
        expected_environment="staging - docs-vnext",
        deployment_environment="staging - docs-vnext",
        observed_base_url=BASE_URL,
        fetcher=fetcher,
    )

    assert report["status"] == "failed"
    assert report["diagnosticSummary"]["counts"] == {"stale_openapi_source": 1}
    assert report["diagnostics"][0]["route"] == "/openapi/widgets.json"


def test_repository_inventory_expands_expected_pages_and_openapi_operations(tmp_path: Path) -> None:
    docs_dir = REPO_ROOT / "docs-vnext"
    inventory = validate_navigation(docs_dir, docs_dir / "docs.json", base_docs_dir=docs_dir)
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    _inventory, targets, summary = load_targets(inventory_path, REPO_ROOT)

    assert summary == {
        "pageEntries": 527,
        "uniquePageRoutes": 526,
        "openapiSources": 2,
        "openapiOperations": 123,
        "requiredTargets": 651,
    }
    assert len(targets) == 651
    routes = {target.route for target in targets}
    assert "/openapi/openai-v1-stable.json" in routes
    assert "/openapi/projects-stable.json" in routes
    assert "/api-reference/openai-v1/batch/creates-and-executes-a-batch-from-an-uploaded-file-of-requests" in routes
    assert "/api-reference/projects/datasets/patch-datasets-versions" in routes


def test_route_failure_preserves_inventory_evidence(tmp_path: Path) -> None:
    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url.endswith("/guide/two"):
            return HttpResult(404, "<html><main>Not found</main></html>", url)
        index = 0
        return HttpResult(200, _html(index), url)

    report = _run(tmp_path, fetcher)

    assert report["status"] == "failed"
    assert report["routeSummary"]["failed"] == 1
    assert report["diagnostics"] == [
        {
            "route": "/guide/two",
            "sourceNavigationEntry": "navigation.groups[0].pages[1]",
            "candidateSourcePath": "docs-vnext/guide/two.mdx",
            "responseStatus": 404,
            "failureClass": "route_missing",
            "detail": "hosted route returned 404",
        }
    ]


def test_empty_and_stale_content_fail_readiness(tmp_path: Path) -> None:
    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url.endswith("/guide/one"):
            return HttpResult(200, "<html><main>FAQ</main></html>", url)
        if url.endswith("/guide/two"):
            return HttpResult(
                200,
                "<html><head><title>Old page</title></head><body><main>"
                + ("Old hosted content. " * 20)
                + "</main></body></html>",
                url,
            )
        return HttpResult(200, "<html><main>Healthy host preflight content.</main></html>", url)

    report = _run(tmp_path, fetcher)

    assert report["status"] == "failed"
    assert report["diagnosticSummary"]["counts"] == {"empty_content": 1, "stale_content": 1}


def test_late_source_change_is_detected_as_stale_content(tmp_path: Path) -> None:
    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url.endswith("/guide/two"):
            body = (
                "Current hosted body marker for route 1 with enough useful documentation content."
                "</p><p>Middle source marker for route 1 that must remain synchronized after deployment."
                "</p><p>Old final content that no longer matches the source."
            )
            return HttpResult(200, _html(1, body), url)
        return HttpResult(200, _html(0), url)

    report = _run(tmp_path, fetcher)

    assert report["status"] == "failed"
    assert report["diagnosticSummary"]["counts"] == {"stale_content": 1}
    assert report["diagnostics"][0]["route"] == "/guide/two"


def test_host_unavailability_is_blocked_without_false_route_success(tmp_path: Path) -> None:
    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        return HttpResult(None, "", url, "TimeoutError: timed out")

    report = _run(tmp_path, fetcher)

    assert report["status"] == "blocked"
    assert report["routeSummary"] == {"required": 2, "checked": 0, "passed": 0, "failed": 0}
    assert report["diagnosticSummary"]["counts"] == {"host_unavailable": 1}


def test_uniform_infrastructure_4xx_is_host_unavailable(tmp_path: Path) -> None:
    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url == f"{BASE_URL}/":
            return HttpResult(200, "<html><main>Healthy host preflight content.</main></html>", url)
        return HttpResult(429, "<html><main>Rate limited</main></html>", url)

    report = _run(tmp_path, fetcher)

    assert report["status"] == "blocked"
    assert report["diagnosticSummary"]["counts"] == {"host_unavailable": 1, "route_http_error": 2}


def test_cross_origin_preflight_is_host_unavailable(tmp_path: Path) -> None:
    report = _run(
        tmp_path,
        lambda _url, _timeout, _max_bytes: HttpResult(
            200,
            "<html><main>Unexpected external content.</main></html>",
            "https://other.example.test/",
        ),
    )

    assert report["status"] == "blocked"
    assert report["diagnosticSummary"]["counts"] == {"host_unavailable": 1}


def test_cross_origin_route_redirect_fails_that_route(tmp_path: Path) -> None:
    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url == f"{BASE_URL}/":
            return HttpResult(200, "<html><main>Healthy host preflight content.</main></html>", url)
        if url.endswith("/guide/two"):
            return HttpResult(200, _html(1), "https://other.example.test/guide/two")
        return HttpResult(200, _html(0), url)

    report = _run(tmp_path, fetcher)

    assert report["status"] == "failed"
    assert report["diagnosticSummary"]["counts"] == {"cross_origin_redirect": 1}
    assert report["diagnostics"][0]["route"] == "/guide/two"


def test_missing_host_configuration_blocks_before_inventory_or_http(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        calls.append(url)
        raise AssertionError("HTTP must not run without hosted configuration")

    report = check_hosted_routes(
        inventory_path=tmp_path / "missing.json",
        repository_root=tmp_path,
        base_url="",
        expected_source_sha=SHA,
        deployed_source_sha=SHA,
        deployment_state="success",
        expected_environment="staging - docs-vnext",
        deployment_environment="staging - docs-vnext",
        observed_base_url="",
        fetcher=fetcher,
    )

    assert report["status"] == "blocked"
    assert report["diagnosticSummary"]["counts"] == {"host_configuration_missing": 1}
    assert calls == []


def test_invalid_host_configuration_with_path_blocks(tmp_path: Path) -> None:
    report = _run(tmp_path, lambda url, _timeout, _max_bytes: HttpResult(200, _html(0), url), base_url=f"{BASE_URL}/docs")

    assert report["status"] == "blocked"
    assert report["diagnosticSummary"]["counts"] == {"host_configuration_invalid": 1}


def test_missing_deployment_environment_url_blocks_before_http(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        calls.append(url)
        raise AssertionError("HTTP must not run without deployment environment_url")

    report = _run(
        tmp_path,
        fetcher,
        observed_base_url="",
    )

    assert report["status"] == "blocked"
    assert report["diagnosticSummary"]["counts"] == {"deployment_url_missing": 1}
    assert calls == []


def test_normalized_deployment_origin_must_match_configured_origin(tmp_path: Path) -> None:
    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        index = 0 if url.endswith("/guide/one") else 1
        return HttpResult(200, _html(index), url)

    passed = _run(
        tmp_path,
        fetcher,
        base_url="https://DOCS.example.test/",
        observed_base_url="https://docs.example.test:443/deployment/status",
    )
    mismatched = _run(
        tmp_path,
        fetcher,
        observed_base_url="https://other.example.test/",
    )

    assert passed["status"] == "passed"
    assert mismatched["status"] == "blocked"
    assert mismatched["diagnosticSummary"]["counts"] == {"deployment_url_mismatch": 1}


def test_stale_deployment_blocks_before_route_requests(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        calls.append(url)
        return HttpResult(200, "<html><main>Unexpected request</main></html>", url)

    report = _run(tmp_path, fetcher, deployed_source_sha="b" * 40)

    assert report["status"] == "blocked"
    assert report["routeSummary"]["checked"] == 0
    assert report["diagnosticSummary"]["counts"] == {"stale_deployment": 1}
    assert calls == []


def test_failed_deployment_is_distinct_from_route_failure(tmp_path: Path) -> None:
    report = _run(
        tmp_path,
        lambda url, _timeout, _max_bytes: HttpResult(200, _html(0), url),
        deployment_state="failure",
    )

    assert report["status"] == "blocked"
    assert report["routeSummary"]["checked"] == 0
    assert report["diagnosticSummary"]["counts"] == {"deployment_failed": 1}


def test_shared_hosting_origin_blocks_colliding_deployment_projects(tmp_path: Path) -> None:
    report = _run(
        tmp_path,
        lambda url, _timeout, _max_bytes: HttpResult(200, _html(0), url),
        conflicting_environment="staging - docs",
        conflicting_source_sha="b" * 40,
        conflicting_base_url=BASE_URL,
    )

    assert report["status"] == "blocked"
    assert report["routeSummary"]["checked"] == 0
    assert report["diagnosticSummary"]["counts"] == {"deployment_host_collision": 1}


def test_diagnostics_are_bounded_but_total_counts_are_complete(tmp_path: Path) -> None:
    routes = [f"guide/{index}" for index in range(5)]

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url == f"{BASE_URL}/":
            return HttpResult(200, "<html><main>Healthy host preflight content.</main></html>", url)
        return HttpResult(404, "<html><main>Not found</main></html>", url)

    report = _run(tmp_path, fetcher, routes=routes, max_diagnostics=2)

    assert report["diagnosticSummary"] == {
        "total": 5,
        "counts": {"route_missing": 5},
        "truncated": True,
    }
    assert len(report["diagnostics"]) == 2


def test_invalid_inventory_is_blocked(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"schemaVersion": 1, "status": "failed", "routes": []}), encoding="utf-8")

    report = check_hosted_routes(
        inventory_path=inventory,
        repository_root=tmp_path,
        base_url=BASE_URL,
        expected_source_sha=SHA,
        deployed_source_sha=SHA,
        deployment_state="success",
        expected_environment="staging - docs-vnext",
        deployment_environment="staging - docs-vnext",
        observed_base_url=BASE_URL,
    )

    assert report["status"] == "blocked"
    assert report["diagnosticSummary"]["counts"] == {"source_inventory_invalid": 1}


def test_duplicate_navigation_entries_probe_a_route_once(tmp_path: Path) -> None:
    inventory = _write_inventory(tmp_path, ["guide/one"])
    data = json.loads(inventory.read_text(encoding="utf-8"))
    duplicate = dict(data["routes"][0])
    duplicate["sourceNavigationEntry"] = "navigation.groups[1].pages[0]"
    data["routes"].append(duplicate)
    inventory.write_text(json.dumps(data), encoding="utf-8")
    route_calls: list[str] = []

    def fetcher(url: str, _timeout: float, _max_bytes: int) -> HttpResult:
        if url != f"{BASE_URL}/":
            route_calls.append(url)
        return HttpResult(200, _html(0), url)

    report = check_hosted_routes(
        inventory_path=inventory,
        repository_root=tmp_path,
        base_url=BASE_URL,
        expected_source_sha=SHA,
        deployed_source_sha=SHA,
        deployment_state="success",
        expected_environment="staging - docs-vnext",
        deployment_environment="staging - docs-vnext",
        observed_base_url=BASE_URL,
        fetcher=fetcher,
    )

    assert report["status"] == "passed"
    assert report["routeSummary"]["required"] == 1
    assert route_calls == [f"{BASE_URL}/guide/one"]


def test_initialize_output_is_uploadable_and_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    summary = tmp_path / "summary.md"

    exit_code = main(
        [
            "--base-url",
            BASE_URL,
            "--output",
            str(output),
            "--summary-output",
            str(summary),
            "--initialize-output",
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert report["status"] == "blocked"
    assert report["diagnosticSummary"]["counts"] == {"workflow_incomplete": 1}
    assert summary.is_file()


def test_workflow_runs_after_deployment_and_on_schedule_with_retained_diagnostics() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    triggers = workflow.get("on") or workflow.get(True)
    assert "deployment_status" in triggers
    assert triggers["schedule"]
    assert "workflow_dispatch" in triggers
    assert workflow["permissions"] == {"contents": "read", "deployments": "read"}
    assert workflow["env"]["DOCS_VNEXT_BASE_URL"] == "${{ vars.DOCS_VNEXT_BASE_URL }}"

    job = workflow["jobs"]["hosted-route-readiness"]
    assert "staging - docs-vnext" in job["if"]
    assert "staging - docs" in job["if"]
    assert "success" in job["if"]
    assert "failure" in job["if"]
    checkout = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["ref"] == "main"
    assert checkout["with"]["fetch-depth"] == 0
    by_name = {step.get("name"): step for step in job["steps"] if "name" in step}
    assert "Initialize blocked diagnostics" in by_name
    assert "Generate validated route inventory" in by_name
    assert "Resolve hosted deployment" in by_name
    assert "Check every hosted route" in by_name
    assert by_name["Upload hosted route diagnostics"]["if"] == "always()"
    assert by_name["Upload hosted route diagnostics"]["with"]["retention-days"] == 30
    assert by_name["Publish hosted readiness summary"]["if"] == "always()"

    resolver = by_name["Resolve hosted deployment"]["run"]
    assert "repos/$GITHUB_REPOSITORY/deployments" in resolver
    assert "deployment_status" in resolver
    assert "HEAD:docs-vnext" in resolver
    assert "$deployed_commit_sha:docs-vnext" in resolver
    checker = by_name["Check every hosted route"]["run"]
    assert "docs-vnext-route-inventory.json" in checker
    assert "--expected-source-sha" in checker
    assert "--deployed-source-sha" in checker
    assert "--conflicting-base-url" in checker


def test_intended_deployment_status_path_resolves_deployed_docs_tree(tmp_path: Path) -> None:
    git = shutil.which("git")
    bash_candidates = (
        [
            Path(os.environ.get("ProgramFiles", "")) / "Git" / "bin" / "bash.exe",
            Path(git).parent.parent / "bin" / "bash.exe",
        ]
        if git and os.name == "nt"
        else []
    )
    bash_candidates.append(Path(shutil.which("bash") or ""))
    bash = next((candidate for candidate in bash_candidates if candidate.is_file()), None)
    if bash is None:
        raise AssertionError("bash is required to execute the workflow resolver")

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    docs_dir = repo / "docs-vnext"
    docs_dir.mkdir()
    (docs_dir / "docs.json").write_text('{"navigation": {"groups": []}}\n', encoding="utf-8")
    subprocess.run(["git", "add", "docs-vnext/docs.json"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True, capture_output=True)
    commit_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree_sha = subprocess.run(
        ["git", "rev-parse", "HEAD:docs-vnext"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["hosted-route-readiness"]["steps"]
    resolver = next(step for step in steps if step.get("name") == "Resolve hosted deployment")["run"]
    script = repo / "resolver.sh"
    script.write_text("#!/usr/bin/env bash\ngh() { return 0; }\n" + resolver, encoding="utf-8", newline="\n")
    output_path = tmp_path / "github-output"
    env = {
        **os.environ,
        "GH_TOKEN": "test-token",
        "GITHUB_REPOSITORY": "owner/repo",
        "GITHUB_OUTPUT": output_path.as_posix(),
        "DOCS_VNEXT_ENVIRONMENT": "staging - docs-vnext",
        "DOCS_PRIMARY_ENVIRONMENT": "staging - docs",
        "EVENT_NAME": "deployment_status",
        "EVENT_ENVIRONMENT": "staging - docs-vnext",
        "EVENT_SHA": commit_sha,
        "EVENT_STATE": "success",
        "EVENT_URL": BASE_URL,
    }

    subprocess.run([str(bash), script.as_posix()], cwd=repo, env=env, check=True, capture_output=True, text=True)

    outputs = dict(
        line.split("=", 1)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )
    assert outputs["expected_sha"] == tree_sha
    assert outputs["deployed_commit_sha"] == commit_sha
    assert outputs["deployed_sha"] == tree_sha
    assert outputs["environment"] == "staging - docs-vnext"
    assert outputs["state"] == "success"
    assert outputs["observed_url"] == BASE_URL
