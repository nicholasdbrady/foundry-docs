"""Generate a deterministic, non-mutating canonical-to-docs-vnext sync manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

MANIFEST_SCHEMA_VERSION = 1
ALLOWLIST_SCHEMA_VERSION = 1
DECISION_ORDER = {"add": 0, "modify": 1, "remove": 2, "preserve": 3}


class SyncManifestError(RuntimeError):
    """Raised when the synchronization inputs do not satisfy the planning contract."""


@dataclass(frozen=True, slots=True)
class PreserveRule:
    path: str
    kind: str

    def matches(self, relative_path: str) -> bool:
        return relative_path == self.path or (
            self.kind == "directory" and relative_path.startswith(f"{self.path}/")
        )


@dataclass(frozen=True, slots=True)
class FileMetadata:
    bytes: int
    sha256: str

    def as_dict(self) -> dict[str, int | str]:
        return {"bytes": self.bytes, "sha256": self.sha256}


def _validate_relative_path(value: Any, source: Path) -> str:
    if not isinstance(value, str) or not value:
        raise SyncManifestError(f"Preserve rule path must be a non-empty string: {source}")
    if "\\" in value or value.startswith("/") or value.endswith("/"):
        raise SyncManifestError(f"Preserve rule path must be a normalized POSIX relative path: {value!r}")

    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise SyncManifestError(f"Preserve rule path must not contain empty, '.' or '..' segments: {value!r}")

    normalized = PurePosixPath(value).as_posix()
    if normalized != value:
        raise SyncManifestError(f"Preserve rule path is not normalized: {value!r}")
    return normalized


def load_preserve_allowlist(path: Path) -> tuple[PreserveRule, ...]:
    """Load and schema-validate the explicit docs-vnext preserve allowlist."""
    if not path.is_file():
        raise SyncManifestError(f"Preserve allowlist does not exist: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SyncManifestError(f"Preserve allowlist is not valid JSON: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SyncManifestError(f"Preserve allowlist must be a JSON object: {path}")

    allowed_keys = {"$schema", "schemaVersion", "preserve"}
    unexpected_keys = sorted(set(data) - allowed_keys)
    if unexpected_keys:
        raise SyncManifestError(f"Preserve allowlist has unsupported fields {unexpected_keys}: {path}")
    if set(data) < {"schemaVersion", "preserve"}:
        raise SyncManifestError(f"Preserve allowlist requires schemaVersion and preserve: {path}")
    if type(data["schemaVersion"]) is not int or data["schemaVersion"] != ALLOWLIST_SCHEMA_VERSION:
        raise SyncManifestError(
            f"Preserve allowlist schemaVersion must be {ALLOWLIST_SCHEMA_VERSION}: {path}"
        )
    if "$schema" in data and not isinstance(data["$schema"], str):
        raise SyncManifestError(f"Preserve allowlist $schema must be a string: {path}")
    if not isinstance(data["preserve"], list):
        raise SyncManifestError(f"Preserve allowlist preserve field must be an array: {path}")

    rules: list[PreserveRule] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(data["preserve"]):
        if not isinstance(item, dict) or set(item) != {"kind", "path"}:
            raise SyncManifestError(
                f"Preserve rule {index} must contain only kind and path fields: {path}"
            )
        if item["kind"] not in {"directory", "file"}:
            raise SyncManifestError(f"Preserve rule {index} has invalid kind {item['kind']!r}: {path}")
        relative_path = _validate_relative_path(item["path"], path)
        if relative_path in seen_paths:
            raise SyncManifestError(f"Preserve allowlist contains duplicate path {relative_path!r}: {path}")
        seen_paths.add(relative_path)
        rules.append(PreserveRule(path=relative_path, kind=item["kind"]))

    rules.sort(key=lambda rule: (rule.path, rule.kind))
    for index, rule in enumerate(rules):
        for other in rules[index + 1 :]:
            if rule.kind == "directory" and other.path.startswith(f"{rule.path}/"):
                raise SyncManifestError(
                    f"Preserve rule {other.path!r} overlaps directory rule {rule.path!r}: {path}"
                )
    return tuple(rules)


def _hash_file(path: Path) -> FileMetadata:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return FileMetadata(bytes=size, sha256=digest.hexdigest())


def inventory_tree(root: Path) -> dict[str, FileMetadata]:
    """Return a sorted, content-addressed inventory of all regular files under root."""
    if not root.is_dir():
        raise SyncManifestError(f"Synchronization root is not a directory: {root}")
    if root.is_symlink():
        raise SyncManifestError(f"Synchronization root must not be a symbolic link: {root}")

    inventory: dict[str, FileMetadata] = {}
    for candidate in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative_path = candidate.relative_to(root).as_posix()
        if candidate.is_symlink():
            raise SyncManifestError(f"Synchronization trees must not contain symbolic links: {relative_path}")
        if candidate.is_file():
            inventory[relative_path] = _hash_file(candidate)
    return inventory


def _operation_id(decision: str, relative_path: str) -> str:
    value = f"docs-vnext-sync-manifest-v{MANIFEST_SCHEMA_VERSION}\0{decision}\0{relative_path}"
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _matching_rule(rules: tuple[PreserveRule, ...], relative_path: str) -> PreserveRule | None:
    return next((rule for rule in rules if rule.matches(relative_path)), None)


def _operation(
    decision: str,
    relative_path: str,
    source: FileMetadata | None,
    target: FileMetadata | None,
    preserve_rule: PreserveRule | None = None,
) -> dict[str, Any]:
    payload_bytes = source.bytes if decision in {"add", "modify"} and source is not None else 0
    operation: dict[str, Any] = {
        "id": _operation_id(decision, relative_path),
        "decision": decision,
        "path": relative_path,
        "fileCount": 1,
        "payloadBytes": payload_bytes,
        "source": source.as_dict() if source is not None else None,
        "target": target.as_dict() if target is not None else None,
    }
    if preserve_rule is not None:
        operation["preserveRule"] = {"kind": preserve_rule.kind, "path": preserve_rule.path}
    return operation


def _tree_summary(inventory: dict[str, FileMetadata]) -> dict[str, int]:
    return {
        "fileCount": len(inventory),
        "payloadBytes": sum(metadata.bytes for metadata in inventory.values()),
    }


def _logical_path(path: Path, repository_root: Path | None = None) -> str:
    resolved_path = path.resolve()
    if repository_root is not None:
        try:
            return resolved_path.relative_to(repository_root.resolve()).as_posix()
        except ValueError as exc:
            raise SyncManifestError(
                f"Manifest inputs must be inside the repository root: {resolved_path}"
            ) from exc
    if path.is_absolute():
        raise SyncManifestError("Absolute manifest inputs require an explicit repository root")
    return path.as_posix()


def build_manifest(
    source_root: Path,
    target_root: Path,
    allowlist_path: Path,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Build the complete synchronization plan without changing either input tree."""
    rules = load_preserve_allowlist(allowlist_path)
    source_inventory = inventory_tree(source_root)
    target_inventory = inventory_tree(target_root)

    operations: list[dict[str, Any]] = []
    matched_paths: dict[PreserveRule, list[str]] = {rule: [] for rule in rules}
    for relative_path in sorted(source_inventory.keys() | target_inventory.keys()):
        source = source_inventory.get(relative_path)
        target = target_inventory.get(relative_path)
        preserve_rule = _matching_rule(rules, relative_path)
        if preserve_rule is not None:
            matched_paths[preserve_rule].append(relative_path)
            operations.append(
                _operation("preserve", relative_path, source, target, preserve_rule=preserve_rule)
            )
        elif source is None:
            operations.append(_operation("remove", relative_path, source, target))
        elif target is None:
            operations.append(_operation("add", relative_path, source, target))
        elif source != target:
            operations.append(_operation("modify", relative_path, source, target))

    operations.sort(key=lambda item: (DECISION_ORDER[item["decision"]], item["path"]))
    decision_summaries = {
        decision: {
            "fileCount": sum(item["fileCount"] for item in operations if item["decision"] == decision),
            "payloadBytes": sum(
                item["payloadBytes"] for item in operations if item["decision"] == decision
            ),
        }
        for decision in DECISION_ORDER
    }

    preserve_rules = []
    for rule in rules:
        paths = matched_paths[rule]
        preserve_rules.append(
            {
                "kind": rule.kind,
                "path": rule.path,
                "matchedFileCount": len(paths),
                "matchedTargetBytes": sum(
                    target_inventory[relative_path].bytes
                    for relative_path in paths
                    if relative_path in target_inventory
                ),
            }
        )

    return {
        "schemaVersion": MANIFEST_SCHEMA_VERSION,
        "source": {"root": _logical_path(source_root, repository_root), **_tree_summary(source_inventory)},
        "target": {"root": _logical_path(target_root, repository_root), **_tree_summary(target_inventory)},
        "preserveAllowlist": {
            "path": _logical_path(allowlist_path, repository_root),
            "schemaVersion": ALLOWLIST_SCHEMA_VERSION,
            "rules": preserve_rules,
        },
        "summary": {
            "operationCount": len(operations),
            "payloadBytes": sum(item["payloadBytes"] for item in operations),
            "decisions": decision_summaries,
        },
        "operations": operations,
    }


def serialize_manifest(manifest: dict[str, Any]) -> str:
    """Serialize a manifest canonically for byte-for-byte repeatability."""
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("docs"))
    parser.add_argument("--target-dir", type=Path, default=Path("docs-vnext"))
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=Path(".github/docs-vnext-sync-preserve.json"),
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path("."),
        help="Root used to serialize stable repository-relative input paths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the manifest outside the input trees. Omit to emit JSON on stdout.",
    )
    return parser.parse_args(argv)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.output is not None and (
            _is_within(args.output, args.source_dir) or _is_within(args.output, args.target_dir)
        ):
            raise SyncManifestError("Manifest output must be outside the synchronization input trees")
        manifest = build_manifest(
            args.source_dir,
            args.target_dir,
            args.allowlist,
            repository_root=args.repository_root,
        )
        serialized = serialize_manifest(manifest)
        if args.output is None:
            sys.stdout.buffer.write(serialized.encode("utf-8"))
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(serialized.encode("utf-8"))
    except (OSError, SyncManifestError) as exc:
        print(f"docs-vnext sync manifest error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
