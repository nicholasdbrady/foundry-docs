"""Apply a retained docs-vnext sync manifest in bounded, resumable pull-request batches."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, Sequence

from generate_docs_vnext_sync_manifest import MANIFEST_SCHEMA_VERSION

BATCH_SCHEMA_VERSION = 1
CHECKPOINT_SCHEMA_VERSION = 1
DEFAULT_MAX_FILES = 50
DEFAULT_MAX_PAYLOAD_BYTES = 40 * 1024 * 1024
MAX_AUTOMATION_BRANCHES = 100
MAX_COMPLETED_BRANCH_DELETIONS = 500
MAX_COMMIT_MESSAGE_BYTES = 4096
MAX_REMOTE_DISCOVERY_BYTES = 32 * 1024
DISCOVERY_COMMAND_TIMEOUT_SECONDS = 30
DISCOVERY_TERMINATION_GRACE_SECONDS = 0.1
WINDOWS_CREATE_SUSPENDED = 0x00000004
BRANCH_PREFIX = "automation/docs-vnext-sync"
PR_MARKER_NAME = "docs-vnext-sync-state"
PR_MARKER_PATTERN = re.compile(
    rf"<!-- {re.escape(PR_MARKER_NAME)}\s*\n(?P<payload>\{{.*?\}})\s*\n-->",
    re.DOTALL,
)
COMMIT_IDENTITY_FIELDS = {
    "Manifest-SHA256": "manifest_digest",
    "Manifest-Run-ID": "manifest_run_id",
    "Batch-ID": "batch_id",
}
TRAILER_PATTERN = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9-]*): (?P<value>\S.*)$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
OPERATION_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
POSITIVE_DECIMAL_PATTERN = re.compile(r"^[1-9][0-9]*$")
AUTOMATION_BRANCH_PATTERN = re.compile(
    rf"^{re.escape(BRANCH_PREFIX)}/"
    r"(?P<manifest>[0-9a-f]{16})/"
    r"batch-(?P<number>[0-9]{3})-(?P<batch>[0-9a-f]{12})$"
)
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


@dataclass(frozen=True, slots=True)
class OrphanBranch:
    head_ref: str
    manifest_digest: str
    manifest_run_id: int
    batch_id: str
    pull_request_number: int | None = None
    commit_sha: str = "0000000000000000000000000000000000000000"


class AutomationBackend(Protocol):
    def list_pull_requests(self) -> list[PullRequest]: ...

    def discover_campaign_branches(
        self, pull_requests: Sequence[PullRequest]
    ) -> list[OrphanBranch]: ...

    def download_manifest(self, run_id: int) -> Path: ...

    def publish_batch(
        self,
        manifest: Manifest,
        batch: Batch,
        branch: str,
        expected_commit_sha: str | None = None,
    ) -> None: ...

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


def _strict_path_prefix(parent: str, child: str) -> bool:
    return child.startswith(f"{parent}/")


def _minimal_pathspecs(paths: set[str]) -> tuple[str, ...]:
    selected: list[str] = []
    for path in sorted(paths, key=lambda item: (len(PurePosixPath(item).parts), item)):
        if not any(path == parent or _strict_path_prefix(parent, path) for parent in selected):
            selected.append(path)
    return tuple(selected)


def _atomic_operation_groups(operations: Sequence[Operation]) -> tuple[tuple[Operation, ...], ...]:
    parent = list(range(len(operations)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left_index, left in enumerate(operations):
        for right_index in range(left_index + 1, len(operations)):
            right = operations[right_index]
            if _strict_path_prefix(left.path, right.path) or _strict_path_prefix(
                right.path, left.path
            ):
                union(left_index, right_index)

    grouped_indices: dict[int, list[int]] = {}
    for index in range(len(operations)):
        grouped_indices.setdefault(find(index), []).append(index)

    dependency_intervals: list[tuple[int, int]] = []
    for indices in grouped_indices.values():
        group = tuple(operations[index] for index in sorted(indices))
        if len(group) > 1:
            decisions = {operation.decision for operation in group}
            paths = [operation.path for operation in group]
            if "preserve" in decisions:
                raise BatchSyncError(
                    "Path dependency collides with a preserved operation and cannot be applied "
                    f"safely: {paths}"
                )
            if not {"add", "remove"} <= decisions or not decisions <= {"add", "remove"}:
                raise BatchSyncError(
                    "Path dependency must be a file/directory remove-and-create replacement: "
                    f"{paths}"
                )
            dependency_intervals.append((min(indices), max(indices)))

    merged_intervals: list[tuple[int, int]] = []
    for start, end in sorted(dependency_intervals):
        if merged_intervals and start <= merged_intervals[-1][1]:
            prior_start, prior_end = merged_intervals[-1]
            merged_intervals[-1] = (prior_start, max(prior_end, end))
        else:
            merged_intervals.append((start, end))

    groups: list[tuple[Operation, ...]] = []
    interval_by_start = {start: end for start, end in merged_intervals}
    index = 0
    while index < len(operations):
        end = interval_by_start.get(index)
        if end is None:
            groups.append((operations[index],))
            index += 1
        else:
            groups.append(tuple(operations[index : end + 1]))
            index = end + 1
    return tuple(groups)


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

    atomic_groups = _atomic_operation_groups(manifest.operations)
    partitions: list[tuple[Operation, ...]] = []
    current: list[Operation] = []
    current_files = 0
    current_payload = 0
    for group in atomic_groups:
        group_files = sum(operation.file_count for operation in group)
        group_payload = sum(operation.payload_bytes for operation in group)
        if group_files > max_files or group_payload > max_payload_bytes:
            paths = [operation.path for operation in group]
            if len(group) > 1:
                raise BatchSyncError(
                    f"Atomic path dependency {paths} requires {group_files} files and "
                    f"{group_payload} payload bytes, exceeding ceilings of {max_files} files "
                    f"and {max_payload_bytes} bytes"
                )
            operation = group[0]
            if operation.file_count > max_files:
                raise BatchSyncError(
                    f"Operation {operation.path!r} requires {operation.file_count} files, "
                    f"above the {max_files}-file ceiling"
                )
            raise BatchSyncError(
                f"Operation {operation.path!r} requires {operation.payload_bytes} payload bytes, "
                f"above the {max_payload_bytes}-byte ceiling"
            )
        exceeds_batch = current and (
            current_files + group_files > max_files
            or current_payload + group_payload > max_payload_bytes
        )
        if exceeds_batch:
            partitions.append(tuple(current))
            current = []
            current_files = 0
            current_payload = 0
        current.extend(group)
        current_files += group_files
        current_payload += group_payload
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
    manifest_ids = [operation.id for operation in manifest.operations]
    if len(planned_ids) != len(set(planned_ids)) or set(planned_ids) != set(manifest_ids):
        raise BatchSyncError("Batch planning did not assign every manifest operation exactly once")
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


def parse_commit_identity(message: str, head_ref: str) -> OrphanBranch:
    message_bytes = len(message.encode("utf-8"))
    if message_bytes > MAX_COMMIT_MESSAGE_BYTES:
        raise BatchSyncError(
            f"Automation branch {head_ref!r} commit message is {message_bytes} bytes, "
            f"above the {MAX_COMMIT_MESSAGE_BYTES}-byte discovery limit"
        )
    lines = message.rstrip("\n").splitlines()
    separator_indices = [index for index, line in enumerate(lines) if not line]
    if not separator_indices:
        raise BatchSyncError(
            f"Automation branch {head_ref!r} is missing a final campaign trailer block"
        )
    trailer_lines = lines[separator_indices[-1] + 1 :]
    if len(trailer_lines) != len(COMMIT_IDENTITY_FIELDS):
        raise BatchSyncError(
            f"Automation branch {head_ref!r} campaign trailer block must contain exactly "
            f"{len(COMMIT_IDENTITY_FIELDS)} trailers"
        )

    values: dict[str, str] = {}
    seen_keys: set[str] = set()
    for line in trailer_lines:
        match = TRAILER_PATTERN.fullmatch(line)
        if match is None:
            raise BatchSyncError(
                f"Automation branch {head_ref!r} has a malformed campaign trailer: {line!r}"
            )
        key = match.group("key")
        if key not in COMMIT_IDENTITY_FIELDS:
            raise BatchSyncError(
                f"Automation branch {head_ref!r} has an unknown campaign trailer {key!r}"
            )
        if key in seen_keys:
            raise BatchSyncError(
                f"Automation branch {head_ref!r} has duplicate campaign trailer {key!r}"
            )
        seen_keys.add(key)
        values[COMMIT_IDENTITY_FIELDS[key]] = match.group("value")
    if set(values) != set(COMMIT_IDENTITY_FIELDS.values()):
        raise BatchSyncError(
            f"Automation branch {head_ref!r} is missing required campaign identity trailers"
        )
    manifest_digest = values["manifest_digest"]
    batch_id = values["batch_id"]
    manifest_run_id_text = values["manifest_run_id"]
    if not POSITIVE_DECIMAL_PATTERN.fullmatch(manifest_run_id_text):
        raise BatchSyncError(
            f"Automation branch {head_ref!r} manifest run ID must be a canonical positive decimal"
        )
    manifest_run_id = int(manifest_run_id_text)
    if not SHA256_PATTERN.fullmatch(manifest_digest):
        raise BatchSyncError(
            f"Orphan automation branch {head_ref!r} has an invalid manifest digest"
        )
    if not OPERATION_ID_PATTERN.fullmatch(batch_id):
        raise BatchSyncError(f"Orphan automation branch {head_ref!r} has an invalid batch ID")
    return OrphanBranch(
        head_ref=head_ref,
        manifest_digest=manifest_digest,
        manifest_run_id=manifest_run_id,
        batch_id=batch_id,
    )


def parse_remote_branch_refs(output: str) -> dict[str, str]:
    lines = [line for line in output.splitlines() if line]
    head_refs: dict[str, str] = {}
    for line in lines:
        commit_sha, separator, ref = line.partition("\t")
        expected_prefix = f"refs/heads/{BRANCH_PREFIX}/"
        if (
            not separator
            or not GIT_COMMIT_PATTERN.fullmatch(commit_sha)
            or not ref.startswith(expected_prefix)
        ):
            raise BatchSyncError(f"Cannot parse automation branch reference: {line!r}")
        head_ref = ref.removeprefix("refs/heads/")
        if head_ref in head_refs:
            raise BatchSyncError("Remote automation branch discovery returned duplicate references")
        head_refs[head_ref] = commit_sha
    return head_refs


def enforce_campaign_candidate_limit(
    remote_heads: set[str],
    incomplete_pull_request_heads: set[str],
) -> None:
    candidate_count = len(remote_heads | incomplete_pull_request_heads)
    if candidate_count > MAX_AUTOMATION_BRANCHES:
        raise BatchSyncError(
            f"Found {candidate_count} active automation identity candidates, above the "
            f"{MAX_AUTOMATION_BRANCHES}-branch discovery limit"
        )


def exclude_completed_remote_heads(
    remote_head_commits: dict[str, str],
    pull_requests: Sequence[PullRequest],
) -> dict[str, str]:
    completed_heads = {
        pull_request.head_ref
        for pull_request in pull_requests
        if pull_request.merged
    }
    return {
        head_ref: commit_sha
        for head_ref, commit_sha in remote_head_commits.items()
        if head_ref not in completed_heads
    }


def completed_branch_deletions(
    pull_requests: Sequence[PullRequest],
) -> tuple[str, ...]:
    active_heads = {
        pull_request.head_ref
        for pull_request in pull_requests
        if pull_request.incomplete
    }
    deletions: set[str] = set()
    for pull_request in pull_requests:
        marker = pull_request.marker
        match = AUTOMATION_BRANCH_PATTERN.fullmatch(pull_request.head_ref)
        if (
            not pull_request.merged
            or pull_request.head_ref in active_heads
            or marker is None
            or match is None
        ):
            continue
        if (
            marker["manifestSha256"][:16] != match.group("manifest")
            or marker["batchNumber"] != int(match.group("number"))
            or marker["batchId"].removeprefix("sha256:")[:12] != match.group("batch")
        ):
            continue
        deletions.add(pull_request.head_ref)
    if len(deletions) > MAX_COMPLETED_BRANCH_DELETIONS:
        raise BatchSyncError(
            f"Found {len(deletions)} verified completed automation branches, above the "
            f"{MAX_COMPLETED_BRANCH_DELETIONS}-branch cleanup limit"
        )
    return tuple(sorted(deletions))


def validate_marker_claim(
    pull_request: PullRequest,
    identity: OrphanBranch,
) -> None:
    marker = pull_request.marker
    if marker is None:
        return
    claimed = (
        marker["manifestSha256"],
        marker["manifestRunId"],
        marker["batchId"],
    )
    verified = (
        identity.manifest_digest,
        identity.manifest_run_id,
        identity.batch_id,
    )
    if claimed != verified:
        raise BatchSyncError(
            f"Pull request #{pull_request.number} body identity conflicts with its verified "
            "head commit"
        )


def select_active_manifest(
    current_manifest: Manifest,
    backend: AutomationBackend,
    campaign_branches: Sequence[OrphanBranch],
) -> Manifest:
    """Resume the single unfinished campaign, downloading its original retained artifact."""
    active_identities = [
        (branch.manifest_digest, branch.manifest_run_id) for branch in campaign_branches
    ]
    if not active_identities:
        return current_manifest

    digests = {digest for digest, _ in active_identities}
    if len(digests) != 1:
        raise BatchSyncError(
            "Multiple unfinished docs-vnext sync campaigns exist; close or merge one campaign "
            f"before retrying: {sorted(digests)}"
        )
    run_ids = {run_id for _, run_id in active_identities}
    if len(run_ids) != 1:
        raise BatchSyncError(
            "Unfinished campaign pull requests disagree on the retained manifest workflow run"
        )

    digest = next(iter(digests))
    run_id = next(iter(run_ids))
    resumed = load_manifest(backend.download_manifest(run_id), run_id)
    if resumed.digest != digest:
        raise BatchSyncError(
            f"Retained manifest from run {run_id} has digest {resumed.digest}, expected {digest}"
        )
    return resumed


def validate_campaign_identities(
    manifest: Manifest,
    batches: Sequence[Batch],
    backend: AutomationBackend,
    pull_requests: Sequence[PullRequest],
    campaign_branches: Sequence[OrphanBranch],
) -> dict[str, str]:
    """Bind every unfinished identity to one exact planned batch and verified branch."""
    batches_by_id = {batch.id: batch for batch in batches}
    claimed_batches: dict[str, str] = {}
    authenticated_commits: dict[str, str] = {}

    for pull_request in pull_requests:
        if not pull_request.incomplete or not pull_request.head_ref.startswith(
            f"{BRANCH_PREFIX}/"
        ):
            continue
        matching_identities = [
            identity
            for identity in campaign_branches
            if identity.pull_request_number == pull_request.number
        ]
        if len(matching_identities) != 1:
            raise BatchSyncError(
                f"Pull request #{pull_request.number} has {len(matching_identities)} "
                "verified head identities"
            )
        identity = matching_identities[0]
        batch = batches_by_id.get(identity.batch_id)
        if batch is None:
            raise BatchSyncError(
                f"Pull request #{pull_request.number} does not match an exact planned batch "
                f"for manifest {manifest.digest}"
            )
        if pull_request.marker is not None and pull_request.marker != _marker_payload(
            manifest, batch
        ):
            raise BatchSyncError(
                f"Pull request #{pull_request.number} body conflicts with its verified head identity"
            )
        expected_head = branch_name(manifest, batch)
        if identity.head_ref != pull_request.head_ref or pull_request.head_ref != expected_head:
            raise BatchSyncError(
                f"Pull request #{pull_request.number} head {pull_request.head_ref!r} does not "
                f"match deterministic branch {expected_head!r}"
            )
        prior = claimed_batches.setdefault(batch.id, f"pull request #{pull_request.number}")
        if prior != f"pull request #{pull_request.number}":
            raise BatchSyncError(f"Batch {batch.id} is claimed by both {prior} and a pull request")
        backend.publish_batch(
            manifest,
            batch,
            expected_head,
            expected_commit_sha=identity.commit_sha,
        )
        authenticated_commits[batch.id] = identity.commit_sha

    for orphan in campaign_branches:
        if orphan.pull_request_number is not None:
            continue
        batch = batches_by_id.get(orphan.batch_id)
        if (
            batch is None
            or orphan.manifest_digest != manifest.digest
            or orphan.manifest_run_id != manifest.run_id
        ):
            raise BatchSyncError(
                f"Orphan branch {orphan.head_ref!r} does not match an exact planned batch "
                f"for manifest {manifest.digest}"
            )
        expected_head = branch_name(manifest, batch)
        if orphan.head_ref != expected_head:
            raise BatchSyncError(
                f"Orphan branch {orphan.head_ref!r} does not match deterministic branch "
                f"{expected_head!r}"
            )
        prior = claimed_batches.setdefault(batch.id, f"orphan branch {orphan.head_ref}")
        if prior != f"orphan branch {orphan.head_ref}":
            raise BatchSyncError(f"Batch {batch.id} is claimed by both {prior} and an orphan branch")
        backend.publish_batch(
            manifest,
            batch,
            expected_head,
            expected_commit_sha=orphan.commit_sha,
        )
        authenticated_commits[batch.id] = orphan.commit_sha
    return authenticated_commits


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


def _directory_files(root: Path, relative_to: Path) -> set[str]:
    files: set[str] = set()
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise BatchSyncError(
                f"Replacement directory must not contain symbolic links: {candidate}"
            )
        if candidate.is_file():
            files.add(candidate.relative_to(relative_to).as_posix())
    return files


def apply_batch(repository_root: Path, manifest: Manifest, batch: Batch) -> tuple[str, ...]:
    """Verify all preconditions, then apply only the mutating operations in one batch."""
    source_root = _path_under(repository_root, manifest.source_root)
    target_root = _path_under(repository_root, manifest.target_root)
    if not source_root.is_dir() or not target_root.is_dir():
        raise BatchSyncError("Manifest source and target roots must exist in the batch worktree")

    removal_paths = {
        operation.path for operation in batch.operations if operation.decision == "remove"
    }
    addition_paths = {
        operation.path for operation in batch.operations if operation.decision == "add"
    }
    replacement_directories: set[Path] = set()
    resolved: list[tuple[Operation, Path, Path]] = []
    for operation in batch.operations:
        source_path = _path_under(source_root, operation.path)
        target_path = _path_under(target_root, operation.path)
        if operation.decision == "remove" and source_path.is_dir():
            expected_additions = {
                path for path in addition_paths if _strict_path_prefix(operation.path, path)
            }
            actual_files = _directory_files(source_path, source_root)
            if not expected_additions or actual_files != expected_additions:
                raise BatchSyncError(
                    f"File replaced by directory {operation.path!r} contains source files outside "
                    f"its atomic creation dependency: actual={sorted(actual_files)}, "
                    f"expected={sorted(expected_additions)}"
                )
        else:
            _verify_metadata(source_path, operation.source, f"Source for {operation.id}")
        if operation.decision == "add" and target_path.is_dir():
            expected_removals = {
                path for path in removal_paths if _strict_path_prefix(operation.path, path)
            }
            actual_files = _directory_files(target_path, target_root)
            if not expected_removals or actual_files != expected_removals:
                raise BatchSyncError(
                    f"Directory replaced by file {operation.path!r} contains files outside its "
                    f"atomic removal dependency: actual={sorted(actual_files)}, "
                    f"expected={sorted(expected_removals)}"
                )
            replacement_directories.add(target_path)
        else:
            _verify_metadata(target_path, operation.target, f"Target for {operation.id}")
        resolved.append((operation, source_path, target_path))

    changed_paths: list[str] = []
    removal_operations = sorted(
        (item for item in resolved if item[0].decision == "remove"),
        key=lambda item: len(PurePosixPath(item[0].path).parts),
        reverse=True,
    )
    for operation, _, target_path in removal_operations:
        target_path.unlink()
        changed_paths.append(f"{manifest.target_root}/{operation.path}")
    for directory in sorted(
        replacement_directories,
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        shutil.rmtree(directory)

    for operation, source_path, target_path in resolved:
        if operation.decision in {"add", "modify"}:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)
            changed_paths.append(f"{manifest.target_root}/{operation.path}")

    for operation, source_path, target_path in resolved:
        if operation.decision in {"add", "modify"}:
            _verify_metadata(target_path, _metadata(source_path), f"Applied target for {operation.id}")
        elif operation.decision == "remove":
            replacement_children = {
                path for path in addition_paths if _strict_path_prefix(operation.path, path)
            }
            if not (replacement_children and target_path.is_dir()):
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
    authenticated_batch_commits: dict[str, str] | None = None,
) -> bool:
    """Resume or publish batches sequentially and stop after the first partial failure."""
    checkpoint = _initial_checkpoint(manifest, batches, max_files, max_payload_bytes)
    _write_checkpoint(checkpoint_path, checkpoint)
    authenticated_batch_commits = authenticated_batch_commits or {}

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
                if (
                    batch.id not in authenticated_batch_commits
                    and not _matching_marker(manifest, batch, pull_request.marker)
                ):
                    raise BatchSyncError(
                        f"Pull request #{pull_request.number} uses {branch!r} with mismatched metadata"
                    )
                if pull_request.merged:
                    result = "existing-merged-pull-request"
                else:
                    backend.publish_batch(
                        manifest,
                        batch,
                        branch,
                        expected_commit_sha=authenticated_batch_commits.get(batch.id),
                    )
                if pull_request.state == "CLOSED":
                    pull_request = backend.reopen_pull_request(pull_request)
                    result = "reopened-pull-request"
                elif not pull_request.merged:
                    result = "existing-open-pull-request"
            else:
                backend.publish_batch(
                    manifest,
                    batch,
                    branch,
                    expected_commit_sha=authenticated_batch_commits.get(batch.id),
                )
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

    def _run_bounded_stdout(
        self,
        args: Sequence[str],
        *,
        max_bytes: int,
        cwd: Path | None = None,
        timeout_seconds: int = DISCOVERY_COMMAND_TIMEOUT_SECONDS,
    ) -> str:
        deadline = time.monotonic() + timeout_seconds
        windows_creation_flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | WINDOWS_CREATE_SUSPENDED
            if os.name == "nt"
            else 0
        )
        process = subprocess.Popen(
            list(args),
            cwd=cwd or self.repository_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == "posix",
            creationflags=windows_creation_flags,
        )
        windows_job: int | None = None
        windows_kernel32: Any | None = None
        if os.name == "nt":
            import ctypes

            class IoCounters(ctypes.Structure):
                _fields_ = [
                    ("ReadOperationCount", ctypes.c_ulonglong),
                    ("WriteOperationCount", ctypes.c_ulonglong),
                    ("OtherOperationCount", ctypes.c_ulonglong),
                    ("ReadTransferCount", ctypes.c_ulonglong),
                    ("WriteTransferCount", ctypes.c_ulonglong),
                    ("OtherTransferCount", ctypes.c_ulonglong),
                ]

            class BasicLimitInformation(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", ctypes.c_uint32),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", ctypes.c_uint32),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", ctypes.c_uint32),
                    ("SchedulingClass", ctypes.c_uint32),
                ]

            class ExtendedLimitInformation(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", BasicLimitInformation),
                    ("IoInfo", IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            class BasicAccountingInformation(ctypes.Structure):
                _fields_ = [
                    ("TotalUserTime", ctypes.c_longlong),
                    ("TotalKernelTime", ctypes.c_longlong),
                    ("ThisPeriodTotalUserTime", ctypes.c_longlong),
                    ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
                    ("TotalPageFaultCount", ctypes.c_uint32),
                    ("TotalProcesses", ctypes.c_uint32),
                    ("ActiveProcesses", ctypes.c_uint32),
                    ("TotalTerminatedProcesses", ctypes.c_uint32),
                ]

            class ThreadEntry32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", ctypes.c_uint32),
                    ("cntUsage", ctypes.c_uint32),
                    ("th32ThreadID", ctypes.c_uint32),
                    ("th32OwnerProcessID", ctypes.c_uint32),
                    ("tpBasePri", ctypes.c_long),
                    ("tpDeltaPri", ctypes.c_long),
                    ("dwFlags", ctypes.c_uint32),
                ]

            windows_kernel32 = ctypes.windll.kernel32
            windows_kernel32.CreateJobObjectW.restype = ctypes.c_void_p
            windows_kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
            windows_kernel32.OpenThread.restype = ctypes.c_void_p
            windows_job = windows_kernel32.CreateJobObjectW(None, None)
            limits = ExtendedLimitInformation()
            limits.BasicLimitInformation.LimitFlags = 0x00002000
            configured = bool(
                windows_job
                and windows_kernel32.SetInformationJobObject(
                    windows_job,
                    9,
                    ctypes.byref(limits),
                    ctypes.sizeof(limits),
                )
            )
            assigned = bool(
                configured
                and windows_kernel32.AssignProcessToJobObject(
                    windows_job,
                    int(process._handle),  # type: ignore[attr-defined]
                )
            )
            if not assigned:
                if windows_job:
                    windows_kernel32.CloseHandle(windows_job)
                process.kill()
                raise BatchSyncError("Cannot assign discovery command to a Windows Job Object")
            snapshot = windows_kernel32.CreateToolhelp32Snapshot(0x00000004, 0)
            invalid_handle = ctypes.c_void_p(-1).value
            resumed = False
            if snapshot != invalid_handle:
                entry = ThreadEntry32()
                entry.dwSize = ctypes.sizeof(entry)
                has_thread = windows_kernel32.Thread32First(snapshot, ctypes.byref(entry))
                while has_thread:
                    if entry.th32OwnerProcessID == process.pid:
                        thread_handle = windows_kernel32.OpenThread(
                            0x0002,
                            False,
                            entry.th32ThreadID,
                        )
                        if thread_handle:
                            resumed = windows_kernel32.ResumeThread(thread_handle) != 0xFFFFFFFF
                            windows_kernel32.CloseHandle(thread_handle)
                        break
                    has_thread = windows_kernel32.Thread32Next(
                        snapshot,
                        ctypes.byref(entry),
                    )
                windows_kernel32.CloseHandle(snapshot)
            if not resumed:
                windows_kernel32.TerminateJobObject(windows_job, 1)
                windows_kernel32.CloseHandle(windows_job)
                process.kill()
                raise BatchSyncError(
                    "Cannot resume discovery command primary thread after Job Object assignment"
                )
        assert process.stdout is not None
        assert process.stderr is not None
        stdout = bytearray()
        stderr = bytearray()
        overflow_streams: set[str] = set()
        overflow_event = threading.Event()
        termination_lock = threading.Lock()
        process_group_id = process.pid

        def close_windows_job() -> None:
            nonlocal windows_job
            if windows_job and windows_kernel32 is not None:
                windows_kernel32.CloseHandle(windows_job)
                windows_job = None

        def terminate_process_group() -> None:
            with termination_lock:
                remaining = max(0.0, deadline - time.monotonic())
                if os.name == "posix":
                    signaled_group = False
                    try:
                        os.killpg(process_group_id, signal.SIGTERM)
                        signaled_group = True
                    except (OSError, ProcessLookupError):
                        pass
                    if signaled_group and remaining > 0:
                        time.sleep(min(0.02, remaining))
                    if signaled_group:
                        try:
                            os.killpg(process_group_id, signal.SIGKILL)
                        except (OSError, ProcessLookupError):
                            pass
                    while time.monotonic() < deadline:
                        try:
                            os.killpg(process_group_id, 0)
                        except (OSError, ProcessLookupError):
                            break
                        time.sleep(0.005)
                elif os.name == "nt":
                    terminated_job = bool(
                        windows_job
                        and windows_kernel32 is not None
                        and windows_kernel32.TerminateJobObject(windows_job, 1)
                    )
                    if not terminated_job:
                        close_windows_job()
                    elif windows_job and windows_kernel32 is not None:
                        accounting = BasicAccountingInformation()
                        while time.monotonic() < deadline:
                            queried = windows_kernel32.QueryInformationJobObject(
                                windows_job,
                                1,
                                ctypes.byref(accounting),
                                ctypes.sizeof(accounting),
                                None,
                            )
                            if not queried or accounting.ActiveProcesses == 0:
                                break
                            time.sleep(0.005)
                else:
                    try:
                        process.kill()
                    except OSError:
                        pass
                if process.poll() is None:
                    try:
                        process.kill()
                    except OSError:
                        pass

        def join_readers() -> bool:
            for thread in (stdout_thread, stderr_thread):
                thread.join(timeout=max(0.0, deadline - time.monotonic()))
            return not stdout_thread.is_alive() and not stderr_thread.is_alive()

        def drain(stream: Any, destination: bytearray, name: str) -> None:
            try:
                while block := stream.read(1024):
                    destination.extend(block)
                    if len(destination) > max_bytes:
                        overflow_streams.add(name)
                        overflow_event.set()
                        return
            except (OSError, ValueError):
                return

        stdout_thread = threading.Thread(
            target=drain,
            args=(process.stdout, stdout, "stdout"),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=drain,
            args=(process.stderr, stderr, "stderr"),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()
        leader_exited_at: float | None = None
        while True:
            if overflow_event.is_set():
                terminate_process_group()
                join_readers()
                close_windows_job()
                raise BatchSyncError(
                    f"{args[0]} {args[1] if len(args) > 1 else ''} "
                    f"{'/'.join(sorted(overflow_streams))} exceeds the "
                    f"{max_bytes}-byte discovery limit"
                )

            now = time.monotonic()
            remaining = deadline - now
            if remaining <= DISCOVERY_TERMINATION_GRACE_SECONDS:
                terminate_process_group()
                join_readers()
                close_windows_job()
                raise BatchSyncError(
                    f"{args[0]} {args[1] if len(args) > 1 else ''} exceeded the "
                    f"{timeout_seconds}-second discovery timeout"
                )

            readers_alive = stdout_thread.is_alive() or stderr_thread.is_alive()
            leader_exited = process.poll() is not None
            if leader_exited and not readers_alive:
                break
            if leader_exited:
                leader_exited_at = leader_exited_at or now
                if now - leader_exited_at >= DISCOVERY_TERMINATION_GRACE_SECONDS:
                    terminate_process_group()
            time.sleep(min(0.01, remaining))
        if overflow_event.is_set() or overflow_streams:
            terminate_process_group()
            join_readers()
            close_windows_job()
            raise BatchSyncError(
                f"{args[0]} {args[1] if len(args) > 1 else ''} "
                f"{'/'.join(sorted(overflow_streams))} exceeds the "
                f"{max_bytes}-byte discovery limit"
            )
        terminate_process_group()
        if not join_readers():
            close_windows_job()
            raise BatchSyncError(
                f"{args[0]} discovery process tree did not stop before its deadline"
            )
        try:
            stdout_text = bytes(stdout).decode("utf-8")
            stderr_text = bytes(stderr).decode("utf-8")
        except UnicodeDecodeError as exc:
            close_windows_job()
            raise BatchSyncError(f"{args[0]} output is not valid UTF-8") from exc
        if process.returncode != 0:
            detail = (
                stderr_text.strip()
                or stdout_text.strip()
                or f"exit code {process.returncode}"
            )
            close_windows_job()
            raise BatchSyncError(f"{args[0]} {args[1] if len(args) > 1 else ''} failed: {detail}")
        close_windows_job()
        return stdout_text

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

    def _fetch_campaign_identity(
        self,
        source_ref: str,
        remote_ref: str,
        head_ref: str,
        pull_request_number: int | None = None,
        expected_commit_sha: str | None = None,
    ) -> OrphanBranch:
        self._run_bounded_stdout(
            [
                "git",
                "fetch",
                "--no-tags",
                "origin",
                f"+{source_ref}:{remote_ref}",
            ],
            max_bytes=MAX_COMMIT_MESSAGE_BYTES,
        )
        commit_sha = self._run_bounded_stdout(
            ["git", "rev-parse", remote_ref],
            max_bytes=MAX_COMMIT_MESSAGE_BYTES,
        ).strip()
        if not GIT_COMMIT_PATTERN.fullmatch(commit_sha):
            raise BatchSyncError(
                f"Fetched automation branch {head_ref!r} has invalid commit ID {commit_sha!r}"
            )
        if expected_commit_sha is not None and commit_sha != expected_commit_sha:
            raise BatchSyncError(
                f"Automation branch {head_ref!r} moved from discovered commit "
                f"{expected_commit_sha} to {commit_sha} before authentication"
            )
        commit_message = self._run_bounded_stdout(
            ["git", "show", "--no-patch", "--format=%B", commit_sha],
            max_bytes=MAX_COMMIT_MESSAGE_BYTES,
        )
        return replace(
            parse_commit_identity(commit_message, head_ref),
            pull_request_number=pull_request_number,
            commit_sha=commit_sha,
        )

    def _delete_completed_branches(
        self,
        pull_requests: Sequence[PullRequest],
    ) -> None:
        deletions = completed_branch_deletions(pull_requests)
        for head_ref in deletions:
            try:
                self._run_bounded_stdout(
                    ["git", "push", "origin", "--delete", head_ref],
                    max_bytes=MAX_REMOTE_DISCOVERY_BYTES,
                )
            except BatchSyncError:
                output = self._run_bounded_stdout(
                    [
                        "git",
                        "ls-remote",
                        "--heads",
                        "origin",
                        f"refs/heads/{head_ref}",
                    ],
                    max_bytes=MAX_REMOTE_DISCOVERY_BYTES,
                )
                if parse_remote_branch_refs(output):
                    raise

    def discover_campaign_branches(
        self, pull_requests: Sequence[PullRequest]
    ) -> list[OrphanBranch]:
        self._delete_completed_branches(pull_requests)
        output = self._run_bounded_stdout(
            [
                "git",
                "ls-remote",
                "--heads",
                "origin",
                f"refs/heads/{BRANCH_PREFIX}/*",
            ],
            max_bytes=MAX_REMOTE_DISCOVERY_BYTES,
        )
        remote_head_commits = exclude_completed_remote_heads(
            parse_remote_branch_refs(output),
            pull_requests,
        )
        remote_heads = set(remote_head_commits)
        all_pull_request_heads = {pull_request.head_ref for pull_request in pull_requests}
        incomplete_by_head: dict[str, PullRequest] = {}
        for pull_request in pull_requests:
            if not pull_request.incomplete or not pull_request.head_ref.startswith(
                f"{BRANCH_PREFIX}/"
            ):
                continue
            if pull_request.head_ref in incomplete_by_head:
                raise BatchSyncError(
                    f"Multiple unmerged pull requests use automation head "
                    f"{pull_request.head_ref!r}"
                )
            incomplete_by_head[pull_request.head_ref] = pull_request

        enforce_campaign_candidate_limit(remote_heads, set(incomplete_by_head))
        campaign_branches: list[OrphanBranch] = []
        for head_ref in sorted(remote_heads):
            pull_request = incomplete_by_head.get(head_ref)
            if head_ref in all_pull_request_heads and pull_request is None:
                continue
            identity = self._fetch_campaign_identity(
                f"refs/heads/{head_ref}",
                f"refs/remotes/origin/{head_ref}",
                head_ref,
                pull_request.number if pull_request is not None else None,
                expected_commit_sha=remote_head_commits[head_ref],
            )
            if pull_request is not None:
                validate_marker_claim(pull_request, identity)
            campaign_branches.append(identity)

        for head_ref, pull_request in incomplete_by_head.items():
            if head_ref in remote_heads:
                continue
            identity = self._fetch_campaign_identity(
                f"refs/pull/{pull_request.number}/head",
                f"refs/remotes/origin/pull-{pull_request.number}-head",
                head_ref,
                pull_request.number,
            )
            validate_marker_claim(pull_request, identity)
            campaign_branches.append(identity)

        return campaign_branches

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

    def publish_batch(
        self,
        manifest: Manifest,
        batch: Batch,
        branch: str,
        expected_commit_sha: str | None = None,
    ) -> None:
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
                    f"+refs/heads/{branch}:{remote_ref}",
                ]
            )
            final_commit_sha = self._run(
                ["git", "rev-parse", remote_ref]
            ).stdout.strip()
            if (
                expected_commit_sha is not None
                and final_commit_sha != expected_commit_sha
            ):
                raise BatchSyncError(
                    f"Automation branch {branch!r} moved from authenticated commit "
                    f"{expected_commit_sha} to {final_commit_sha} before final verification"
                )
            final_message = self._run(
                ["git", "show", "--no-patch", "--format=%B", final_commit_sha]
            ).stdout
            final_identity = parse_commit_identity(final_message, branch)
            if (
                final_identity.manifest_digest != manifest.digest
                or final_identity.manifest_run_id != manifest.run_id
                or final_identity.batch_id != batch.id
            ):
                raise BatchSyncError(
                    f"Automation branch {branch!r} final commit identity does not match "
                    "the planned manifest batch"
                )

        worktree = Path(tempfile.mkdtemp(prefix="docs-vnext-sync-", dir=self.runner_temp))
        worktree.rmdir()
        self._run(["git", "worktree", "add", "--detach", str(worktree), base_ref])
        try:
            changed_paths = apply_batch(worktree, manifest, batch)
            expected_names = set(changed_paths)
            if not expected_names:
                raise BatchSyncError(f"Batch {batch.number} has no mutating paths to publish")
            pathspecs = _minimal_pathspecs(expected_names)
            self._run(["git", "add", "--all", "--", *pathspecs], cwd=worktree)
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
                        *pathspecs,
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
                        f"Manifest-Run-ID: {manifest.run_id}\n"
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
        campaign_branches = active_backend.discover_campaign_branches(pull_requests)
        manifest = select_active_manifest(
            current_manifest,
            active_backend,
            campaign_branches,
        )
        batches = plan_batches(manifest, args.max_files, args.max_payload_bytes)
        authenticated_batch_commits = validate_campaign_identities(
            manifest,
            batches,
            active_backend,
            pull_requests,
            campaign_branches,
        )
        succeeded = execute_batches(
            manifest,
            batches,
            active_backend,
            pull_requests,
            args.checkpoint,
            args.max_files,
            args.max_payload_bytes,
            authenticated_batch_commits,
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
