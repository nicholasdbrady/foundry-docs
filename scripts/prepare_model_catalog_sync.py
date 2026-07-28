"""Stage one bounded model catalog sync phase and write its change summary."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

CATALOG_FILENAMES = ("models-core.json", "models-huggingface.json")
SUMMARY_MODEL_LIMIT = 100


class CatalogSyncError(RuntimeError):
    """Raised when catalog inputs do not satisfy the sync contract."""


def _read_catalog(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CatalogSyncError(f"Required catalog file is missing: {path}")

    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        raise CatalogSyncError(f"Catalog file has an invalid models collection: {path}")
    return data


def _meaningful_catalog(path: Path) -> dict[str, Any]:
    data = _read_catalog(path)
    return {key: value for key, value in data.items() if key != "generatedAt"}


def _catalogs_match(left_dir: Path, right_dir: Path) -> bool:
    return all(
        _meaningful_catalog(left_dir / filename) == _meaningful_catalog(right_dir / filename)
        for filename in CATALOG_FILENAMES
    )


def _copy_changed_catalogs(source_dir: Path, target_dir: Path) -> list[str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    changed_filenames = []
    for filename in CATALOG_FILENAMES:
        source_path = source_dir / filename
        target_path = target_dir / filename
        if _meaningful_catalog(source_path) != _meaningful_catalog(target_path):
            shutil.copyfile(source_path, target_path)
            changed_filenames.append(filename)
    return changed_filenames


def _models_by_key(catalog: dict[str, Any], source: Path) -> dict[tuple[str, str], dict[str, Any]]:
    models_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for model in catalog["models"]:
        if not isinstance(model, dict) or not isinstance(model.get("id"), str):
            raise CatalogSyncError(f"Catalog contains a model without a string id: {source}")
        publisher = model.get("publisher", "")
        if not isinstance(publisher, str):
            raise CatalogSyncError(f"Catalog contains a model without a string publisher: {source}")
        model_key = (publisher, model["id"])
        if model_key in models_by_key:
            raise CatalogSyncError(f"Catalog contains duplicate publisher/id pair {model_key!r}: {source}")
        models_by_key[model_key] = model
    return models_by_key


def _models_by_directory(directory: Path) -> dict[tuple[str, str], dict[str, Any]]:
    models_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for filename in CATALOG_FILENAMES:
        path = directory / filename
        for model_key, model in _models_by_key(_read_catalog(path), path).items():
            if model_key in models_by_key:
                raise CatalogSyncError(
                    f"Catalog shards contain duplicate publisher/id pair {model_key!r}: {directory}"
                )
            models_by_key[model_key] = model
    return models_by_key


def _model_label(model_key: tuple[str, str]) -> str:
    publisher, model_id = model_key
    return f"{publisher}/{model_id}" if publisher else model_id


def _catalog_counts(directory: Path) -> dict[str, int]:
    core = len(_read_catalog(directory / "models-core.json")["models"])
    hugging_face = len(_read_catalog(directory / "models-huggingface.json")["models"])
    return {"core": core, "huggingFace": hugging_face, "total": core + hugging_face}


def _summarize_changes(before_dir: Path, after_dir: Path) -> dict[str, Any]:
    before_models = _models_by_directory(before_dir)
    after_models = _models_by_directory(after_dir)

    before_keys = set(before_models)
    after_keys = set(after_models)
    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)
    changed = sorted(
        model_key
        for model_key in before_keys & after_keys
        if before_models[model_key] != after_models[model_key]
    )

    changed_fields: Counter[str] = Counter()
    for model_key in changed:
        before_model = before_models[model_key]
        after_model = after_models[model_key]
        for field in before_model.keys() | after_model.keys():
            if before_model.get(field) != after_model.get(field):
                changed_fields[field] += 1

    return {
        "beforeCounts": _catalog_counts(before_dir),
        "afterCounts": _catalog_counts(after_dir),
        "addedCount": len(added),
        "addedModels": [_model_label(model_key) for model_key in added[:SUMMARY_MODEL_LIMIT]],
        "addedModelsTruncated": len(added) > SUMMARY_MODEL_LIMIT,
        "removedCount": len(removed),
        "removedModels": [_model_label(model_key) for model_key in removed[:SUMMARY_MODEL_LIMIT]],
        "removedModelsTruncated": len(removed) > SUMMARY_MODEL_LIMIT,
        "changedCount": len(changed),
        "changedModels": [_model_label(model_key) for model_key in changed[:SUMMARY_MODEL_LIMIT]],
        "changedModelsTruncated": len(changed) > SUMMARY_MODEL_LIMIT,
        "changedFields": dict(sorted(changed_fields.items())),
    }


def prepare_sync(
    generated_dir: Path,
    primary_dir: Path,
    mirror_dir: Path,
) -> dict[str, Any]:
    """Stage the mirror first when needed, otherwise stage freshly generated primary data."""
    for directory in (generated_dir, primary_dir, mirror_dir):
        for filename in CATALOG_FILENAMES:
            _read_catalog(directory / filename)

    if not _catalogs_match(primary_dir, mirror_dir):
        phase = "mirror"
        source_dir = primary_dir
        target_dir = mirror_dir
    else:
        phase = "primary"
        source_dir = generated_dir
        target_dir = primary_dir

    if _catalogs_match(source_dir, target_dir):
        return {
            "status": "noop",
            "phase": "noop",
            "message": "Model catalog data is up to date.",
            "beforeCounts": _catalog_counts(target_dir),
            "afterCounts": _catalog_counts(target_dir),
            "addedCount": 0,
            "addedModels": [],
            "addedModelsTruncated": False,
            "removedCount": 0,
            "removedModels": [],
            "removedModelsTruncated": False,
            "changedCount": 0,
            "changedModels": [],
            "changedModelsTruncated": False,
            "changedFields": {},
        }

    summary = _summarize_changes(target_dir, source_dir)
    changed_filenames = _copy_changed_catalogs(source_dir, target_dir)
    summary.update(
        {
            "status": "changes",
            "phase": phase,
            "message": (
                "Updated the primary docs model catalog."
                if phase == "primary"
                else "Synchronized the primary model catalog to docs-vnext."
            ),
            "targetDirectory": target_dir.as_posix(),
            "targetFiles": [
                str((target_dir / filename).as_posix()) for filename in changed_filenames
            ],
        }
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-dir", type=Path, required=True)
    parser.add_argument("--primary-dir", type=Path, required=True)
    parser.add_argument("--mirror-dir", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()

    summary = prepare_sync(args.generated_dir, args.primary_dir, args.mirror_dir)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
