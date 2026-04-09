#!/usr/bin/env python3
"""
Azure AI Model Catalog Scraper

Paginates the public Azure AI Asset Gallery API to collect model metadata,
filters to Azure-sold ("Direct from Azure") models, normalizes into a compact
JSON schema, validates output, and optionally merges region availability
from `generate_model_availability.py`.

When --include-partners is used, the output is split into two files:
  - models-core.json   (non-HuggingFace models — Azure Direct + curated partners)
  - models-huggingface.json  (HuggingFace managed-compute models, lazy-loaded by UI)

An enrichment config (model_enrichment.json) is applied to fix missing metadata
from the upstream API (e.g., Anthropic and Fireworks deployment types/regions).

Prerequisites:
  - Python 3.11+ (uses stdlib only — no pip install needed)
  - Optional: `az` CLI for region availability merge

Usage:
  python scrape_model_catalog.py                          # Output to stdout
  python scrape_model_catalog.py --output docs-vnext/static/data
  python scrape_model_catalog.py --include-partners       # Include non-Azure-direct models
  python scrape_model_catalog.py --merge-regions output/raw_data.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import asdict, dataclass, field

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

CATALOG_API_URL = "https://ai.azure.com/api/westus2/asset-gallery/v1.0/models"
PUBLISHERS_API_URL = "https://ai.azure.com/api/westus2/asset-gallery/v1.0/publishers/list"
CATALOG_HEADERS = {
    "Content-Type": "application/json",
    "x-ms-use-full-service-contracts": "true",
}
PAGE_SIZE = 100
MAX_PAGES = 200  # Safety limit: 200 * 100 = 20,000 models
MIN_AZURE_DIRECT_MODELS = 50  # Validation gate

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5.0


@dataclass(slots=True)
class CatalogModel:
    """Normalized model record for the catalog JSON output."""

    id: str
    displayName: str
    publisher: str
    latestVersion: str
    versions: list[str] = field(default_factory=list)
    summary: str = ""
    tasks: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    deploymentTypes: list[str] = field(default_factory=list)
    azureOffers: list[str] = field(default_factory=list)
    toolsSupported: list[str] = field(default_factory=list)
    inputModalities: list[str] = field(default_factory=list)
    outputModalities: list[str] = field(default_factory=list)
    contextWindow: int | None = None
    maxOutputTokens: int | None = None
    languages: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    license: str = ""
    pricingLink: str = ""
    isDirectFromAzure: bool = False
    lifecycleStatus: str = "generally-available"
    isPreview: bool = False
    trainingDataDate: str = ""
    createdAt: str = ""
    regions: dict[str, list[str]] = field(default_factory=dict)


def _api_post(url: str, body: dict, headers: dict) -> dict:
    """POST JSON to an API with retry logic."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                delay = RETRY_DELAY * attempt
                log.warning("  ⚠ HTTP %d on attempt %d, retrying in %.0fs...", e.code, attempt, delay)
                time.sleep(delay)
                continue
            raise
        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * attempt
                log.warning("  ⚠ URLError on attempt %d: %s, retrying in %.0fs...", attempt, e.reason, delay)
                time.sleep(delay)
                continue
            raise

    raise RuntimeError(f"Failed after {MAX_RETRIES} retries: {url}")


def fetch_publisher_icons() -> dict[str, str]:
    """Fetch publisher icons (base64-encoded SVGs) from the publishers API."""
    import base64

    log.info("  🎨 Fetching publisher icons...")
    data = _api_post(PUBLISHERS_API_URL, {}, {"Content-Type": "application/json"})
    icons = {}
    for p in data.get("value", []):
        name = p.get("publisherName", "") or p.get("displayName", "")
        icon_b64 = (p.get("icons") or {}).get("light", "")
        if name and icon_b64:
            try:
                svg = base64.b64decode(icon_b64).decode("utf-8")
                if "<svg" in svg:
                    icons[name] = icon_b64
            except Exception:
                pass
    log.info("  ✅ Got icons for %d publishers", len(icons))
    return icons


