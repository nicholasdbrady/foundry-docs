"""Tests for the deterministic docs-vnext baseline synchronization manifest."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from generate_docs_vnext_sync_manifest import (  # noqa: E402
    SyncManifestError,
    build_manifest,
    load_preserve_allowlist,
    main,
    serialize_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(root: Path, relative_path: str, content: bytes | str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _write_allowlist(path: Path, preserve: list[dict[str, str]], **extra: object) -> None:
    path.write_text(
        json.dumps({"schemaVersion": 1, "preserve": preserve, **extra}),
        encoding="utf-8",
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_plans_all_decisions_with_canonical_payloads_and_stable_order(tmp_path):
    source = tmp_path / "docs"
    target = tmp_path / "docs-vnext"
    allowlist = tmp_path / "preserve.json"
    _write(source, "z-add.mdx", "new")
    _write(source, "a-modify.mdx", "canonical")
    _write(source, "same.mdx", "same")
    _write(source, "preserved/shared.mdx", "canonical-preserved")
    _write(source, "docs.json", "canonical-navigation")
    _write(target, "a-modify.mdx", "vnext")
    _write(target, "m-remove.png", b"old-image")
    _write(target, "same.mdx", "same")
    _write(target, "preserved/shared.mdx", "vnext-preserved")
    _write(target, "preserved/only-vnext.mdx", "vnext-only")
    _write(target, "docs.json", "vnext-navigation")
    _write_allowlist(
        allowlist,
        [
            {"kind": "file", "path": "docs.json"},
            {"kind": "directory", "path": "preserved"},
        ],
    )

    manifest = build_manifest(source, target, allowlist, tmp_path)

    assert [(item["decision"], item["path"]) for item in manifest["operations"]] == [
        ("add", "z-add.mdx"),
        ("modify", "a-modify.mdx"),
        ("remove", "m-remove.png"),
        ("preserve", "docs.json"),
        ("preserve", "preserved/only-vnext.mdx"),
        ("preserve", "preserved/shared.mdx"),
    ]
    operations = {item["path"]: item for item in manifest["operations"]}
    assert operations["a-modify.mdx"]["payloadBytes"] == len("canonical")
    assert operations["a-modify.mdx"]["source"]["bytes"] == len("canonical")
    assert operations["a-modify.mdx"]["target"]["bytes"] == len("vnext")
    assert operations["m-remove.png"]["payloadBytes"] == 0
    assert operations["docs.json"]["preserveRule"] == {"kind": "file", "path": "docs.json"}
    assert all(item["fileCount"] == 1 for item in manifest["operations"])
    assert all(item["id"].startswith("sha256:") for item in manifest["operations"])


def test_summary_has_file_counts_and_payload_estimates(tmp_path):
    source = tmp_path / "docs"
    target = tmp_path / "docs-vnext"
    allowlist = tmp_path / "preserve.json"
    _write(source, "add.mdx", b"1234")
    _write(source, "modify.mdx", b"123456")
    _write(target, "modify.mdx", b"x")
    _write(target, "remove.mdx", b"removed")
    _write(target, "keep/file.mdx", b"keep")
    _write_allowlist(allowlist, [{"kind": "directory", "path": "keep"}])

    summary = build_manifest(source, target, allowlist, tmp_path)["summary"]

    assert summary == {
        "operationCount": 4,
        "payloadBytes": 10,
        "decisions": {
            "add": {"fileCount": 1, "payloadBytes": 4},
            "modify": {"fileCount": 1, "payloadBytes": 6},
            "remove": {"fileCount": 1, "payloadBytes": 0},
            "preserve": {"fileCount": 1, "payloadBytes": 0},
        },
    }


def test_repeated_planning_is_byte_identical_and_non_mutating(tmp_path):
    source = tmp_path / "docs"
    target = tmp_path / "docs-vnext"
    allowlist = tmp_path / "preserve.json"
    _write(source, "b/file.mdx", "source-b")
    _write(source, "a/file.mdx", "source-a")
    _write(target, "b/file.mdx", "target-b")
    _write(target, "remove/file.mdx", "remove")
    _write_allowlist(allowlist, [])
    before_source = _snapshot(source)
    before_target = _snapshot(target)

    first = serialize_manifest(build_manifest(source, target, allowlist, tmp_path))
    second = serialize_manifest(build_manifest(source, target, allowlist, tmp_path))

    assert first == second
    assert _snapshot(source) == before_source
    assert _snapshot(target) == before_target


def test_repository_root_makes_absolute_and_relative_input_paths_byte_identical(tmp_path):
    repository_root = tmp_path / "repo"
    source = repository_root / "docs"
    target = repository_root / "docs-vnext"
    allowlist = repository_root / ".github" / "preserve.json"
    _write(source, "page.mdx", "canonical")
    _write(target, "page.mdx", "vnext")
    allowlist.parent.mkdir(parents=True)
    _write_allowlist(allowlist, [])

    absolute = serialize_manifest(
        build_manifest(source.resolve(), target.resolve(), allowlist.resolve(), repository_root)
    )
    relative = serialize_manifest(
        build_manifest(
            repository_root / "docs",
            repository_root / "docs-vnext",
            repository_root / ".github" / "preserve.json",
            repository_root,
        )
    )

    assert absolute == relative
    manifest = json.loads(absolute)
    assert manifest["source"]["root"] == "docs"
    assert manifest["target"]["root"] == "docs-vnext"
    assert manifest["preserveAllowlist"]["path"] == ".github/preserve.json"


def test_cli_writes_only_the_requested_external_manifest(tmp_path):
    source = tmp_path / "docs"
    target = tmp_path / "docs-vnext"
    allowlist = tmp_path / "preserve.json"
    output = tmp_path / "artifacts" / "manifest.json"
    _write(source, "add.mdx", "content")
    target.mkdir()
    _write_allowlist(allowlist, [])

    exit_code = main(
        [
            "--source-dir",
            str(source),
            "--target-dir",
            str(target),
            "--allowlist",
            str(allowlist),
            "--repository-root",
            str(tmp_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    output_bytes = output.read_bytes()
    assert b"\r\n" not in output_bytes
    assert json.loads(output_bytes)["summary"]["operationCount"] == 1
    assert _snapshot(source) == {"add.mdx": b"content"}
    assert _snapshot(target) == {}


def test_cli_rejects_manifest_output_inside_an_input_tree(tmp_path, capsys):
    source = tmp_path / "docs"
    target = tmp_path / "docs-vnext"
    allowlist = tmp_path / "preserve.json"
    source.mkdir()
    target.mkdir()
    _write_allowlist(allowlist, [])

    exit_code = main(
        [
            "--source-dir",
            str(source),
            "--target-dir",
            str(target),
            "--allowlist",
            str(allowlist),
            "--repository-root",
            str(tmp_path),
            "--output",
            str(target / "manifest.json"),
        ]
    )

    assert exit_code == 2
    assert "outside the synchronization input trees" in capsys.readouterr().err
    assert not (target / "manifest.json").exists()


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"schemaVersion": 2, "preserve": []}, "schemaVersion"),
        ({"schemaVersion": 1, "preserve": [], "unknown": True}, "unsupported fields"),
        (
            {"schemaVersion": 1, "preserve": [{"kind": "file", "path": "../escape"}]},
            "must not contain",
        ),
        (
            {"schemaVersion": 1, "preserve": [{"kind": "file", "path": "bad\\path"}]},
            "normalized POSIX",
        ),
        (
            {"schemaVersion": 1, "preserve": [{"kind": "file", "path": "trailing/"}]},
            "normalized POSIX",
        ),
        (
            {"schemaVersion": 1, "preserve": [{"kind": "file", "path": "empty//segment"}]},
            "must not contain",
        ),
        (
            {"schemaVersion": 1, "preserve": [{"kind": "file", "path": "dot/./segment"}]},
            "must not contain",
        ),
        (
            {
                "schemaVersion": 1,
                "preserve": [
                    {"kind": "file", "path": "README.md"},
                    {"kind": "file", "path": "README.md"},
                ],
            },
            "duplicate",
        ),
        (
            {
                "schemaVersion": 1,
                "preserve": [
                    {"kind": "directory", "path": "slides"},
                    {"kind": "file", "path": "slides/deck.md"},
                ],
            },
            "overlaps",
        ),
    ],
)
def test_allowlist_schema_validation_rejects_invalid_contracts(tmp_path, payload, error):
    allowlist = tmp_path / "preserve.json"
    allowlist.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SyncManifestError, match=error):
        load_preserve_allowlist(allowlist)


def test_repository_preserve_allowlist_is_valid_and_explicit():
    rules = load_preserve_allowlist(REPO_ROOT / ".github" / "docs-vnext-sync-preserve.json")

    assert [(rule.kind, rule.path) for rule in rules] == [
        ("directory", ".mintlify"),
        ("file", "README.md"),
        ("file", "RFC-navigation-reflow.md"),
        ("file", "docs.json"),
        ("file", "reference/glossary.mdx"),
        ("directory", "slides"),
    ]


def test_json_schema_path_pattern_matches_runtime_normalization_contract():
    schema = json.loads(
        (REPO_ROOT / ".github" / "docs-vnext-sync-preserve.schema.json").read_text(encoding="utf-8")
    )
    pattern = schema["properties"]["preserve"]["items"]["properties"]["path"]["pattern"]

    for valid_path in [".mintlify", "README.md", "reference/glossary.mdx"]:
        assert re.fullmatch(pattern, valid_path)
    for invalid_path in ["/absolute", "bad\\path", "../escape", "a/../b", "a/./b", "a//b", "a/"]:
        assert re.fullmatch(pattern, invalid_path) is None
