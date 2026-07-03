"""Tests for scrape_model_catalog.py — deprecated filtering and region preservation."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

# Import from scripts/ which isn't a package, so adjust path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from check_model_catalog_watchdog import main as watchdog_main
from check_model_catalog_watchdog import run_api_contract_check
from check_model_catalog_watchdog import WatchdogError
from scrape_model_catalog import (
    CatalogContractError,
    CatalogModel,
    _preserve_existing_regions,
    fetch_all_models,
    filter_deprecated,
)


def _make_model(id: str, publisher: str = "OpenAI", regions: dict | None = None, lifecycle: str = "generally-available") -> CatalogModel:
    return CatalogModel(
        id=id,
        displayName=id,
        publisher=publisher,
        latestVersion="1.0",
        regions=regions or {},
        lifecycleStatus=lifecycle,
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

    def test_filters_by_api_lifecycle_status(self):
        models = [
            _make_model("old-model", lifecycle="deprecated"),
            _make_model("gpt-4o"),
        ]
        result = filter_deprecated(models, {})
        assert [m.id for m in result] == ["gpt-4o"]

    def test_both_config_and_api_lifecycle(self):
        models = [
            _make_model("config-dep"),
            _make_model("api-dep", lifecycle="deprecated"),
            _make_model("gpt-4o"),
        ]
        config = {"deprecated": {"models": ["config-dep"]}}
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


class TestAssetGalleryContract:
    def test_fetch_all_models_fails_when_pagination_exceeds_safety_limit(self, monkeypatch):
        def fake_post(_url, _body, _headers):
            return {
                "value": [
                    {
                        "annotations": {"name": "gpt-4o", "systemCatalogData": {"publisher": "OpenAI"}},
                        "version": "1",
                    }
                ],
                "continuationToken": "next-page",
            }

        monkeypatch.setattr("scrape_model_catalog.MAX_PAGES", 1)
        monkeypatch.setattr("scrape_model_catalog._api_post", fake_post)
        monkeypatch.setattr("scrape_model_catalog.time.sleep", lambda _seconds: None)

        with pytest.raises(CatalogContractError, match="continuationToken after 1 pages"):
            fetch_all_models()

    def test_watchdog_api_check_returns_bounded_contract_report(self):
        def fake_post(_url, body, _headers):
            assert body["pageSize"] == 1
            return {
                "totalCount": 123,
                "value": [
                    {
                        "entityId": "azureml://registries/azureml/models/gpt-4o/versions/1",
                        "assetId": "azureml://registries/azureml/models/gpt-4o/versions/1",
                        "annotations": {"name": "gpt-4o", "systemCatalogData": {"publisher": "OpenAI"}},
                        "version": "1",
                    }
                ],
                "continuationToken": "next-page",
            }

        report = run_api_contract_check(api_post=fake_post)

        assert report == {
            "apiUrl": "https://ai.azure.com/api/westus2/asset-gallery/v1.0/models",
            "sampleModels": 1,
            "totalCount": 123,
            "hasContinuationToken": True,
            "sampleModel": {
                "id": "gpt-4o",
                "publisher": "OpenAI",
                "version": "1",
                "hasAssetId": True,
                "hasEntityId": True,
            },
        }

    def test_watchdog_api_check_rejects_non_object_api_response(self):
        def fake_post(_url, _body, _headers):
            return []

        with pytest.raises(WatchdogError, match="Catalog page 1 response is not an object"):
            run_api_contract_check(api_post=fake_post)

    def test_watchdog_creates_parent_directory_for_report(self, monkeypatch, tmp_path):
        output_path = tmp_path / "reports" / "watchdog.json"
        monkeypatch.setattr(
            "check_model_catalog_watchdog.run_api_contract_check",
            lambda: {"sampleModels": 1},
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["check_model_catalog_watchdog.py", "--api-only", "--output", str(output_path)],
        )

        assert watchdog_main() == 0
        assert json.loads(output_path.read_text())["status"] == "ok"

    def test_watchdog_writes_blocked_report_for_api_contract_failure(self, monkeypatch, tmp_path):
        output_path = tmp_path / "reports" / "watchdog.json"

        def fail_contract():
            raise CatalogContractError("Catalog page 1 is missing annotations")

        monkeypatch.setattr("check_model_catalog_watchdog.run_api_contract_check", fail_contract)
        monkeypatch.setattr(
            sys,
            "argv",
            ["check_model_catalog_watchdog.py", "--api-only", "--output", str(output_path)],
        )

        assert watchdog_main() == 2
        report = json.loads(output_path.read_text())
        assert report["status"] == "blocked"
        assert report["error"] == "Catalog page 1 is missing annotations"

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