def fetch_all_models() -> list[dict]:
    """Paginate through the Asset Gallery API to collect all model records."""
    all_models = []
    continuation_token = None

    for page in range(1, MAX_PAGES + 1):
        body: dict = {
            "pageSize": PAGE_SIZE,
            "filters": [],
            "searchParameters": {},
        }
        if continuation_token:
            body["continuationToken"] = continuation_token

        log.info("  📄 Page %d (have %d models so far)...", page, len(all_models))
        data = _api_post(CATALOG_API_URL, body, CATALOG_HEADERS)

        items = data.get("value", [])
        all_models.extend(items)

        continuation_token = data.get("continuationToken")
        if not continuation_token:
            break

        # Be polite
        time.sleep(0.2)

    log.info("  ✅ Fetched %d total model records across %d pages", len(all_models), page)
    return all_models


def _safe_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _safe_list(val) -> list[str]:
    """Normalize a value to a list of strings."""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v).strip() for v in val if v]
    if isinstance(val, str):
        # Handle comma-separated strings
        return [v.strip() for v in val.split(",") if v.strip()]
    return []


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def normalize_model(raw: dict) -> CatalogModel | None:
    """Extract and normalize key fields from a raw API model record."""
    annotations = raw.get("annotations", {})
    tags = annotations.get("tags", {})
    scd = annotations.get("systemCatalogData", {})

    # Prefer systemCatalogData, fall back to tags
    model_name = annotations.get("name", "")
    display_name = scd.get("displayName") or tags.get("displayName") or model_name
    publisher = scd.get("publisher") or tags.get("author") or ""
    version = raw.get("version", "")

    if not model_name or not publisher:
        return None

    is_direct = (
        scd.get("isDirectFromAzure") is True
        or _safe_str(tags.get("isDirectFromAzure")).lower() == "true"
    )

    # Detect preview/deprecated from labels and tags
    labels = annotations.get("labels", [])
    is_preview = "Preview" in tags or any("preview" in str(label).lower() for label in labels)
    lifecycle = "preview" if is_preview else "generally-available"

    # Extract createdAt from properties.creationContext (most reliable source)
    props = raw.get("properties", {})
    creation_ctx = props.get("creationContext") or {}
    created_at = _safe_str(creation_ctx.get("createdTime", ""))
    if not created_at:
        # Fallback to systemData
        system_data = raw.get("annotations", {}).get("systemData") or {}
        if not system_data:
            system_data = props.get("systemData") or {}
        created_at = _safe_str(system_data.get("createdAt", ""))

    return CatalogModel(
        id=model_name,
        displayName=display_name,
        publisher=publisher,
        latestVersion=version,
        versions=[version],
        summary=_safe_str(scd.get("summary") or tags.get("summary")),
        tasks=_safe_list(scd.get("inferenceTasks") or tags.get("task")),
        capabilities=_safe_list(scd.get("modelCapabilities") or tags.get("modelCapabilities")),
        deploymentTypes=_safe_list(scd.get("deploymentTypes")),
        azureOffers=_safe_list(scd.get("azureOffers")),
        toolsSupported=_safe_list(scd.get("toolsSupported")),
        inputModalities=_safe_list(scd.get("inputModalities") or tags.get("inputModalities")),
        outputModalities=_safe_list(scd.get("outputModalities") or tags.get("outputModalities")),
        contextWindow=_safe_int(scd.get("textContextWindow") or tags.get("textContextWindow")),
        maxOutputTokens=_safe_int(scd.get("maxOutputTokens") or tags.get("maxOutputTokens")),
        languages=_safe_list(scd.get("languages") or tags.get("languages")),
        keywords=_safe_list(scd.get("keywords") or tags.get("keywords")),
        license=_safe_str(scd.get("license") or tags.get("license")),
        pricingLink=_safe_str(scd.get("pricingLink") or tags.get("pricingLink")),
        isDirectFromAzure=is_direct,
        lifecycleStatus=lifecycle,
        isPreview=is_preview,
        trainingDataDate=_safe_str(scd.get("trainingDataDate") or tags.get("trainingDataDate")),
        createdAt=created_at,
    )


