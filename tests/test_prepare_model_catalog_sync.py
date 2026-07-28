"""Tests for bounded two-phase model catalog synchronization."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from prepare_model_catalog_sync import CATALOG_FILENAMES, _models_by_key, prepare_sync


def _write_catalogs(directory: Path, model_ids: list[str], generated_at: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    models = [{"id": model_id, "displayName": model_id} for model_id in model_ids]
    core = [model for model in models if not model["id"].startswith("hf-")]
    hugging_face = [model for model in models if model["id"].startswith("hf-")]
    payloads = {
        "models-core.json": core,
        "models-huggingface.json": hugging_face,
    }
    for filename, catalog_models in payloads.items():
        (directory / filename).write_text(
            json.dumps(
                {
                    "generatedAt": generated_at,
                    "totalModels": len(catalog_models),
                    "publisherIcons": {},
                    "models": catalog_models,
                }
            ),
            encoding="utf-8",
        )


def _read_ids(directory: Path) -> list[str]:
    model_ids = []
    for filename in CATALOG_FILENAMES:
        model_ids.extend(
            model["id"] for model in json.loads((directory / filename).read_text())["models"]
        )
    return model_ids


def test_updates_only_primary_when_corpora_are_in_sync(tmp_path):
    generated = tmp_path / "generated"
    primary = tmp_path / "docs"
    mirror = tmp_path / "docs-vnext"
    _write_catalogs(primary, ["model-a"], "old")
    _write_catalogs(mirror, ["model-a"], "old")
    _write_catalogs(generated, ["model-a", "model-b", "hf-model"], "new")

    summary = prepare_sync(generated, primary, mirror)

    assert summary["status"] == "changes"
    assert summary["phase"] == "primary"
    assert summary["beforeCounts"] == {"core": 1, "huggingFace": 0, "total": 1}
    assert summary["afterCounts"] == {"core": 2, "huggingFace": 1, "total": 3}
    assert summary["addedModels"] == ["hf-model", "model-b"]
    assert _read_ids(primary) == ["model-a", "model-b", "hf-model"]
    assert _read_ids(mirror) == ["model-a"]


def test_prioritizes_mirror_sync_before_new_primary_data(tmp_path):
    generated = tmp_path / "generated"
    primary = tmp_path / "docs"
    mirror = tmp_path / "docs-vnext"
    _write_catalogs(primary, ["model-a", "model-b"], "primary")
    _write_catalogs(mirror, ["model-a"], "mirror")
    _write_catalogs(generated, ["model-a", "model-b", "model-c"], "generated")

    summary = prepare_sync(generated, primary, mirror)

    assert summary["status"] == "changes"
    assert summary["phase"] == "mirror"
    assert summary["addedModels"] == ["model-b"]
    assert _read_ids(primary) == ["model-a", "model-b"]
    assert _read_ids(mirror) == ["model-a", "model-b"]


def test_ignores_generated_timestamp_only_changes(tmp_path):
    generated = tmp_path / "generated"
    primary = tmp_path / "docs"
    mirror = tmp_path / "docs-vnext"
    _write_catalogs(primary, ["model-a"], "primary")
    _write_catalogs(mirror, ["model-a"], "mirror")
    _write_catalogs(generated, ["model-a"], "generated")

    summary = prepare_sync(generated, primary, mirror)

    assert summary["status"] == "noop"
    assert summary["phase"] == "noop"
    for filename in CATALOG_FILENAMES:
        assert json.loads((primary / filename).read_text())["generatedAt"] == "primary"
        assert (primary / filename).read_text() != (generated / filename).read_text()


def test_model_identity_includes_publisher():
    catalog = {
        "models": [
            {"id": "shared-id", "publisher": "Publisher A"},
            {"id": "shared-id", "publisher": "Publisher B"},
        ]
    }

    models = _models_by_key(catalog, Path("models.json"))

    assert set(models) == {("Publisher A", "shared-id"), ("Publisher B", "shared-id")}


def test_copies_only_meaningfully_changed_shards(tmp_path):
    generated = tmp_path / "generated"
    primary = tmp_path / "docs"
    mirror = tmp_path / "docs-vnext"
    _write_catalogs(primary, ["model-a", "hf-model"], "old")
    _write_catalogs(mirror, ["model-a", "hf-model"], "old")
    _write_catalogs(generated, ["model-a", "model-b", "hf-model"], "new")

    summary = prepare_sync(generated, primary, mirror)

    assert summary["targetFiles"] == [(primary / "models-core.json").as_posix()]
    assert json.loads((primary / "models-core.json").read_text())["generatedAt"] == "new"
    assert json.loads((primary / "models-huggingface.json").read_text())["generatedAt"] == "old"
