"""Tests for bounded, resumable docs-vnext baseline synchronization batches."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
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
    OrphanBranch,
    PullRequest,
    apply_batch,
    branch_name,
    build_pull_request_body,
    enforce_campaign_candidate_limit,
    execute_batches,
    load_manifest,
    parse_commit_identity,
    parse_pull_request_marker,
    parse_remote_branch_refs,
    plan_batches,
    select_active_manifest,
    validate_campaign_identities,
    validate_marker_claim,
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


def _tree_manifest(
    root: Path,
    source_files: dict[str, str],
    target_files: dict[str, str],
    *,
    run_id: int = 100,
) -> Manifest:
    source = root / "docs"
    target = root / "docs-vnext"
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    for path, content in source_files.items():
        _write(source, path, content)
    for path, content in target_files.items():
        _write(target, path, content)
    allowlist = root / "preserve.json"
    allowlist.write_text(
        json.dumps({"schemaVersion": 1, "preserve": []}),
        encoding="utf-8",
    )
    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        serialize_manifest(build_manifest(source, target, allowlist, root)),
        encoding="utf-8",
        newline="\n",
    )
    return load_manifest(manifest_path, run_id)


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
        remote_branches: set[str] | None = None,
        pull_request_identities: dict[int, OrphanBranch] | None = None,
    ) -> None:
        self.pull_requests = list(pull_requests or [])
        self.downloaded_manifests = downloaded_manifests or {}
        self.fail_create_batch = fail_create_batch
        self.published: list[int] = []
        self.created: list[int] = []
        self.reopened: list[int] = []
        self.remote_branches = set(remote_branches or set())
        self.branch_identities: dict[str, OrphanBranch] = {}
        self.pull_request_identities = dict(pull_request_identities or {})
        for pull_request in self.pull_requests:
            marker = pull_request.marker
            if marker is not None and pull_request.number not in self.pull_request_identities:
                self.pull_request_identities[pull_request.number] = OrphanBranch(
                    head_ref=pull_request.head_ref,
                    manifest_digest=marker["manifestSha256"],
                    manifest_run_id=marker["manifestRunId"],
                    batch_id=marker["batchId"],
                    pull_request_number=pull_request.number,
                )
        self.verified_branches: list[int] = []
        self.reconstructed_branches: list[int] = []
        self.downloaded_run_ids: list[int] = []

    def list_pull_requests(self) -> list[PullRequest]:
        return list(self.pull_requests)

    def discover_campaign_branches(
        self, pull_requests: list[PullRequest]
    ) -> list[OrphanBranch]:
        pull_request_heads = {pull_request.head_ref for pull_request in pull_requests}
        identities = [
            identity
            for branch, identity in self.branch_identities.items()
            if branch in self.remote_branches and branch not in pull_request_heads
        ]
        for pull_request in pull_requests:
            if not pull_request.incomplete or not pull_request.head_ref.startswith(
                "automation/docs-vnext-sync/"
            ):
                continue
            identity = self.pull_request_identities.get(pull_request.number)
            if identity is None:
                raise BatchSyncError(
                    f"Pull request #{pull_request.number} has no recoverable head identity"
                )
            validate_marker_claim(pull_request, identity)
            identities.append(identity)
        return identities

    def download_manifest(self, run_id: int) -> Path:
        self.downloaded_run_ids.append(run_id)
        try:
            return self.downloaded_manifests[run_id]
        except KeyError as exc:
            raise BatchSyncError(
                f"Manifest artifact for workflow run {run_id} is unavailable"
            ) from exc

    def publish_batch(self, manifest: Manifest, batch: Batch, branch: str) -> None:
        assert branch == branch_name(manifest, batch)
        if branch in self.remote_branches:
            self.verified_branches.append(batch.number)
        else:
            self.remote_branches.add(branch)
            self.reconstructed_branches.append(batch.number)
        self.branch_identities[branch] = OrphanBranch(
            head_ref=branch,
            manifest_digest=manifest.digest,
            manifest_run_id=manifest.run_id,
            batch_id=batch.id,
        )
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


def test_file_replaces_directory_atomically_under_batch_boundary_pressure(tmp_path):
    root = tmp_path / "file-replaces-directory"
    manifest = _tree_manifest(
        root,
        {"a.mdx": "independent", "swap": "replacement-file"},
        {"swap/child.mdx": "old-child"},
    )

    batches = plan_batches(manifest, max_files=2, max_payload_bytes=1000)

    assert [[operation.path for operation in batch.operations] for batch in batches] == [
        ["a.mdx"],
        ["swap", "swap/child.mdx"],
    ]
    apply_batch(root, manifest, batches[1])
    assert (root / "docs-vnext" / "swap").read_text(encoding="utf-8") == "replacement-file"


def test_directory_replaces_file_atomically_under_batch_boundary_pressure(tmp_path):
    root = tmp_path / "directory-replaces-file"
    manifest = _tree_manifest(
        root,
        {"a.mdx": "independent", "swap/child.mdx": "replacement-child"},
        {"swap": "old-file"},
    )

    batches = plan_batches(manifest, max_files=2, max_payload_bytes=1000)

    assert [[operation.path for operation in batch.operations] for batch in batches] == [
        ["a.mdx"],
        ["swap/child.mdx", "swap"],
    ]
    apply_batch(root, manifest, batches[1])
    assert (root / "docs-vnext" / "swap" / "child.mdx").read_text(
        encoding="utf-8"
    ) == "replacement-child"


def test_atomic_path_dependency_fails_closed_when_group_exceeds_ceiling(tmp_path):
    root = tmp_path / "oversize-replacement"
    manifest = _tree_manifest(
        root,
        {"swap": "replacement-file"},
        {"swap/child.mdx": "old-child"},
    )

    with pytest.raises(BatchSyncError, match="Atomic path dependency.*exceeding ceilings"):
        plan_batches(manifest, max_files=1, max_payload_bytes=1000)


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
    backend = FakeBackend([pull_request], remote_branches={branch_name(manifest, batch)})
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
    assert backend.published == [1]
    assert backend.verified_branches == [1]
    assert backend.created == []
    state = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert state["batches"][0]["result"] == "existing-open-pull-request"


def test_open_pull_request_with_missing_branch_is_reconstructed_before_completion(tmp_path):
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
    assert backend.published == [1]
    assert backend.reconstructed_branches == [1]
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


def test_closed_pull_request_with_missing_branch_is_reconstructed_before_reopen(tmp_path):
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
    assert backend.published == [1]
    assert backend.reconstructed_branches == [1]
    assert backend.verified_branches == []
    assert backend.created == []


def test_closed_pull_request_with_existing_branch_is_verified_before_reopen(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)])
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    branch = branch_name(manifest, batch)
    closed = _pull_request(manifest, batch, number=9, state="CLOSED")
    backend = FakeBackend([closed], remote_branches={branch})

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
    assert backend.published == [1]
    assert backend.reconstructed_branches == []
    assert backend.verified_branches == [1]
    assert backend.created == []


def test_real_git_backend_recovers_branch_with_add_and_path_replacements(tmp_path):
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
    _write(repository / "docs", "file-replacement", "replacement-file")
    _write(repository / "docs", "directory-replacement/child.mdx", "replacement-child")
    _write(repository / "docs-vnext", ".gitkeep", "")
    _write(repository / "docs-vnext", "file-replacement/old-child.mdx", "old-child")
    _write(repository / "docs-vnext", "directory-replacement", "old-file")
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
    orphans = backend.discover_campaign_branches([])
    backend.publish_batch(manifest, batch, branch)

    assert orphans == [
        OrphanBranch(
            head_ref=branch,
            manifest_digest=manifest.digest,
            manifest_run_id=manifest.run_id,
            batch_id=batch.id,
        )
    ]
    result = subprocess.run(
        ["git", "--git-dir", str(remote), "show", f"{branch}:docs-vnext/page.mdx"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.stdout == "canonical"
    file_replacement = subprocess.run(
        ["git", "--git-dir", str(remote), "show", f"{branch}:docs-vnext/file-replacement"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert file_replacement.stdout == "replacement-file"
    directory_replacement = subprocess.run(
        [
            "git",
            "--git-dir",
            str(remote),
            "show",
            f"{branch}:docs-vnext/directory-replacement/child.mdx",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert directory_replacement.stdout == "replacement-child"


def test_real_git_backend_rejects_force_pushed_open_pr_branch(tmp_path):
    remote = tmp_path / "forged-remote.git"
    repository = tmp_path / "forged-repository"
    runner_temp = tmp_path / "forged-runner"
    remote.mkdir()
    repository.mkdir()
    _git(remote, "init", "--bare")
    _git(repository, "init", "--initial-branch=main")
    _git(repository, "config", "user.name", "Test User")
    _git(repository, "config", "user.email", "test@example.com")
    _write(repository / "docs", "page.mdx", "canonical")
    _write(repository / "docs-vnext", ".gitkeep", "")
    allowlist = repository / "preserve.json"
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
    manifest_path = tmp_path / "forged-manifest.json"
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
    manifest = load_manifest(manifest_path, 789)
    batch = plan_batches(manifest, max_files=10, max_payload_bytes=1000)[0]
    branch = branch_name(manifest, batch)
    backend = GitHubGitBackend(
        repository_root=repository,
        repository="example/repository",
        base_branch="main",
        runner_temp=runner_temp,
    )
    backend.publish_batch(manifest, batch, branch)

    _git(repository, "fetch", "origin", branch)
    _git(repository, "switch", "--create", "forged", "FETCH_HEAD")
    _write(repository / "docs-vnext", "page.mdx", "forged")
    _git(repository, "add", "docs-vnext/page.mdx")
    _git(
        repository,
        "commit",
        "-m",
        "forge deterministic branch",
        "-m",
        (
            f"Manifest-SHA256: {manifest.digest}\n"
            f"Manifest-Run-ID: {manifest.run_id}\n"
            f"Batch-ID: {batch.id}"
        ),
    )
    _git(repository, "push", "--force", "origin", f"HEAD:refs/heads/{branch}")
    forged_pr = _pull_request(manifest, batch)
    campaign_branches = backend.discover_campaign_branches([forged_pr])

    with pytest.raises(BatchSyncError, match="does not match the reconstructed batch"):
        validate_campaign_identities(
            manifest,
            [batch],
            backend,
            [forged_pr],
            campaign_branches,
        )


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


def test_new_manifest_recovers_orphan_branch_from_failed_pr_creation(tmp_path):
    original = _write_manifest(
        tmp_path,
        [_operation(1, 1), _operation(2, 1)],
        name="original-orphan.json",
        run_id=200,
    )
    backend = FakeBackend(
        downloaded_manifests={200: original.path},
        fail_create_batch=1,
    )
    original_batches = plan_batches(original, max_files=1, max_payload_bytes=10)

    first_succeeded = execute_batches(
        original,
        original_batches,
        backend,
        [],
        tmp_path / "first-checkpoint.json",
        max_files=1,
        max_payload_bytes=10,
    )

    assert first_succeeded is False
    orphans = backend.discover_campaign_branches([])
    assert [orphan.head_ref for orphan in orphans] == [
        branch_name(original, original_batches[0])
    ]
    current = _write_manifest(
        tmp_path,
        [_operation(2, 1)],
        name="newer-manifest.json",
        run_id=300,
    )

    selected = select_active_manifest(current, backend, orphans)

    assert selected.digest == original.digest
    assert selected.run_id == 200
    backend.fail_create_batch = None
    resumed_succeeded = execute_batches(
        selected,
        plan_batches(selected, max_files=1, max_payload_bytes=10),
        backend,
        [],
        tmp_path / "resumed-checkpoint.json",
        max_files=1,
        max_payload_bytes=10,
    )
    assert resumed_succeeded is True
    assert backend.verified_branches == [1]
    assert backend.created == [1, 2]


@pytest.mark.parametrize(
    ("message", "error"),
    [
        (
            "Subject\n\nManifest-SHA256: "
            + "a" * 64
            + "\nManifest-Run-ID: 1\nManifest-Run-ID: 2",
            "duplicate campaign trailer",
        ),
        (
            "Subject\n\nManifest-SHA256: "
            + "a" * 64
            + "\nUnknown-ID: 1\nBatch-ID: sha256:"
            + "b" * 64,
            "unknown campaign trailer",
        ),
        (
            "Subject\n\nManifest-SHA256: "
            + "a" * 64
            + "\nManifest-Run-ID: 1",
            "exactly 3 trailers",
        ),
        (        "Subject without trailers", "missing a final campaign trailer block"),
        (
        "Subject\n\nManifest-SHA256: "
        + "a" * 64
        + "\nManifest-Run-ID 1\nBatch-ID: sha256:"
        + "b" * 64,
        "malformed campaign trailer",
        ),
    ],
)
def test_commit_identity_rejects_malformed_duplicate_missing_and_unknown_trailers(
    message,
    error,
):
    with pytest.raises(BatchSyncError, match=error):
        parse_commit_identity(message, "automation/docs-vnext-sync/forged")


def test_commit_identity_rejects_oversize_message():
    message = "x" * 4097 + "\n\nManifest-SHA256: " + "a" * 64

    with pytest.raises(BatchSyncError, match="above the 4096-byte discovery limit"):
        parse_commit_identity(message, "automation/docs-vnext-sync/oversize")


def test_backend_bounds_commit_message_output_before_parsing(tmp_path):
    backend = GitHubGitBackend(
        repository_root=tmp_path,
        repository="example/repository",
        base_branch="main",
        runner_temp=tmp_path / "runner",
    )

    with pytest.raises(BatchSyncError, match="stdout exceeds the 4096-byte discovery limit"):
        backend._run_bounded_stdout(
            [sys.executable, "-c", "print('x' * 5000)"],
            max_bytes=4096,
        )

    with pytest.raises(BatchSyncError, match="stderr exceeds the 4096-byte discovery limit"):
        backend._run_bounded_stdout(
            [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('e' * 200000); sys.stderr.flush(); print('ok')",
            ],
            max_bytes=4096,
        )


def test_single_stream_overflow_cannot_race_natural_completion(tmp_path):
    backend = GitHubGitBackend(
        repository_root=tmp_path,
        repository="example/repository",
        base_branch="main",
        runner_temp=tmp_path / "runner",
    )

    for _ in range(20):
        with pytest.raises(BatchSyncError, match="stdout exceeds the 4096-byte discovery limit"):
            backend._run_bounded_stdout(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stderr.close(); sys.stdout.write('x' * 5000)",
                ],
                max_bytes=4096,
                timeout_seconds=1,
            )


def test_backend_bounds_hanging_discovery_command(tmp_path):
    backend = GitHubGitBackend(
        repository_root=tmp_path,
        repository="example/repository",
        base_branch="main",
        runner_temp=tmp_path / "runner",
    )

    started = time.monotonic()
    with pytest.raises(BatchSyncError, match="exceeded the 1-second discovery timeout"):
        backend._run_bounded_stdout(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            max_bytes=4096,
            timeout_seconds=1,
        )
    assert time.monotonic() - started < 1.5


def test_timeout_terminates_child_holding_discovery_pipes(tmp_path):
    backend = GitHubGitBackend(
        repository_root=tmp_path,
        repository="example/repository",
        base_branch="main",
        runner_temp=tmp_path / "runner",
    )
    child_code = (
        "import time\n"
        "while True:\n"
        " print('holding-pipe', flush=True)\n"
        " time.sleep(0.1)\n"
    )
    parent_code = (
        "import subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
        "time.sleep(30)"
    )

    started = time.monotonic()
    with pytest.raises(BatchSyncError, match="exceeded the 1-second discovery timeout"):
        backend._run_bounded_stdout(
            [sys.executable, "-c", parent_code],
            max_bytes=4096,
            timeout_seconds=1,
        )

    assert time.monotonic() - started < 1.5


def test_exited_parent_still_terminates_grandchild_holding_discovery_pipes(tmp_path):
    backend = GitHubGitBackend(
        repository_root=tmp_path,
        repository="example/repository",
        base_branch="main",
        runner_temp=tmp_path / "runner",
    )
    child_code = "import time; time.sleep(5)"
    parent_code = (
        "import subprocess, sys; "
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}])"
    )

    started = time.monotonic()
    output = backend._run_bounded_stdout(
        [sys.executable, "-c", parent_code],
        max_bytes=4096,
        timeout_seconds=1,
    )

    assert output == ""
    assert time.monotonic() - started < 1.5


def test_exited_parent_child_holding_both_streams_uses_one_deadline(tmp_path):
    backend = GitHubGitBackend(
        repository_root=tmp_path,
        repository="example/repository",
        base_branch="main",
        runner_temp=tmp_path / "runner",
    )
    started_file = tmp_path / "two-stream-child-started"
    child_code = (
        "import pathlib, sys, time; "
        "print('stdout-held', flush=True); "
        "print('stderr-held', file=sys.stderr, flush=True); "
        f"pathlib.Path({str(started_file)!r}).write_text('started'); "
        "time.sleep(5)"
    )
    parent_code = (
        "import pathlib, subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
        f"started = pathlib.Path({str(started_file)!r}); "
        "deadline = time.monotonic() + 2; "
        "exec(\"while not started.exists() and time.monotonic() < deadline:\\n time.sleep(0.01)\")"
    )

    started = time.monotonic()
    output = backend._run_bounded_stdout(
        [sys.executable, "-c", parent_code],
        max_bytes=4096,
        timeout_seconds=1,
    )

    assert output.strip() == "stdout-held"
    assert time.monotonic() - started < 1.5


def test_overflow_terminates_grandchild_holding_discovery_pipes(tmp_path):
    backend = GitHubGitBackend(
        repository_root=tmp_path,
        repository="example/repository",
        base_branch="main",
        runner_temp=tmp_path / "runner",
    )
    child_code = "import time; time.sleep(5)"
    parent_code = (
        "import subprocess, sys; "
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
        "sys.stdout.write('x' * 5000); sys.stdout.flush()"
    )

    started = time.monotonic()
    with pytest.raises(BatchSyncError, match="stdout exceeds the 4096-byte discovery limit"):
        backend._run_bounded_stdout(
            [sys.executable, "-c", parent_code],
            max_bytes=4096,
            timeout_seconds=1,
        )

    assert time.monotonic() - started < 1.5


def test_campaign_discovery_routes_ls_remote_fetch_and_show_through_bounded_runner(
    tmp_path,
):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)], run_id=321)
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    branch = branch_name(manifest, batch)

    class RecordingBackend(GitHubGitBackend):
        def __init__(self):
            super().__init__(
                repository_root=tmp_path,
                repository="example/repository",
                base_branch="main",
                runner_temp=tmp_path / "runner",
            )
            self.calls = []

        def _run_bounded_stdout(
            self,
            args,
            *,
            max_bytes,
            cwd=None,
            timeout_seconds=30,
        ):
            self.calls.append((tuple(args), max_bytes, timeout_seconds))
            if args[1] == "ls-remote":
                return f"{'a' * 40}\trefs/heads/{branch}\n"
            if args[1] == "fetch":
                return ""
            return (
                "Sync batch\n\n"
                f"Manifest-SHA256: {manifest.digest}\n"
                f"Manifest-Run-ID: {manifest.run_id}\n"
                f"Batch-ID: {batch.id}\n"
            )

        def download_manifest(self, run_id):
            assert run_id == manifest.run_id
            return manifest.path

    backend = RecordingBackend()

    identities = backend.discover_campaign_branches([])

    assert identities[0].batch_id == batch.id
    assert [(call[0][1], call[1], call[2]) for call in backend.calls] == [
        ("ls-remote", 32 * 1024, 30),
        ("fetch", 4096, 30),
        ("show", 4096, 30),
    ]


def test_deleted_pr_head_with_missing_marker_recovers_via_bounded_pull_ref(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)], run_id=654)
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    pull_request = replace(_pull_request(manifest, batch), marker=None)

    class RecordingBackend(GitHubGitBackend):
        def __init__(self):
            super().__init__(
                repository_root=tmp_path,
                repository="example/repository",
                base_branch="main",
                runner_temp=tmp_path / "runner",
            )
            self.calls = []

        def _run_bounded_stdout(
            self,
            args,
            *,
            max_bytes,
            cwd=None,
            timeout_seconds=30,
        ):
            self.calls.append((tuple(args), max_bytes, timeout_seconds))
            if args[1] in {"ls-remote", "fetch"}:
                return ""
            return (
                "Sync batch\n\n"
                f"Manifest-SHA256: {manifest.digest}\n"
                f"Manifest-Run-ID: {manifest.run_id}\n"
                f"Batch-ID: {batch.id}\n"
            )

        def download_manifest(self, run_id):
            assert run_id == manifest.run_id
            return manifest.path

    backend = RecordingBackend()

    identities = backend.discover_campaign_branches([pull_request])
    selected = select_active_manifest(manifest, backend, identities)

    assert selected.digest == manifest.digest
    assert identities[0].pull_request_number == pull_request.number
    fetch_call = backend.calls[1]
    assert fetch_call[0][1] == "fetch"
    assert f"refs/pull/{pull_request.number}/head" in fetch_call[0][-1]
    assert fetch_call[1:] == (4096, 30)


@pytest.mark.parametrize("run_id", ["+1", "01", "1_0", "1 ", "0", "-1"])
def test_commit_identity_rejects_noncanonical_run_ids(run_id):
    message = (
        "Subject\n\n"
        f"Manifest-SHA256: {'a' * 64}\n"
        f"Manifest-Run-ID: {run_id}\n"
        f"Batch-ID: sha256:{'b' * 64}"
    )

    with pytest.raises(BatchSyncError, match="canonical positive decimal"):
        parse_commit_identity(message, "automation/docs-vnext-sync/noncanonical")


def test_remote_branch_discovery_rejects_excessive_branch_count():
    output = "\n".join(
        f"{'a' * 40}\trefs/heads/automation/docs-vnext-sync/campaign/batch-{index}"
        for index in range(101)
    )

    with pytest.raises(BatchSyncError, match="above the 100-branch discovery limit"):
        parse_remote_branch_refs(output)


def test_remote_branch_discovery_rejects_duplicate_refs():
    line = (
        f"{'a' * 40}\trefs/heads/automation/docs-vnext-sync/campaign/batch-001"
    )

    with pytest.raises(BatchSyncError, match="duplicate references"):
        parse_remote_branch_refs(f"{line}\n{line}\n")


def test_combined_remote_and_deleted_pr_candidates_are_capped_before_fetch():
    remote_heads = {
        f"automation/docs-vnext-sync/campaign/batch-{index:03d}"
        for index in range(100)
    }
    deleted_pr_heads = {"automation/docs-vnext-sync/campaign/deleted-pr-head"}

    with pytest.raises(BatchSyncError, match="101 active automation identity candidates"):
        enforce_campaign_candidate_limit(remote_heads, deleted_pr_heads)


def test_forged_pr_and_orphan_identities_cannot_bind_to_campaign(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)])
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    valid_pr = _pull_request(manifest, batch)
    forged_pr = replace(valid_pr, head_ref=f"{branch_name(manifest, batch)}-forged")
    backend = FakeBackend([forged_pr])
    forged_pr_identity = backend.discover_campaign_branches([forged_pr])

    with pytest.raises(BatchSyncError, match="does not match deterministic branch"):
        validate_campaign_identities(
            manifest,
            [batch],
            backend,
            [forged_pr],
            forged_pr_identity,
        )

    forged_orphan = OrphanBranch(
        head_ref=branch_name(manifest, batch),
        manifest_digest=manifest.digest,
        manifest_run_id=manifest.run_id,
        batch_id=f"sha256:{'f' * 64}",
    )
    with pytest.raises(BatchSyncError, match="does not match an exact planned batch"):
        validate_campaign_identities(manifest, [batch], backend, [], [forged_orphan])


@pytest.mark.parametrize(
    "body",
    [
        None,
        "<!-- docs-vnext-sync-state\n{malformed-json}\n-->",
    ],
)
def test_missing_or_malformed_pr_marker_recovers_from_verified_head(tmp_path, body):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)])
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    valid = _pull_request(manifest, batch)
    pull_request = replace(valid, marker=parse_pull_request_marker(body))
    identity = OrphanBranch(
        head_ref=pull_request.head_ref,
        manifest_digest=manifest.digest,
        manifest_run_id=manifest.run_id,
        batch_id=batch.id,
        pull_request_number=pull_request.number,
    )
    backend = FakeBackend(
        [pull_request],
        downloaded_manifests={manifest.run_id: manifest.path},
        remote_branches={pull_request.head_ref},
        pull_request_identities={pull_request.number: identity},
    )

    campaign_branches = backend.discover_campaign_branches([pull_request])
    selected = select_active_manifest(manifest, backend, campaign_branches)
    preverified = validate_campaign_identities(
        selected,
        [batch],
        backend,
        [pull_request],
        campaign_branches,
    )
    succeeded = execute_batches(
        selected,
        [batch],
        backend,
        [pull_request],
        tmp_path / "recovered-checkpoint.json",
        max_files=1,
        max_payload_bytes=10,
        preverified_batch_ids=preverified,
    )

    assert succeeded is True
    assert backend.downloaded_run_ids == [manifest.run_id]


def test_forged_marker_cannot_pin_manifest_before_head_authentication(tmp_path):
    current = _write_manifest(
        tmp_path,
        [_operation(1, 1)],
        name="current-authenticated.json",
        run_id=300,
    )
    current_batch = plan_batches(current, max_files=1, max_payload_bytes=10)[0]
    old = _write_manifest(
        tmp_path,
        [_operation(2, 1)],
        name="forged-old.json",
        run_id=200,
    )
    old_batch = plan_batches(old, max_files=1, max_payload_bytes=10)[0]
    forged_marker_pr = _pull_request(old, old_batch)
    authenticated_identity = OrphanBranch(
        head_ref=forged_marker_pr.head_ref,
        manifest_digest=current.digest,
        manifest_run_id=current.run_id,
        batch_id=current_batch.id,
        pull_request_number=forged_marker_pr.number,
    )
    backend = FakeBackend(
        [forged_marker_pr],
        downloaded_manifests={200: old.path},
        pull_request_identities={forged_marker_pr.number: authenticated_identity},
    )

    with pytest.raises(BatchSyncError, match="conflicts with its verified head commit"):
        backend.discover_campaign_branches([forged_marker_pr])
    assert backend.downloaded_run_ids == []


def test_pr_and_orphan_cannot_claim_the_same_derived_batch(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)])
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    branch = branch_name(manifest, batch)
    pull_request = _pull_request(manifest, batch)
    orphan = OrphanBranch(
        head_ref=branch,
        manifest_digest=manifest.digest,
        manifest_run_id=manifest.run_id,
        batch_id=batch.id,
    )
    backend = FakeBackend([pull_request], remote_branches={branch})
    pull_request_identity = backend.discover_campaign_branches([pull_request])

    with pytest.raises(BatchSyncError, match="claimed by both"):
        validate_campaign_identities(
            manifest,
            [batch],
            backend,
            [pull_request],
            [*pull_request_identity, orphan],
        )


def test_same_digest_claim_cannot_adopt_nonexistent_run_id(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)], run_id=300)
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    claimed = OrphanBranch(
        head_ref=branch_name(manifest, batch),
        manifest_digest=manifest.digest,
        manifest_run_id=999,
        batch_id=batch.id,
    )
    backend = FakeBackend()

    with pytest.raises(BatchSyncError, match="workflow run 999 is unavailable"):
        select_active_manifest(manifest, backend, [claimed])
    assert backend.downloaded_run_ids == [999]


def test_same_digest_claim_cannot_adopt_unrelated_run_artifact(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        [_operation(1, 1)],
        name="same-digest-current.json",
        run_id=300,
    )
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    unrelated = _write_manifest(
        tmp_path,
        [_operation(2, 1)],
        name="unrelated-run.json",
        run_id=998,
    )
    claimed = OrphanBranch(
        head_ref=branch_name(manifest, batch),
        manifest_digest=manifest.digest,
        manifest_run_id=998,
        batch_id=batch.id,
    )
    backend = FakeBackend(downloaded_manifests={998: unrelated.path})

    with pytest.raises(BatchSyncError, match="has digest.*expected"):
        select_active_manifest(manifest, backend, [claimed])
    assert backend.downloaded_run_ids == [998]


def test_same_digest_claim_adopts_only_verified_run_artifact(tmp_path):
    manifest = _write_manifest(tmp_path, [_operation(1, 1)], run_id=300)
    batch = plan_batches(manifest, max_files=1, max_payload_bytes=10)[0]
    claimed = OrphanBranch(
        head_ref=branch_name(manifest, batch),
        manifest_digest=manifest.digest,
        manifest_run_id=997,
        batch_id=batch.id,
    )
    backend = FakeBackend(downloaded_manifests={997: manifest.path})

    selected = select_active_manifest(manifest, backend, [claimed])

    assert selected.digest == manifest.digest
    assert selected.run_id == 997
    assert backend.downloaded_run_ids == [997]


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

    selected = select_active_manifest(
        current,
        backend,
        backend.discover_campaign_branches([active]),
    )

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