def deduplicate_models(models: list[CatalogModel]) -> list[CatalogModel]:
    """Group by (publisher, model_id), keep the latest version as default, collect all versions."""
    groups: dict[tuple[str, str], list[CatalogModel]] = defaultdict(list)
    for m in models:
        key = (m.publisher.lower(), m.id.lower())
        groups[key].append(m)

    deduped = []
    for _key, versions in groups.items():
        # Sort by version string descending (works for date-based versions)
        versions.sort(key=lambda m: m.latestVersion, reverse=True)
        latest = versions[0]
        # Collect all version strings
        all_versions = sorted({v.latestVersion for v in versions}, reverse=True)
        latest.versions = all_versions
        latest.latestVersion = all_versions[0]
        # Merge capabilities across versions
        all_caps = set()
        all_tasks = set()
        all_dt = set()
        all_offers = set()
        all_tools = set()
        for v in versions:
            all_caps.update(v.capabilities)
            all_tasks.update(v.tasks)
            all_dt.update(v.deploymentTypes)
            all_offers.update(v.azureOffers)
            all_tools.update(v.toolsSupported)
        latest.capabilities = sorted(all_caps)
        latest.tasks = sorted(all_tasks)
        latest.deploymentTypes = sorted(all_dt)
        latest.azureOffers = sorted(all_offers)
        latest.toolsSupported = sorted(all_tools)
        # Use the earliest createdAt across all versions for proper release-date sorting
        all_dates = [v.createdAt for v in versions if v.createdAt]
        if all_dates:
            latest.createdAt = min(all_dates)
        deduped.append(latest)

    return sorted(deduped, key=lambda m: (m.publisher.lower(), m.id.lower()))


def merge_region_data(models: list[CatalogModel], raw_data_path: str) -> list[CatalogModel]:
    """Merge region availability from generate_model_availability.py output.

    Returns models with region data merged. Does NOT filter deprecated models —
    use filter_deprecated() for that (runs unconditionally via enrichment config).
    """
    if not os.path.exists(raw_data_path):
        log.warning("  ⚠ Region data file not found: %s — skipping region merge", raw_data_path)
        return models

    with open(raw_data_path) as f:
        region_data = json.load(f)

    # Build lookup: model_name -> { sku_name -> [regions] }
    region_map: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    deprecated_in_api: list[str] = []
    for rd in region_data:
        region = rd.get("region", "")
        for entry in rd.get("models", []):
            m = entry.get("model", {})
            name = m.get("name", "").lower()
            lifecycle = m.get("lifecycleStatus", "")
            if lifecycle == "Deprecated":
                deprecated_in_api.append(m.get("name", name))
                continue
            for sku in m.get("skus", []):
                sku_name = sku.get("name", "")
                if sku_name and region:
                    region_map[name][sku_name].append(region)

    if deprecated_in_api:
        unique_deprecated = sorted(set(deprecated_in_api))
        log.info("  ℹ  Region API reports %d deprecated models — ensure these are in model_enrichment.json[deprecated]:",
                 len(unique_deprecated))
        for name in unique_deprecated[:30]:
            log.info("      - %s", name)

    matched = 0
    for model in models:
        key = model.id.lower()
        if key in region_map:
            model.regions = {
                sku: sorted(set(regions)) for sku, regions in region_map[key].items()
            }
            matched += 1

    log.info("  📍 Region merge: %d/%d models matched", matched, len(models))
    if matched < len(models):
        unmatched = [m.id for m in models if not m.regions]
        log.info("  ℹ  Unmatched models: %s", ", ".join(unmatched[:20]))
        if len(unmatched) > 20:
            log.info("     ... and %d more", len(unmatched) - 20)

    return models


def validate_output(models: list[CatalogModel]) -> bool:
    """Validate the output data. Returns True if valid, False otherwise."""
    errors = []

    # Check minimum count
    azure_direct = [m for m in models if m.isDirectFromAzure]
    if len(azure_direct) < MIN_AZURE_DIRECT_MODELS:
        errors.append(
            f"Only {len(azure_direct)} Azure Direct models found "
            f"(minimum: {MIN_AZURE_DIRECT_MODELS})"
        )

    # Check required fields
    for m in models:
        if not m.id:
            errors.append(f"Model missing id: {m.displayName}")
        if not m.displayName:
            errors.append(f"Model missing displayName: {m.id}")
        if not m.publisher:
            errors.append(f"Model missing publisher: {m.id}")
        if not m.latestVersion:
            errors.append(f"Model missing latestVersion: {m.id}")

    # Check region data integrity
    for m in models:
        for sku, regions in m.regions.items():
            if not isinstance(regions, list):
                errors.append(f"Model {m.id}: regions[{sku}] is not a list")
            elif not all(isinstance(r, str) for r in regions):
                errors.append(f"Model {m.id}: regions[{sku}] contains non-string values")

    if errors:
        log.error("❌ Validation failed with %d errors:", len(errors))
        for e in errors[:20]:
            log.error("   - %s", e)
        return False

    log.info("  ✅ Validation passed: %d models (%d Azure Direct)", len(models), len(azure_direct))
    return True


