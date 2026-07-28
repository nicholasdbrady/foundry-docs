"""Tests for bounded, resumable docs-vnext baseline synchronization batches."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from apply_docs_vnext_sync_batches import (  # noqa: E402
    Batch,
    BatchSyncError,
    GitHubGitBackend,
    Manifest,
    PullRequest,
    apply_batch,
    branch_name,
    build_pull_request_body,
    execute_batches,
    load_manifest,
    parse_pull_request_marker,
    plan_batches,
    select_active_manifest,
)
from generate_docs_vnext_sync_manifest import build_manifest, serialize_manifest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _metadata(content: bytes) -> dict[str, int | str]:
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def _operation(
    index: int,
    payload_bytes: int,
    *,
    decision: str = "add",
) -> dict[str, Any]:
    path = f"page-{index:02d}.mdx"
    if decision == "add":
        source = _metadata(b"s" * payload_bytes)
        target = None
    elif decision == "modify":
        source_bytes = payload_bytes // 2
        source = _metadata(b"s" * source_bytes)
        target = _metadata(b"t" * (payload_bytes - source_bytes))
    elif decision == "remove":
        source = None
        target = _metadata(b"t" * payload_bytes)
    else:
        source = _metadata(f"source-{index}".encode())
        target = _metadata(f"target-{index}".encode())
    operation: dict[str, Any] = {
        "id": f"sha256:{hashlib.sha256(f'{decision}:{path}'.encode()).hexdigest()}",
        "decision": decision,
        "path": path,
        "fileCount": 1,
        "payloadBytes": payload_bytes,
        "source": source,
        "target": target,
    }
    if decision == "preserve":
        operation["preserveRule"] = {"kind": "file", "path": path}
    return operation


def _write_manifest(
    tmp_path: Path,
    operations: list[dict[str, Any]],
    *,
    name: str = "manifest.json",
    run_id: int = 100,
) -> Manifest:
    path = tmp_path / name
    payload = {
        "schemaVersion": 2,
        "source": {"root": "docs"},
        "target": {"root": "docs-vnext"},
        "summary": {
            "operationCount": len(operations),
            "payloadBytes": sum(item["payloadBytes"] for item in operations),
        },
        "operations": operations,
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return load_manifest(path, run_id)


def _write(root: Path, relative_path: str, content: bytes | str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _pull_request(
    manifest: Manifest,
    batch: Batch,
    *,
    number: int = 1,
    state: str = "OPEN",
) -> PullRequest:
    return PullRequest(
        number=number,
        state=state,
        url=f"https://github.com/example/repo/pull/{number}",
        head_ref=branch_name(manifest, batch),
        marker=parse_pull_request_marker(build_pull_request_body(manifest, batch)),
    )


class FakeBackend:
    def __init__(
        self,
        pull_requests: list[PullRequest] | None = None,
        downloaded_manifests: dict[int, Path] | None = None,
        fail_create_batch: int | None = None,
    ) -> None:
        self.pull_requests = list(pull_requests or [])
        self.downloaded_manifests = downloaded_manifests or {}
        self.fail_create_batch = fail_create_batch
        self.published: list[int] = []
        self.created: list[int] = []
        self.reopened: list[int] = []

    def list_pull_requests(self) -> list[PullRequest]:
        return list(self.pull_requests)

    def download_manifest(self, run_id: int) -> Path:
        return self.downloaded_manifests[run_id]

    def publish_batch(self, manifest: Manifest, batch: Batch, branch: str) -> None:
        assert branch == branch_name(manifest, batch)
        self.published.append(batch.number)

    def create_pull_request(
        self,
        manifest: Manifest,
        batch: Batch,
        branch: str,
        title: str,
        body: str,
    ) -> PullRequest:
        if batch.number == self.fail_create_batch:
            raise BatchSyncError("simulated pull-request failure")
        assert manifest.digest in body
        assert title.endswith(f"batch {batch.number}/{batch.total}")
        pull_request = PullRequest(
            number=1000 + batch.number,
            state="OPEN",
            url=f"https://github.com/example/repo/pull/{1000 + batch.number}",
            head_ref=branch,
            marker=parse_pull_request_marker(body),
        )
        self.created.append(batch.number)
        self.pull_requests.append(pull_request)
        return pull_request

    def reopen_pull_request(self, pull_request: PullRequest) -> PullRequest:
        reopened = replace(pull_request, state="OPEN")
        self.reopened.append(pull_request.number)
        return reopened


def test_batch_planning_uses_inclusive_boundaries_and_preserves_order(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        [_operation(1, 4), _operation(2, 6), _operation(3, 1), _operation(4, 9)],
    )

    first = plan_batches(manifest, max_files=2, max_payload_bytes=10)
    second = plan_batches(manifest, max_files=2, max_payload_bytes=10)

    assert first == second
    assert [(batch.file_count, batch.payload_bytes) for batch in first] == [(2, 10), (2, 10)]
    assert [operation.id for batch in first for operation in batch.operations] == [
        operation.id for operation in manifest.operations
    ]
    assert len({operation.id for batch in first for operation in batch.operations}) == 4


def test_batch_planning_rejects_single_oversize_operation_before_mutation(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 11)])

    with pytest.raises(BatchSyncError, match="above the 10-byte ceiling"):
        plan_batches(manifest, max_files=5, max_payload_bytes=10)


def test_manifest_consumer_rejects_underreported_payload_accounting(tmp_path):
    operation = _operation(1, 11)
    operation["payloadBytes"] = 10

    with pytest.raises(BatchSyncError, match="conservative accounting"):
        _write_manifest(tmp_path, [operation])


def test_apply_batch_copies_adds_and_modifications_removes_and_preserves(tmp_path):
    source = tmp_path / "docs"
    target = tmp_path / "docs-vnext"
    allowlist = tmp_path / "preserve.json"
    _write(source, "add.mdx", "added")
    _write(source, "modify.mdx", "canonical")
    _write(source, "preserve.mdx", "canonical-preserved")
    _write(target, "modify.mdx", "old")
    _write(target, "remove.mdx", "remove")
    _write(target, "preserve.mdx", "customized")
    allowlist.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "preserve": [{"kind": "file", "path": "preserve.mdx"}],
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        serialize_manifest(build_manifest(source, target, allowlist, tmp_path)),
        encoding="utf-8",
        newline="\n",
    )
    manifest = load_manifest(manifest_path, 123)
    batch = plan_batches(manifest, max_files=10, max_payload_bytes=1000)[0]

    changed = apply_batch(tmp_path, manifest, batch)

    assert set(changed) == {
        "docs-vnext/add.mdx",
        "docs-vnext/modify.mdx",
        "docs-vnext/remove.mdx",
    }
    assert (target / "add.mdx").read_text(encoding="utf-8") == "added"
    assert (target / "modify.mdx").read_text(encoding="utf-8") == "canonical"
    assert not (target / "remove.mdx").exists()
    assert (target / "preserve.mdx").read_text(encoding="utf-8") == "customized"


def test_existing_open_pull_request_prevents_duplicate_publish_and_creation(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)])
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    pull_request = _pull_request(manifest, batch)
    backend = FakeBackend([pull_request])
    checkpoint = tmp_path / "checkpoint.json"

    succeeded = execute_batches(
        manifest,
        [batch],
        backend,
        [pull_request],
        checkpoint,
        max_files=1,
        max_payload_bytes=10,
    )

    assert succeeded is True
    assert backend.published == []
    assert backend.created == []
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["batches"][0]["result"] == "existing-open-pull-request"


def test_preserve_only_batch_completes_without_branch_or_pull_request(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 0, decision="preserve")])
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    backend = FakeBackend()
    checkpoint = tmp_path / "checkpoint.json"

    succeeded = execute_batches(
        manifest,
        [batch],
        backend,
        [],
        checkpoint,
        max_files=1,
        max_payload_bytes=10,
    )

    assert succeeded is True
    assert backend.published == []
    assert backend.created == []
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["batches"][0]["result"] == "preserve-only"


def test_resume_skips_merged_batch_and_creates_only_pending_batch(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1), _operation(2, 1)])
    batches = plan_batches(manifest, max_files=1, max_payload_bytes=10)
    merged = _pull_request(manifest, batches[0], state="MERGED")
    backend = FakeBackend([merged])
    checkpoint = tmp_path / "checkpoint.json"

    succeeded = execute_batches(
        manifest,
        batches,
        backend,
        [merged],
        checkpoint,
        max_files=1,
        max_payload_bytes=10,
    )

    assert succeeded is True
    assert backend.published == [2]
    assert backend.created == [2]
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert [item["result"] for item in state["batches"]] == [
        "existing-merged-pull-request",
        "created-pull-request",
    ]


def test_closed_pull_request_is_reopened_instead_of_duplicated(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)])
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    closed = _pull_request(manifest, batch, number=9, state="CLOSED")
    backend = FakeBackend([closed])

    succeeded = execute_batches(
        manifest,
        [batch],
        backend,
        [closed],
        tmp_path / "checkpoint.json",
        max_files=1,
        max_payload_bytes=10,
    )

    assert succeeded is True
    assert backend.reopened == [9]
    assert backend.published == []
    assert backend.created == []


def test_real_git_backend_recovers_existing_branch_with_added_file(tmp_path):
    remote = tmp_path / "remote.git"
    repository = tmp_path / "repository"
    runner_temp = tmp_path / "runner"
    remote.mkdir()
    repository.mkdir()
    _git(remote, "init", "--bare")
    _git(repository, "init", "--initial-branch=main")
    _git(repository, "config", "user.name", "Test User")
    _git(repository, "config", "user.email", "test@example.com")
    _write(repository / "docs", "page.mdx", "canonical")
    _write(repository / "docs-vnext", ".gitkeep", "")
    allowlist = repository / ".github" / "preserve.json"
    allowlist.parent.mkdir(parents=True)
    allowlist.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "preserve": [{"kind": "file", "path": ".gitkeep"}],
            }
        ),
        encoding="utf-8",
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "base")
    _git(repository, "remote", "add", "origin", str(remote))
    _git(repository, "push", "--set-upstream", "origin", "main")
    manifest_path = tmp_path / "git-manifest.json"
    manifest_path.write_text(
        serialize_manifest(
            build_manifest(
                repository / "docs",
                repository / "docs-vnext",
                allowlist,
                repository,
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    manifest = load_manifest(manifest_path, 456)
    batch = plan_batches(manifest, max_files=10, max_payload_bytes=1000)[0]
    branch = branch_name(manifest, batch)
    backend = GitHubGitBackend(
        repository_root=repository,
        repository="example/repository",
        base_branch="main",
        runner_temp=runner_temp,
    )

    backend.publish_batch(manifest, batch, branch)
    backend.publish_batch(manifest, batch, branch)

    result = subprocess.run(
        ["git", "--git-dir", str(remote), "show", f"{branch}:docs-vnext/page.mdx"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.stdout == "canonical"


def test_partial_failure_records_completed_failed_and_pending_batches(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        [_operation(1, 1), _operation(2, 1), _operation(3, 1)],
    )
    batches = plan_batches(manifest, max_files=1, max_payload_bytes=10)
    backend = FakeBackend(fail_create_batch=2)
    checkpoint = tmp_path / "checkpoint.json"

    succeeded = execute_batches(
        manifest,
        batches,
        backend,
        [],
        checkpoint,
        max_files=1,
        max_payload_bytes=10,
    )

    assert succeeded is False
    assert backend.published == [1, 2]
    assert backend.created == [1]
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["status"] == "failed"
    assert state["summary"] == {"completed": 1, "failed": 1, "pending": 1}
    assert [item["state"] for item in state["batches"]] == [
        "completed",
        "failed",
        "pending",
    ]
    assert "simulated pull-request failure" in state["batches"][1]["diagnostic"]


def test_active_campaign_resumes_original_retained_manifest(tmp_path):
    original = _write_manifest(
        tmp_path,
        [_operation(1, 1), _operation(2, 1)],
        name="original.json",
        run_id=200,
    )
    current = _write_manifest(
        tmp_path,
        [_operation(2, 1)],
        name="current.json",
        run_id=300,
    )
    original_batch = plan_batches(original, max_files=1, max_payload_bytes=10)[0]
    active = _pull_request(original, original_batch)
    backend = FakeBackend([active], downloaded_manifests={200: original.path})

    selected = select_active_manifest(current, backend, [active])

    assert selected.digest == original.digest
    assert selected.run_id == 200
    assert [operation.id for operation in selected.operations] == [
        operation.id for operation in original.operations
    ]


def test_pull_request_marker_round_trips_manifest_and_batch_identity(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1), _operation(2, 1)])
    batch = plan_batches(manifest, max_files=2, max_payload_bytes=10)[0]

    marker = parse_pull_request_marker(build_pull_request_body(manifest, batch))

    assert marker == {
        "schemaVersion": 1,
        "manifestSha256": manifest.digest,
        "manifestRunId": manifest.run_id,
        "batchId": batch.id,
        "batchNumber": 1,
        "batchCount": 1,
        "operationIds": [operation.id for operation in batch.operations],
    }


def test_workflow_consumes_retained_manifest_and_always_retains_checkpoint():
    workflow = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "docs-vnext-sync-batches.yml").read_text(
            encoding="utf-8"
        ),
        Loader=yaml.BaseLoader,
    )
    job = workflow["jobs"]["apply-batches"]
    steps = {step["name"]: step for step in job["steps"]}

    assert set(workflow["on"]) == {"workflow_run", "workflow_dispatch"}
    assert workflow["on"]["workflow_run"]["workflows"] == [
        "Docs-vnext Baseline Sync Manifest"
    ]
    assert workflow["permissions"] == {
        "actions": "read",
        "contents": "write",
        "pull-requests": "write",
    }
    assert "docs-vnext-sync-manifest-$MANIFEST_RUN_ID" in steps[
        "Download retained schema-v2 manifest"
    ]["run"]
    apply_step = steps["Apply resumable bounded batches"]["run"]
    assert "apply_docs_vnext_sync_batches.py" in apply_step
    assert "--max-files 50" in apply_step
    assert "--max-payload-bytes 41943040" in apply_step
    checkpoint_step = steps["Retain batch checkpoint"]
    assert checkpoint_step["if"] == "always()"
    assert checkpoint_step["with"]["if-no-files-found"] == "error"

    producer = yaml.load(
        (REPO_ROOT / ".github" / "workflows" / "docs-vnext-sync-manifest.yml").read_text(
            encoding="utf-8"
        ),
        Loader=yaml.BaseLoader,
    )
    producer_upload = producer["jobs"]["manifest"]["steps"][-1]
    assert producer_upload["with"]["retention-days"] == "90"
