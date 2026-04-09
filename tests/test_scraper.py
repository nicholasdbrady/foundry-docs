"""Tests for scrape_model_catalog.py — deprecated filtering and region preservation."""

from __future__ import annotations

import json
import os
import tempfile

# Import from scripts/ which isn't a package, so adjust path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from scrape_model_catalog import CatalogModel, _preserve_existing_regions, filter_deprecated


def _make_model(id: str, publisher: str = "OpenAI", regions: dict | None = None) -> CatalogModel:
    return CatalogModel(
        id=id,
        displayName=id,
        publisher=publisher,
        latestVersion="1.0",
        regions=regions or {},
    )


class TestFilterDeprecated:
    def test_removes_deprecated_models(self):
        models = [_make_model("gpt-4"), _make_model("gpt-35-turbo"), _make_model("gpt-4o")]
        config = {"deprecated": {"models": ["gpt-35-turbo"]}}
        result = filter_deprecated(models, config)
        assert [m.id for m in result] == ["gpt-4", "gpt-4o"]

    def test_case_insensitive(self):
        models = [_make_model("GPT-35-Turbo"), _make_model("gpt-4o")]
        config = {"deprecated": {"models": ["gpt-35-turbo"]}}
        result = filter_deprecated(models, config)
        assert [m.id for m in result] == ["gpt-4o"]

    def test_empty_deprecated_list(self):
        models = [_make_model("gpt-4"), _make_model("gpt-4o")]
        config = {"deprecated": {"models": []}}
        result = filter_deprecated(models, config)
        assert len(result) == 2

    def test_no_deprecated_key(self):
        models = [_make_model("gpt-4")]
        config = {"publishers": {}}
        result = filter_deprecated(models, config)
        assert len(result) == 1

    def test_empty_config(self):
        models = [_make_model("gpt-4")]
        result = filter_deprecated(models, {})
        assert len(result) == 1

    def test_all_deprecated(self):
        models = [_make_model("old-model")]
        config = {"deprecated": {"models": ["old-model"]}}
        result = filter_deprecated(models, config)
        assert result == []

    def test_multiple_deprecated(self):
        models = [
            _make_model("gpt-35-turbo"),
            _make_model("gpt-4-32k"),
            _make_model("gpt-4o"),
            _make_model("davinci-002"),
        ]
        config = {"deprecated": {"models": ["gpt-35-turbo", "gpt-4-32k", "davinci-002"]}}
        result = filter_deprecated(models, config)
        assert [m.id for m in result] == ["gpt-4o"]


class TestPreserveExistingRegions:
    def test_preserves_regions_from_existing_file(self):
        models = [
            _make_model("gpt-4o", regions={}),
            _make_model("gpt-4.1", regions={"Standard": ["eastus"]}),
        ]
        existing_data = {
            "models": [
                {"id": "gpt-4o", "regions": {"GlobalStandard": ["eastus", "westus"]}},
                {"id": "gpt-4.1", "regions": {"Standard": ["eastus"]}},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(existing_data, f)
            tmp_path = f.name

        try:
            result = _preserve_existing_regions(models, tmp_path)
            gpt4o = next(m for m in result if m.id == "gpt-4o")
            gpt41 = next(m for m in result if m.id == "gpt-4.1")
            assert gpt4o.regions == {"GlobalStandard": ["eastus", "westus"]}
            # gpt-4.1 already had regions, so not overwritten
            assert gpt41.regions == {"Standard": ["eastus"]}
        finally:
            os.unlink(tmp_path)

    def test_no_existing_file(self):
        models = [_make_model("gpt-4o", regions={})]
        result = _preserve_existing_regions(models, "/nonexistent/path.json")
        assert result[0].regions == {}

    def test_existing_file_has_no_regions(self):
        models = [_make_model("gpt-4o", regions={})]
        existing_data = {"models": [{"id": "gpt-4o", "regions": {}}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(existing_data, f)
            tmp_path = f.name

        try:
            result = _preserve_existing_regions(models, tmp_path)
            assert result[0].regions == {}
        finally:
            os.unlink(tmp_path)

    def test_does_not_overwrite_new_regions(self):
        """If the new data has regions, don't replace them with old data."""
        models = [_make_model("gpt-4o", regions={"Standard": ["eastus2"]})]
        existing_data = {
            "models": [{"id": "gpt-4o", "regions": {"GlobalStandard": ["westus"]}}]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(existing_data, f)
            tmp_path = f.name

        try:
            result = _preserve_existing_regions(models, tmp_path)
            assert result[0].regions == {"Standard": ["eastus2"]}
        finally:
            os.unlink(tmp_path)

    def test_case_insensitive_matching(self):
        models = [_make_model("GPT-4o", regions={})]
        existing_data = {
            "models": [{"id": "gpt-4o", "regions": {"Standard": ["eastus"]}}]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(existing_data, f)
            tmp_path = f.name

        try:
            result = _preserve_existing_regions(models, tmp_path)
            assert result[0].regions == {"Standard": ["eastus"]}
        finally:
            os.unlink(tmp_path)