def load_enrichment_config() -> dict:
    """Load the enrichment config from model_enrichment.json (sibling to this script)."""
    config_path = os.path.join(os.path.dirname(__file__), "model_enrichment.json")
    if not os.path.exists(config_path):
        log.warning("  ⚠ No enrichment config found at %s", config_path)
        return {}
    with open(config_path) as f:
        return json.load(f)


def apply_enrichment(models: list[CatalogModel], config: dict) -> list[CatalogModel]:
    """Apply publisher-level metadata overrides from enrichment config."""
    publishers = config.get("publishers", {})
    if not publishers:
        return models

    enriched = 0
    for model in models:
        overrides = publishers.get(model.publisher)
        if not overrides:
            continue

        if not model.deploymentTypes and overrides.get("deploymentTypes"):
            model.deploymentTypes = overrides["deploymentTypes"]

        if not model.regions and overrides.get("regions"):
            model.regions = dict(overrides["regions"])

        enriched += 1

    log.info("  🔧 Enriched %d models from config (%s)", enriched, ", ".join(publishers.keys()))
    return models


def apply_icon_fallbacks(publisher_icons: dict[str, str], config: dict) -> dict[str, str]:
    """Copy icons for publishers that should inherit another publisher's icon."""
    fallbacks = config.get("iconFallbacks", {})
    applied = 0
    for source_pub, target_pub in fallbacks.items():
        if source_pub == "$comment":
            continue
        if source_pub not in publisher_icons and target_pub in publisher_icons:
            publisher_icons[source_pub] = publisher_icons[target_pub]
            applied += 1
    if applied:
        log.info("  🎨 Applied %d icon fallbacks", applied)
    return publisher_icons


def filter_deprecated(models: list[CatalogModel], config: dict) -> list[CatalogModel]:
    """Remove deprecated models listed in enrichment config. Runs unconditionally."""
    deprecated_cfg = config.get("deprecated", {})
    deprecated_ids = {mid.lower() for mid in deprecated_cfg.get("models", [])}
    if not deprecated_ids:
        return models

    removed = [m for m in models if m.id.lower() in deprecated_ids]
    kept = [m for m in models if m.id.lower() not in deprecated_ids]
    if removed:
        log.info("  🗑️  Removed %d deprecated models: %s", len(removed), ", ".join(m.id for m in removed))
    return kept


def _preserve_existing_regions(models: list[CatalogModel], output_path: str) -> list[CatalogModel]:
    """Carry forward region data from existing output file for models that would otherwise lose it."""
    if not os.path.exists(output_path):
        return models

    with open(output_path) as f:
        existing = json.load(f)

    existing_regions: dict[str, dict] = {}
    for m in existing.get("models", []):
        regions = m.get("regions", {})
        if regions and any(regions.values()):
            existing_regions[m["id"].lower()] = regions

    if not existing_regions:
        return models

    preserved = 0
    for model in models:
        if (not model.regions or not any(model.regions.values())) and model.id.lower() in existing_regions:
            model.regions = existing_regions[model.id.lower()]
            preserved += 1

    if preserved:
        log.info("  🔄 Preserved existing region data for %d models", preserved)
    return models


