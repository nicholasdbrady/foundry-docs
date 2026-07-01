#!/usr/bin/env python3
"""Watchdog for the signed-out Azure AI model catalog API and public UI contract."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
from collections.abc import Callable
from typing import Any

from scrape_model_catalog import (
    CATALOG_API_URL,
    CATALOG_HEADERS,
    CatalogContractError,
    _api_post,
    validate_catalog_page_contract,
)

CATALOG_UI_URL = "https://ai.azure.com/explore/models"


class WatchdogError(RuntimeError):
    """Raised when the catalog watchdog cannot verify the public API/UI contract."""


def _model_summary(raw_model: dict[str, Any]) -> dict[str, Any]:
    annotations = raw_model.get("annotations") or {}
    tags = annotations.get("tags") or {}
    system_catalog_data = annotations.get("systemCatalogData") or {}
    model_id = annotations.get("name") or raw_model.get("entityObjectId") or ""
    publisher = system_catalog_data.get("publisher") or tags.get("author") or ""
    if not model_id or not publisher:
        raise WatchdogError("Sample catalog model is missing a model id or publisher")

    return {
        "id": model_id,
        "publisher": publisher,
        "version": raw_model.get("version", ""),
        "hasAssetId": bool(raw_model.get("assetId")),
        "hasEntityId": bool(raw_model.get("entityId")),
    }


def run_api_contract_check(
    api_post: Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]] = _api_post,
) -> dict[str, Any]:
    """Call the signed-out asset-gallery API and return a bounded contract report."""
    body = {
        "pageSize": 1,
        "filters": [],
        "searchParameters": {},
    }
    try:
        data = api_post(CATALOG_API_URL, body, CATALOG_HEADERS)
        validate_catalog_page_contract(data, page=1)
    except (CatalogContractError, urllib.error.URLError, RuntimeError) as exc:
        raise WatchdogError(str(exc)) from exc

    models = data["value"]
    if not models:
        raise WatchdogError("Signed-out asset-gallery API returned no sample models")

    return {
        "apiUrl": CATALOG_API_URL,
        "sampleModels": len(models),
        "totalCount": data.get("totalCount"),
        "hasContinuationToken": bool(data.get("continuationToken")),
        "sampleModel": _model_summary(models[0]),
    }


def run_browser_contract_check(catalog_url: str = CATALOG_UI_URL, timeout_ms: int = 30_000) -> dict[str, Any]:
    """Use Playwright/CDP to verify the signed-out catalog page discovers the asset-gallery API."""
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise WatchdogError("Playwright is not installed; install the dev dependencies before running the UI watchdog") from exc

    observed_api_responses: list[dict[str, Any]] = []

    def record_response(response) -> None:
        if "/asset-gallery/" not in response.url or "/models" not in response.url:
            return
        observed_api_responses.append({"url": response.url, "status": response.status})

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context()
                page = context.new_page()
                page.on("response", record_response)
                cdp_session = context.new_cdp_session(page)
                cdp_session.send("Network.enable")

                with page.expect_response(
                    lambda res: "/asset-gallery/" in res.url and "/models" in res.url,
                    timeout=timeout_ms,
                ):
                    response = page.goto(catalog_url, wait_until="domcontentloaded", timeout=timeout_ms)
                    if response is None:
                        raise WatchdogError(f"Catalog page did not return a navigation response: {catalog_url}")
                    if response.status >= 400:
                        raise WatchdogError(f"Catalog page returned HTTP {response.status}: {catalog_url}")
                body_text = page.locator("body").inner_text(timeout=timeout_ms).lower()
            finally:
                browser.close()
    except PlaywrightTimeoutError as exc:
        raise WatchdogError("Timed out waiting for the public catalog UI to call the asset-gallery models API") from exc
    except PlaywrightError as exc:
        raise WatchdogError(f"Playwright could not verify the public catalog UI: {exc}") from exc

    if "model" not in body_text:
        raise WatchdogError("Catalog page loaded but did not render model catalog text")

    failed_responses = [res for res in observed_api_responses if res["status"] >= 400]
    if failed_responses:
        raise WatchdogError(f"Catalog UI observed failing asset-gallery responses: {failed_responses[:3]}")

    return {
        "catalogUrl": catalog_url,
        "observedAssetGalleryResponses": len(observed_api_responses),
        "statuses": sorted({res["status"] for res in observed_api_responses}),
    }


def _write_report(report: dict[str, Any], output_path: str | None) -> None:
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if output_path:
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(serialized)
            f.write("\n")
    print(serialized)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the signed-out Azure AI model catalog API/UI contract")
    parser.add_argument("--api-only", action="store_true", help="Skip the Playwright UI check")
    parser.add_argument("--catalog-url", default=CATALOG_UI_URL, help="Public catalog page to verify")
    parser.add_argument("--timeout-ms", type=int, default=30_000, help="Playwright timeout in milliseconds")
    parser.add_argument("--output", default=None, help="Optional JSON report path")
    args = parser.parse_args()

    try:
        report: dict[str, Any] = {
            "status": "ok",
            "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "api": run_api_contract_check(),
        }
        if not args.api_only:
            report["browser"] = run_browser_contract_check(args.catalog_url, args.timeout_ms)
    except (WatchdogError, CatalogContractError, urllib.error.URLError) as exc:
        _write_report(
            {
                "status": "blocked",
                "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "error": str(exc),
            },
            args.output,
        )
        return 2

    _write_report(report, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
