"""Apply a retained docs-vnext sync manifest in bounded, resumable pull-request batches."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, Sequence

from generate_docs_vnext_sync_manifest import MANIFEST_SCHEMA_VERSION

BATCH_SCHEMA_VERSION = 1
CHECKPOINT_SCHEMA_VERSION = 1
DEFAULT_MAX_FILES = 50
DEFAULT_MAX_PAYLOAD_BYTES = 40 * 1024 * 1024
BRANCH_PREFIX = "automation/docs-vnext-sync"
PR_MARKER_NAME = "docs-vnext-sync-state"
PR_MARKER_PATTERN = re.compile(
    rf"<!-- {re.escape(PR_MARKER_NAME)}\s*\n(?P<payload>\{{.*?\}})\s*\n-->",
    re.DOTALL,
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
OPERATION_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
DECISIONS = {"add", "modify", "remove", "preserve"}
MUTATING_DECISIONS = {"add", "modify", "remove"}


class BatchSyncError(RuntimeError):
    """Raised when a sync batch cannot be planned or applied safely."""


@dataclass(frozen=True, slots=True)
class Operation:
    id: str
    decision: str
    path: str
    file_count: int
    payload_bytes: int
    source: dict[str, int | str] | None
    target: dict[str, int | str] | None


@dataclass(frozen=True, slots=True)
class Manifest:
    path: Path
    run_id: int
    digest: str
    source_root: str
    target_root: str
    operations: tuple[Operation, ...]


@dataclass(frozen=True, slots=True)
class Batch:
    id: str
    number: int
    total: int
    operations: tuple[Operation, ...]

    @property
    def file_count(self) -> int:
        return sum(operation.file_count for operation in self.operations)

    @property
    def payload_bytes(self) -> int:
        return sum(operation.payload_bytes for operation in self.operations)

    @property
    def mutating_operations(self) -> tuple[Operation, ...]:
        return tuple(
            operation for operation in self.operations if operation.decision in MUTATING_DECISIONS
        )


@dataclass(frozen=True, slots=True)
class PullRequest:
    number: int
    state: str
    url: str
    head_ref: str
    marker: dict[str, Any] | None

    @property
    def merged(self) -> bool:
        return self.state == "MERGED"

    @property
    def incomplete(self) -> bool:
        return self.state in {"OPEN", "CLOSED"}


class AutomationBackend(Protocol):
    def list_pull_requests(self) -> list[PullRequest]: ...

    def download_manifest(self, run_id: int) -> Path: ...

    def publish_batch(self, manifest: Manifest, batch: Batch, branch: str) -> None: ...

    def create_pull_request(
        self,
        manifest: Manifest,
        batch: Batch,
        branch: str,
        title: str,
        body: str,
    ) -> PullRequest: ...

    def reopen_pull_request(self, pull_request: PullRequest) -> PullRequest: ...


def _require_int(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise BatchSyncError(f"{label} must be an integer greater than or equal to {minimum}")
    return value


def _validate_relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise BatchSyncError(f"{label} must be a non-empty POSIX relative path")
    if "\\" in value or value.startswith("/") or value.endswith("/"):
        raise BatchSyncError(f"{label} must be a normalized POSIX relative path: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise BatchSyncError(f"{label} must not contain empty, '.' or '..' segments: {value!r}")
    if PurePosixPath(value).as_posix() != value:
        raise BatchSyncError(f"{label} is not normalized: {value!r}")
    return value


def _validate_metadata(value: Any, label: str) -> dict[str, int | str] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"bytes", "sha256"}:
        raise BatchSyncError(f"{label} must contain only bytes and sha256")
    byte_count = _require_int(value["bytes"], f"{label}.bytes")
    sha256 = value["sha256"]
    if not isinstance(sha256, str) or not SHA256_PATTERN.fullmatch(sha256):
        raise BatchSyncError(f"{label}.sha256 must be a lowercase SHA-256 digest")
    return {"bytes": byte_count, "sha256": sha256}


def _parse_operation(value: Any, index: int) -> Operation:
    if not isinstance(value, dict):
        raise BatchSyncError(f"Manifest operation {index} must be an object")
    required = {"id", "decision", "path", "fileCount", "payloadBytes", "source", "target"}
    allowed = required | {"preserveRule"}
    if not required <= set(value) or not set(value) <= allowed:
        raise BatchSyncError(f"Manifest operation {index} has an unsupported field set")

    operation_id = value["id"]
    if not isinstance(operation_id, str) or not OPERATION_ID_PATTERN.fullmatch(operation_id):
        raise BatchSyncError(f"Manifest operation {index}.id must be a schema-v2 operation ID")
    decision = value["decision"]
    if decision not in DECISIONS:
        raise BatchSyncError(f"Manifest operation {index}.decision is unsupported: {decision!r}")
    path = _validate_relative_path(value["path"], f"Manifest operation {index}.path")
    file_count = _require_int(value["fileCount"], f"Manifest operation {index}.fileCount", 1)
    if file_count != 1:
        raise BatchSyncError(f"Manifest operation {index}.fileCount must be 1 for schema v2")
    payload_bytes = _require_int(
        value["payloadBytes"], f"Manifest operation {index}.payloadBytes"
    )
    source = _validate_metadata(value["source"], f"Manifest operation {index}.source")
    target = _validate_metadata(value["target"], f"Manifest operation {index}.target")

    if decision == "add" and (source is None or target is not None):
        raise BatchSyncError(f"Add operation {path!r} must have source metadata only")
    if decision == "modify" and (source is None or target is None):
        raise BatchSyncError(f"Modify operation {path!r} must have source and target metadata")
    if decision == "remove" and (source is not None or target is None):
        raise BatchSyncError(f"Remove operation {path!r} must have target metadata only")
    if decision == "preserve" and "preserveRule" not in value:
        raise BatchSyncError(f"Preserve operation {path!r} must identify its preserve rule")
    expected_payload_bytes = {
        "add": source["bytes"] if source is not None else 0,
        "modify": (
            (source["bytes"] if source is not None else 0)
            + (target["bytes"] if target is not None else 0)
        ),
        "remove": target["bytes"] if target is not None else 0,
        "preserve": 0,
    }[decision]
    if payload_bytes != expected_payload_bytes:
        raise BatchSyncError(
            f"Manifest operation {index}.payloadBytes does not match schema-v2 "
            f"conservative accounting for {path!r}"
        )

    return Operation(
        id=operation_id,
        decision=decision,
        path=path,
        file_count=file_count,
        payload_bytes=payload_bytes,
        source=source,
        target=target,
    )


def load_manifest(path: Path, run_id: int) -> Manifest:
    """Load and validate the portions of the schema-v2 manifest consumed by batching."""
    try:
        manifest_bytes = path.read_bytes()
        payload = json.loads(manifest_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise BatchSyncError(f"Cannot read retained manifest {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise BatchSyncError("Retained manifest must be a JSON object")
    if payload.get("schemaVersion") != MANIFEST_SCHEMA_VERSION:
        raise BatchSyncError(
            f"Retained manifest schemaVersion must be {MANIFEST_SCHEMA_VERSION}"
        )
    if not isinstance(payload.get("source"), dict) or not isinstance(payload.get("target"), dict):
        raise BatchSyncError("Retained manifest must contain source and target objects")
    source_root = _validate_relative_path(payload["source"].get("root"), "Manifest source.root")
    target_root = _validate_relative_path(payload["target"].get("root"), "Manifest target.root")
    raw_operations = payload.get("operations")
    if not isinstance(raw_operations, list):
        raise BatchSyncError("Retained manifest operations must be an array")

    operations = tuple(_parse_operation(item, index) for index, item in enumerate(raw_operations))
    operation_ids = [operation.id for operation in operations]
    operation_paths = [operation.path for operation in operations]
    if len(operation_ids) != len(set(operation_ids)):
        raise BatchSyncError("Retained manifest contains duplicate operation IDs")
    if len(operation_paths) != len(set(operation_paths)):
        raise BatchSyncError("Retained manifest contains duplicate operation paths")

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise BatchSyncError("Retained manifest summary must be an object")
    if summary.get("operationCount") != len(operations):
        raise BatchSyncError("Retained manifest summary.operationCount does not match operations")
    if summary.get("payloadBytes") != sum(operation.payload_bytes for operation in operations):
        raise BatchSyncError("Retained manifest summary.payloadBytes does not match operations")

    return Manifest(
        path=path,
        run_id=run_id,
        digest=hashlib.sha256(manifest_bytes).hexdigest(),
        source_root=source_root,
        target_root=target_root,
        operations=operations,
    )


def _batch_id(manifest_digest: str, number: int, operations: Sequence[Operation]) -> str:
    value = "\0".join(
        [
            f"docs-vnext-sync-batch-v{BATCH_SCHEMA_VERSION}",
            manifest_digest,
            str(number),
            *(operation.id for operation in operations),
        ]
    )
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def plan_batches(
    manifest: Manifest,
    max_files: int,
    max_payload_bytes: int,
) -> tuple[Batch, ...]:
    """Greedily partition every operation in manifest order under inclusive ceilings."""
    if max_files <= 0:
        raise BatchSyncError("max_files must be greater than zero")
    if max_payload_bytes <= 0:
        raise BatchSyncError("max_payload_bytes must be greater than zero")

    partitions: list[tuple[Operation, ...]] = []
    current: list[Operation] = []
    current_files = 0
    current_payload = 0
    for operation in manifest.operations:
        if operation.file_count > max_files:
            raise BatchSyncError(
                f"Operation {operation.path!r} requires {operation.file_count} files, "
                f"above the {max_files}-file ceiling"
            )
        if operation.payload_bytes > max_payload_bytes:
            raise BatchSyncError(
                f"Operation {operation.path!r} requires {operation.payload_bytes} payload bytes, "
                f"above the {max_payload_bytes}-byte ceiling"
            )
        exceeds_batch = current and (
            current_files + operation.file_count > max_files
            or current_payload + operation.payload_bytes > max_payload_bytes
        )
        if exceeds_batch:
            partitions.append(tuple(current))
            current = []
            current_files = 0
            current_payload = 0
        current.append(operation)
        current_files += operation.file_count
        current_payload += operation.payload_bytes
    if current:
        partitions.append(tuple(current))

    total = len(partitions)
    batches = tuple(
        Batch(
            id=_batch_id(manifest.digest, number, operations),
            number=number,
            total=total,
            operations=operations,
        )
        for number, operations in enumerate(partitions, start=1)
    )
    planned_ids = [operation.id for batch in batches for operation in batch.operations]
    if planned_ids != [operation.id for operation in manifest.operations]:
        raise BatchSyncError("Batch planning did not preserve the complete manifest operation order")
    return batches


def branch_name(manifest: Manifest, batch: Batch) -> str:
    return (
        f"{BRANCH_PREFIX}/{manifest.digest[:16]}/"
        f"batch-{batch.number:03d}-{batch.id.removeprefix('sha256:')[:12]}"
    )


def _marker_payload(manifest: Manifest, batch: Batch) -> dict[str, Any]:
    return {
        "schemaVersion": BATCH_SCHEMA_VERSION,
        "manifestSha256": manifest.digest,
        "manifestRunId": manifest.run_id,
        "batchId": batch.id,
        "batchNumber": batch.number,
        "batchCount": batch.total,
        "operationIds": [operation.id for operation in batch.operations],
    }


def build_pull_request_body(manifest: Manifest, batch: Batch) -> str:
    marker = json.dumps(_marker_payload(manifest, batch), sort_keys=True, separators=(",", ":"))
    operations = "\n".join(
        f"- `{operation.decision}` `{operation.path}`" for operation in batch.operations
    )
    return (
        f"<!-- {PR_MARKER_NAME}\n{marker}\n-->\n\n"
        "## Docs-vnext bounded baseline sync\n\n"
        f"- Manifest SHA-256: `{manifest.digest}`\n"
        f"- Manifest workflow run: `{manifest.run_id}`\n"
        f"- Batch: `{batch.number}/{batch.total}`\n"
        f"- Files: `{batch.file_count}` (ceiling enforced before mutation)\n"
        f"- Conservative payload: `{batch.payload_bytes}` bytes\n\n"
        "### Manifest operations\n\n"
        f"{operations}\n\n"
        "The branch was produced by deterministic host automation from the retained schema-v2 "
        "manifest. No model-authored corpus patch was used.\n\n"
        "Related to #635.\n"
    )


def parse_pull_request_marker(body: str | None) -> dict[str, Any] | None:
    if not body:
        return None
    match = PR_MARKER_PATTERN.search(body)
    if match is None:
        return None
    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError:
        return None
    required = {
        "schemaVersion",
        "manifestSha256",
        "manifestRunId",
        "batchId",
        "batchNumber",
        "batchCount",
        "operationIds",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        return None
    if payload["schemaVersion"] != BATCH_SCHEMA_VERSION:
        return None
    if not isinstance(payload["manifestSha256"], str) or not SHA256_PATTERN.fullmatch(
        payload["manifestSha256"]
    ):
        return None
    if not isinstance(payload["batchId"], str) or not OPERATION_ID_PATTERN.fullmatch(
        payload["batchId"]
    ):
        return None
    if type(payload["manifestRunId"]) is not int or payload["manifestRunId"] <= 0:
        return None
    if type(payload["batchNumber"]) is not int or payload["batchNumber"] <= 0:
        return None
    if type(payload["batchCount"]) is not int or payload["batchCount"] <= 0:
        return None
    operation_ids = payload["operationIds"]
    if not isinstance(operation_ids, list) or not all(
        isinstance(item, str) and OPERATION_ID_PATTERN.fullmatch(item) for item in operation_ids
    ):
        return None
    return payload


def select_active_manifest(
    current_manifest: Manifest,
    backend: AutomationBackend,
    pull_requests: Sequence[PullRequest],
) -> Manifest:
    """Resume the single unfinished campaign, downloading its original retained artifact."""
    active_markers = [
        pull_request.marker
        for pull_request in pull_requests
        if pull_request.incomplete and pull_request.marker is not None
    ]
    if not active_markers:
        return current_manifest

    digests = {marker["manifestSha256"] for marker in active_markers}
    if len(digests) != 1:
        raise BatchSyncError(
            "Multiple unfinished docs-vnext sync campaigns exist; close or merge one campaign "
            f"before retrying: {sorted(digests)}"
        )
    run_ids = {marker["manifestRunId"] for marker in active_markers}
    if len(run_ids) != 1:
        raise BatchSyncError(
            "Unfinished campaign pull requests disagree on the retained manifest workflow run"
        )

    digest = next(iter(digests))
    run_id = next(iter(run_ids))
    if digest == current_manifest.digest:
        return replace(current_manifest, run_id=run_id)

    resumed = load_manifest(backend.download_manifest(run_id), run_id)
    if resumed.digest != digest:
        raise BatchSyncError(
            f"Retained manifest from run {run_id} has digest {resumed.digest}, expected {digest}"
        )
    return resumed


def _metadata(path: Path) -> dict[str, int | str] | None:
    if path.is_symlink():
        raise BatchSyncError(f"Synchronization path must not be a symbolic link: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise BatchSyncError(f"Synchronization path must be a regular file: {path}")
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            byte_count += len(block)
    return {"bytes": byte_count, "sha256": digest.hexdigest()}


def _path_under(root: Path, relative_path: str) -> Path:
    candidate = root / Path(*PurePosixPath(relative_path).parts)
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise BatchSyncError(f"Synchronization path escapes its root: {relative_path!r}") from exc
    cursor = root
    for part in PurePosixPath(relative_path).parts:
        cursor /= part
        if cursor.is_symlink():
            raise BatchSyncError(f"Synchronization path contains a symbolic link: {cursor}")
    return candidate


def _verify_metadata(path: Path, expected: dict[str, int | str] | None, label: str) -> None:
    actual = _metadata(path)
    if actual != expected:
        raise BatchSyncError(f"{label} metadata changed since manifest generation: {path}")


def apply_batch(repository_root: Path, manifest: Manifest, batch: Batch) -> tuple[str, ...]:
    """Verify all preconditions, then apply only the mutating operations in one batch."""
    source_root = _path_under(repository_root, manifest.source_root)
    target_root = _path_under(repository_root, manifest.target_root)
    if not source_root.is_dir() or not target_root.is_dir():
        raise BatchSyncError("Manifest source and target roots must exist in the batch worktree")

    resolved: list[tuple[Operation, Path, Path]] = []
    for operation in batch.operations:
        source_path = _path_under(source_root, operation.path)
        target_path = _path_under(target_root, operation.path)
        _verify_metadata(source_path, operation.source, f"Source for {operation.id}")
        _verify_metadata(target_path, operation.target, f"Target for {operation.id}")
        resolved.append((operation, source_path, target_path))

    changed_paths: list[str] = []
    for operation, source_path, target_path in resolved:
        if operation.decision in {"add", "modify"}:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)
            changed_paths.append(f"{manifest.target_root}/{operation.path}")
        elif operation.decision == "remove":
            target_path.unlink()
            changed_paths.append(f"{manifest.target_root}/{operation.path}")

    for operation, source_path, target_path in resolved:
        if operation.decision in {"add", "modify"}:
            _verify_metadata(target_path, _metadata(source_path), f"Applied target for {operation.id}")
        elif operation.decision == "remove":
            _verify_metadata(target_path, None, f"Applied target for {operation.id}")
    return tuple(changed_paths)


def _initial_checkpoint(
    manifest: Manifest,
    batches: Sequence[Batch],
    max_files: int,
    max_payload_bytes: int,
) -> dict[str, Any]:
    return {
        "schemaVersion": CHECKPOINT_SCHEMA_VERSION,
        "status": "pending",
        "manifest": {"sha256": manifest.digest, "runId": manifest.run_id},
        "limits": {"maxFiles": max_files, "maxPayloadBytes": max_payload_bytes},
        "summary": {"completed": 0, "failed": 0, "pending": len(batches)},
        "batches": [
            {
                "id": batch.id,
                "number": batch.number,
                "operationCount": len(batch.operations),
                "fileCount": batch.file_count,
                "payloadBytes": batch.payload_bytes,
                "branch": branch_name(manifest, batch),
                "state": "pending",
                "result": None,
                "diagnostic": None,
                "pullRequest": None,
            }
            for batch in batches
        ],
    }


def _write_checkpoint(path: Path, checkpoint: dict[str, Any]) -> None:
    states = [batch["state"] for batch in checkpoint["batches"]]
    checkpoint["summary"] = {
        "completed": states.count("completed"),
        "failed": states.count("failed"),
        "pending": states.count("pending"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _matching_marker(manifest: Manifest, batch: Batch, marker: dict[str, Any] | None) -> bool:
    return marker == _marker_payload(manifest, batch)


def execute_batches(
    manifest: Manifest,
    batches: Sequence[Batch],
    backend: AutomationBackend,
    pull_requests: list[PullRequest],
    checkpoint_path: Path,
    max_files: int,
    max_payload_bytes: int,
) -> bool:
    """Resume or publish batches sequentially and stop after the first partial failure."""
    checkpoint = _initial_checkpoint(manifest, batches, max_files, max_payload_bytes)
    _write_checkpoint(checkpoint_path, checkpoint)

    failed = False
    for batch, batch_state in zip(batches, checkpoint["batches"], strict=True):
        branch = branch_name(manifest, batch)
        try:
            if not batch.mutating_operations:
                batch_state["state"] = "completed"
                batch_state["result"] = "preserve-only"
                _write_checkpoint(checkpoint_path, checkpoint)
                continue

            branch_pull_requests = [
                pull_request
                for pull_request in pull_requests
                if pull_request.head_ref == branch
            ]
            if len(branch_pull_requests) > 1:
                raise BatchSyncError(f"Multiple pull requests use deterministic branch {branch!r}")
            if branch_pull_requests:
                pull_request = branch_pull_requests[0]
                if not _matching_marker(manifest, batch, pull_request.marker):
                    raise BatchSyncError(
                        f"Pull request #{pull_request.number} uses {branch!r} with mismatched metadata"
                    )
                if pull_request.state == "CLOSED":
                    pull_request = backend.reopen_pull_request(pull_request)
                    result = "reopened-pull-request"
                elif pull_request.merged:
                    result = "existing-merged-pull-request"
                else:
                    result = "existing-open-pull-request"
            else:
                backend.publish_batch(manifest, batch, branch)
                title = (
                    f"[docs-vnext-sync] Baseline {manifest.digest[:12]} "
                    f"batch {batch.number}/{batch.total}"
                )
                pull_request = backend.create_pull_request(
                    manifest,
                    batch,
                    branch,
                    title,
                    build_pull_request_body(manifest, batch),
                )
                pull_requests.append(pull_request)
                result = "created-pull-request"

            batch_state["state"] = "completed"
            batch_state["result"] = result
            batch_state["pullRequest"] = {
                "number": pull_request.number,
                "state": pull_request.state,
                "url": pull_request.url,
            }
        except Exception as exc:  # noqa: BLE001 - checkpoint must retain the exact batch failure
            batch_state["state"] = "failed"
            batch_state["diagnostic"] = f"{type(exc).__name__}: {exc}"
            failed = True
        _write_checkpoint(checkpoint_path, checkpoint)
        if failed:
            break

    checkpoint["status"] = "failed" if failed else "completed"
    _write_checkpoint(checkpoint_path, checkpoint)
    return not failed


def _write_summary(path: Path | None, checkpoint_path: Path) -> None:
    if path is None or not checkpoint_path.is_file():
        return
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    summary = checkpoint["summary"]
    lines = [
        "## Docs-vnext bounded baseline sync",
        "",
        f"- Status: **{checkpoint['status']}**",
        f"- Manifest: `{checkpoint['manifest']['sha256']}`",
        f"- Manifest run: `{checkpoint['manifest']['runId']}`",
        f"- Completed batches: `{summary['completed']}`",
        f"- Failed batches: `{summary['failed']}`",
        f"- Pending batches: `{summary['pending']}`",
    ]
    failed_batches = [batch for batch in checkpoint["batches"] if batch["state"] == "failed"]
    if failed_batches:
        lines.extend(["", "### Failure", ""])
        lines.extend(
            f"- Batch {batch['number']} (`{batch['id']}`): {batch['diagnostic']}"
            for batch in failed_batches
        )
    elif checkpoint.get("diagnostics"):
        lines.extend(["", "### Failure", ""])
        lines.extend(f"- {diagnostic}" for diagnostic in checkpoint["diagnostics"])
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


class GitHubGitBackend:
    """GitHub CLI and git implementation used only by the traditional host workflow."""

    def __init__(
        self,
        repository_root: Path,
        repository: str,
        base_branch: str,
        runner_temp: Path,
    ) -> None:
        self.repository_root = repository_root
        self.repository = repository
        self.base_branch = base_branch
        self.runner_temp = runner_temp
        self.runner_temp.mkdir(parents=True, exist_ok=True)

    def _run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            list(args),
            cwd=cwd or self.repository_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if check and result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            raise BatchSyncError(f"{args[0]} {args[1] if len(args) > 1 else ''} failed: {detail}")
        return result

    def _pull_request_from_api(self, payload: dict[str, Any]) -> PullRequest:
        merged = payload.get("merged_at") is not None
        state = "MERGED" if merged else str(payload["state"]).upper()
        return PullRequest(
            number=int(payload["number"]),
            state=state,
            url=str(payload["html_url"]),
            head_ref=str(payload["head"]["ref"]),
            marker=parse_pull_request_marker(payload.get("body")),
        )

    def list_pull_requests(self) -> list[PullRequest]:
        result = self._run(
            [
                "gh",
                "api",
                "--method",
                "GET",
                "--paginate",
                "--slurp",
                f"repos/{self.repository}/pulls",
                "-f",
                "state=all",
                "-f",
                "per_page=100",
            ]
        )
        pages = json.loads(result.stdout)
        pull_requests = []
        for page in pages:
            for payload in page:
                head_repository = payload.get("head", {}).get("repo") or {}
                if head_repository.get("full_name") == self.repository:
                    pull_requests.append(self._pull_request_from_api(payload))
        return pull_requests

    def download_manifest(self, run_id: int) -> Path:
        destination = self.runner_temp / f"resume-manifest-{run_id}"
        destination.mkdir(parents=True, exist_ok=True)
        self._run(
            [
                "gh",
                "run",
                "download",
                str(run_id),
                "--repo",
                self.repository,
                "--name",
                f"docs-vnext-sync-manifest-{run_id}",
                "--dir",
                str(destination),
            ]
        )
        matches = list(destination.rglob("docs-vnext-sync-manifest.json"))
        if len(matches) != 1:
            raise BatchSyncError(
                f"Manifest artifact for workflow run {run_id} contained {len(matches)} manifest files"
            )
        return matches[0]

    def _remote_branch_exists(self, branch: str) -> bool:
        result = self._run(
            ["git", "ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{branch}"],
            check=False,
        )
        if result.returncode == 0:
            return True
        if result.returncode == 2:
            return False
        detail = result.stderr.strip() or result.stdout.strip()
        raise BatchSyncError(f"Cannot inspect remote branch {branch!r}: {detail}")

    def _changed_names(self, cwd: Path, revision_range: str) -> set[str]:
        result = self._run(
            ["git", "diff", "--name-only", revision_range],
            cwd=cwd,
        )
        return {line for line in result.stdout.splitlines() if line}

    def publish_batch(self, manifest: Manifest, batch: Batch, branch: str) -> None:
        self._run(["git", "fetch", "--no-tags", "origin", self.base_branch])
        base_ref = f"refs/remotes/origin/{self.base_branch}"
        remote_exists = self._remote_branch_exists(branch)
        remote_ref = f"refs/remotes/origin/{branch}"
        if remote_exists:
            self._run(
                [
                    "git",
                    "fetch",
                    "--no-tags",
                    "origin",
                    f"refs/heads/{branch}:{remote_ref}",
                ]
            )

        worktree = Path(tempfile.mkdtemp(prefix="docs-vnext-sync-", dir=self.runner_temp))
        worktree.rmdir()
        self._run(["git", "worktree", "add", "--detach", str(worktree), base_ref])
        try:
            changed_paths = apply_batch(worktree, manifest, batch)
            expected_names = set(changed_paths)
            if not expected_names:
                raise BatchSyncError(f"Batch {batch.number} has no mutating paths to publish")
            self._run(["git", "add", "--", *sorted(expected_names)], cwd=worktree)
            staged_names = self._changed_names(worktree, "--cached")
            if staged_names != expected_names:
                raise BatchSyncError(
                    f"Staged batch paths {sorted(staged_names)} do not match {sorted(expected_names)}"
                )

            if remote_exists:
                branch_names = self._changed_names(worktree, f"{base_ref}...{remote_ref}")
                if branch_names != expected_names:
                    raise BatchSyncError(
                        f"Existing branch {branch!r} changes {sorted(branch_names)}, "
                        f"expected {sorted(expected_names)}"
                    )
                comparison = self._run(
                    [
                        "git",
                        "diff",
                        "--cached",
                        "--quiet",
                        remote_ref,
                        "--",
                        *sorted(expected_names),
                    ],
                    cwd=worktree,
                    check=False,
                )
                if comparison.returncode != 0:
                    raise BatchSyncError(
                        f"Existing branch {branch!r} does not match the reconstructed batch"
                    )
                return

            self._run(["git", "switch", "--create", branch], cwd=worktree)
            self._run(["git", "config", "user.name", "github-actions[bot]"], cwd=worktree)
            self._run(
                [
                    "git",
                    "config",
                    "user.email",
                    "41898282+github-actions[bot]@users.noreply.github.com",
                ],
                cwd=worktree,
            )
            self._run(
                [
                    "git",
                    "commit",
                    "-m",
                    (
                        f"Sync docs-vnext baseline batch {batch.number}/{batch.total}\n\n"
                        f"Manifest-SHA256: {manifest.digest}\n"
                        f"Batch-ID: {batch.id}"
                    ),
                ],
                cwd=worktree,
            )
            self._run(
                ["git", "push", "origin", f"HEAD:refs/heads/{branch}"],
                cwd=worktree,
            )
        finally:
            self._run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                check=False,
            )

    def _get_pull_request(self, number: int) -> PullRequest:
        result = self._run(
            ["gh", "api", f"repos/{self.repository}/pulls/{number}"],
        )
        return self._pull_request_from_api(json.loads(result.stdout))

    def create_pull_request(
        self,
        manifest: Manifest,
        batch: Batch,
        branch: str,
        title: str,
        body: str,
    ) -> PullRequest:
        body_file = self.runner_temp / f"batch-{batch.number:03d}-pr.md"
        body_file.write_text(body, encoding="utf-8", newline="\n")
        result = self._run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                self.repository,
                "--base",
                self.base_branch,
                "--head",
                branch,
                "--title",
                title,
                "--body-file",
                str(body_file),
                "--label",
                "documentation",
                "--label",
                "automation",
                "--label",
                "docs-vnext",
                "--label",
                "upstream-sync",
            ]
        )
        match = re.search(r"/pull/(?P<number>\d+)", result.stdout)
        if match is None:
            raise BatchSyncError(f"Cannot identify created pull request from: {result.stdout!r}")
        return self._get_pull_request(int(match.group("number")))

    def reopen_pull_request(self, pull_request: PullRequest) -> PullRequest:
        self._run(
            [
                "gh",
                "pr",
                "reopen",
                str(pull_request.number),
                "--repo",
                self.repository,
            ]
        )
        return self._get_pull_request(pull_request.number)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-run-id", type=int, required=True)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--base-branch", default="main")
    parser.add_argument(
        "--runner-temp",
        type=Path,
        default=Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())),
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-payload-bytes", type=int, default=DEFAULT_MAX_PAYLOAD_BYTES)
    return parser.parse_args(argv)


def _write_fatal_checkpoint(
    path: Path,
    manifest: Manifest | None,
    max_files: int,
    max_payload_bytes: int,
    diagnostic: str,
) -> None:
    checkpoint = {
        "schemaVersion": CHECKPOINT_SCHEMA_VERSION,
        "status": "failed",
        "manifest": {
            "sha256": manifest.digest if manifest is not None else None,
            "runId": manifest.run_id if manifest is not None else None,
        },
        "limits": {"maxFiles": max_files, "maxPayloadBytes": max_payload_bytes},
        "summary": {"completed": 0, "failed": 0, "pending": 0},
        "diagnostics": [diagnostic],
        "batches": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    backend: AutomationBackend | None = None,
) -> int:
    args = _parse_args(argv)
    current_manifest: Manifest | None = None
    try:
        if not args.repository:
            raise BatchSyncError("--repository or GITHUB_REPOSITORY is required")
        if args.manifest_run_id <= 0:
            raise BatchSyncError("--manifest-run-id must be greater than zero")
        current_manifest = load_manifest(args.manifest, args.manifest_run_id)
        active_backend = backend or GitHubGitBackend(
            repository_root=args.repository_root.resolve(),
            repository=args.repository,
            base_branch=args.base_branch,
            runner_temp=args.runner_temp,
        )
        pull_requests = active_backend.list_pull_requests()
        manifest = select_active_manifest(current_manifest, active_backend, pull_requests)
        batches = plan_batches(manifest, args.max_files, args.max_payload_bytes)
        succeeded = execute_batches(
            manifest,
            batches,
            active_backend,
            pull_requests,
            args.checkpoint,
            args.max_files,
            args.max_payload_bytes,
        )
        _write_summary(args.summary, args.checkpoint)
        if not succeeded:
            print(
                f"docs-vnext batch sync failed; inspect checkpoint {args.checkpoint}",
                file=sys.stderr,
            )
            return 1
    except (BatchSyncError, OSError, subprocess.SubprocessError) as exc:
        diagnostic = f"{type(exc).__name__}: {exc}"
        _write_fatal_checkpoint(
            args.checkpoint,
            current_manifest,
            args.max_files,
            args.max_payload_bytes,
            diagnostic,
        )
        _write_summary(args.summary, args.checkpoint)
        print(f"docs-vnext batch sync error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