def _write_json(data: dict, path: str) -> None:
    """Write JSON data to a file, log size."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(path) / 1024
    count = len(data.get("models", []))
    log.info("  📦 Wrote %s (%.1f KB, %d models)", path, size_kb, count)


def main():
    parser = argparse.ArgumentParser(description="Scrape Azure AI Model Catalog")
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (writes models.json). If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--include-partners",
        action="store_true",
        help="Include non-Azure-Direct partner models (default: Azure Direct only)",
    )
    parser.add_argument(
        "--merge-regions",
        default=None,
        help="Path to raw_data.json from generate_model_availability.py for region merge",
    )
    args = parser.parse_args()

    log.info("🔍 Fetching model catalog from Azure AI Asset Gallery...")
    publisher_icons = fetch_publisher_icons()
    raw_models = fetch_all_models()

    log.info("🔄 Normalizing %d raw records...", len(raw_models))
    normalized = []
    for raw in raw_models:
        model = normalize_model(raw)
        if model is not None:
            normalized.append(model)
    log.info("  ✅ Normalized %d models (skipped %d malformed)", len(normalized), len(raw_models) - len(normalized))

    if not args.include_partners:
        before = len(normalized)
        normalized = [m for m in normalized if m.isDirectFromAzure]
        log.info("  🔎 Filtered to Azure Direct: %d models (removed %d partner models)", len(normalized), before - len(normalized))

    log.info("🔀 Deduplicating across versions...")
    deduped = deduplicate_models(normalized)
    log.info("  ✅ %d unique models after deduplication", len(deduped))

    if args.merge_regions:
        log.info("📍 Merging region availability data...")
        deduped = merge_region_data(deduped, args.merge_regions)

    # Apply enrichment overrides (deployment types, regions, icons)
    enrichment = load_enrichment_config()
    if enrichment:
        log.info("🔧 Applying enrichment overrides...")
        deduped = apply_enrichment(deduped, enrichment)
        publisher_icons = apply_icon_fallbacks(publisher_icons, enrichment)

    # Filter deprecated models unconditionally (from enrichment config)
    if enrichment:
        log.info("🗑️  Filtering deprecated models...")
        deduped = filter_deprecated(deduped, enrichment)

    log.info("✔️  Validating output...")
    if not validate_output(deduped):
        log.error("💥 Aborting: validation failed. No output written.")
        sys.exit(1)

    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if args.output:
        os.makedirs(args.output, exist_ok=True)

        # Preserve existing region data for models that would otherwise lose it
        log.info("🔄 Checking for existing region data to preserve...")
        deduped = _preserve_existing_regions(deduped, os.path.join(args.output, "models.json"))
        deduped = _preserve_existing_regions(deduped, os.path.join(args.output, "models-core.json"))

        if args.include_partners:
            # Split into core (non-HF) and HuggingFace shards
            core_models = [m for m in deduped if m.publisher != "Hugging Face"]
            hf_models = [m for m in deduped if m.publisher == "Hugging Face"]

            log.info("📂 Splitting output: %d core + %d HuggingFace models", len(core_models), len(hf_models))

            core_data = {
                "generatedAt": generated_at,
                "totalModels": len(core_models),
                "publisherIcons": publisher_icons,
                "models": [asdict(m) for m in core_models],
            }
            _write_json(core_data, os.path.join(args.output, "models-core.json"))

            hf_data = {
                "generatedAt": generated_at,
                "totalModels": len(hf_models),
                "publisherIcons": {},
                "models": [asdict(m) for m in hf_models],
            }
            _write_json(hf_data, os.path.join(args.output, "models-huggingface.json"))

            # Also write the combined models.json for backward compatibility
            combined_data = {
                "generatedAt": generated_at,
                "totalModels": len(deduped),
                "publisherIcons": publisher_icons,
                "models": [asdict(m) for m in deduped],
            }
            _write_json(combined_data, os.path.join(args.output, "models.json"))

            log.info("✨ Done! Core: %d models, HuggingFace: %d models, Combined: %d models",
                     len(core_models), len(hf_models), len(deduped))
        else:
            output_data = {
                "generatedAt": generated_at,
                "totalModels": len(deduped),
                "publisherIcons": publisher_icons,
                "models": [asdict(m) for m in deduped],
            }
            _write_json(output_data, os.path.join(args.output, "models.json"))
            log.info("✨ Done! %d models", len(deduped))
    else:
        output_data = {
            "generatedAt": generated_at,
            "totalModels": len(deduped),
            "publisherIcons": publisher_icons,
            "models": [asdict(m) for m in deduped],
        }
        json.dump(output_data, sys.stdout, indent=2, ensure_ascii=False)
        print()


if __name__ == "__main__":
    main()
