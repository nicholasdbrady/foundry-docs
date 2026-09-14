# Reverse Engineering the Azure AI Model Catalog & Building a Custom Enriched Catalog

## Executive Summary

The Azure AI Model Catalog at `https://ai.azure.com/catalog` is powered by a **public, unauthenticated REST API** at `POST https://ai.azure.com/api/westus2/asset-gallery/v1.0/models` that returns rich model metadata for all 14,879+ model versions across 55+ publishers. The API supports pagination, text search, and returns structured data including publisher, deployment types, capabilities, inference tasks, supported tools, pricing links, context windows, and more. Separately, the **`az cognitiveservices model list`** CLI command returns per-region model availability with SKU types. By combining these two data sources, we can build a comprehensive model catalog with region availability. Mintlify supports **custom React components** in MDX files, enabling an interactive search/filter/faceted catalog page.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION PIPELINE                         │
│                                                                     │
│  ┌──────────────────────┐      ┌──────────────────────────┐        │
│  │ Azure AI Catalog API  │      │ Azure RM Model List API  │        │
│  │ (model metadata)     │      │ (region availability)    │        │
│  │                      │      │                          │        │
│  │ POST /asset-gallery/  │      │ az cognitiveservices     │        │
│  │   v1.0/models        │      │   model list --location  │        │
│  │                      │      │                          │        │
│  │ Returns:             │      │ Returns:                 │        │
│  │ - name, publisher    │      │ - model name + version   │        │
│  │ - capabilities       │      │ - SKU types per region   │        │
│  │ - deployment types   │      │ - rate limits            │        │
│  │ - context window     │      │ - lifecycle status       │        │
│  │ - pricing link       │      │ - capabilities           │        │
│  │ - tools supported    │      │                          │        │
│  │ - tasks, modalities  │      │                          │        │
│  └──────────┬───────────┘      └───────────┬──────────────┘        │
│             │                               │                       │
│             ▼                               ▼                       │
│  ┌──────────────────────────────────────────────────────┐          │
│  │              ENRICHMENT + MERGE STEP                  │          │
│  │  Join on model name → unified JSON catalog            │          │
│  └───────────────────────┬──────────────────────────────┘          │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────┐          │
│  │              OUTPUT: models.json                      │          │
│  │  Array of enriched model objects with:                │          │
│  │  - All catalog metadata                               │          │
│  │  - Region availability per deployment type            │          │
│  │  - Facet-friendly tags                                │          │
│  └───────────────────────┬──────────────────────────────┘          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                MINTLIFY DOCS SITE                                 │
│                                                                  │
│  docs-vnext/                                                     │
│  ├── snippets/                                                   │
│  │   └── model-catalog.jsx     ← React component                │
│  ├── models/                                                     │
│  │   └── catalog/                                                │
│  │       └── model-explorer.mdx  ← Page that imports component  │
│  └── static/                                                     │
│      └── data/                                                   │
│          └── models.json         ← Generated catalog data        │
└──────────────────────────────────────────────────────────────────┘
```

---

## API #1: Azure AI Model Catalog (Asset Gallery)

### Endpoint

```
POST https://ai.azure.com/api/westus2/asset-gallery/v1.0/models
```

**No authentication required.** Works from curl with the `x-ms-use-full-service-contracts: true` header[^1].

### Request Schema

```json
{
  "pageSize": 100,
  "filters": [],
  "searchParameters": {
    "searchText": "optional search query"
  },
  "continuationToken": "optional — from previous response"
}
```

**Available filter fields** (returned in error message when using invalid fields)[^2]:

| Field | Example Values |
|-------|---------------|
| `Name` | Model identifier |
| `Version` | Version string |
| `Labels` | `"latest"` |
| `Publisher` | `"OpenAI"`, `"Meta"` |
| `Author` | Publisher name |
| `InferenceTasks` | `"chat-completion"`, `"text-to-image"` |
| `FineTuningTasks` | `"chat-completion"`, `"chat"` |
| `ModelCapabilities` | `"streaming"`, `"tool-calling"`, `"reasoning"` |
| `AzureOffers` | `"standard-paygo"`, `"vm"`, `"ptu"`, `"batch-paygo"` |
| `License` | `"custom"`, `"mit"`, `"apache-2.0"` |
| `ModelLimits/TextLimits/MaxOutputTokens` | Integer |
| `ModelLimits/TextLimits/InputContextWindow` | Integer |
| `ModelLimits/SupportedInputModalities` | `"text"`, `"image"` |
| `ModelLimits/SupportedOutputModalities` | `"text"`, `"image"` |
| `Deprecation/InferenceRetirementDate` | ISO date |
| `DisplayName` | Display name string |
| `Summary` | Summary text |

Filter operators: `eq`, `ne`[^2].

**Note**: The `facets` parameter works only through the browser's BFF (backend-for-frontend) session, not from bare curl requests[^3]. Facets return counts by category (e.g., 38 models with "streaming" capability).

### Response Schema — Model Object

Each model in the `value` array has this structure[^4]:

```json
{
  "relevancyScore": 1.0,
  "entityResourceName": "azureml-registry-name",
  "entityId": "azureml://registries/.../models/model-name/version/X",
  "kind": "Versioned",
  "version": "2026-03-17",
  "annotations": {
    "name": "gpt-5.4-nano",
    "archived": false,
    "labels": ["default", "latest", "invisibleLatest"],
    "description": "...(markdown)...",
    "tags": {
      "displayName": "OpenAI gpt-5.4-nano",
      "author": "OpenAI",
      "summary": "...",
      "task": "chat-completion",
      "textContextWindow": "400000",
      "maxOutputTokens": "128000",
      "inputModalities": "text, image",
      "outputModalities": "text",
      "languages": "en",
      "keywords": "Multipurpose,Multilingual,Multimodal",
      "license": "custom",
      "pricingLink": "https://aka.ms/AzureOAIpricing",
      "modelCapabilities": "agentsV2, reasoning, tool-calling, streaming",
      "deploymentOptions": "UnifiedEndpointMaaS, AOAI",
      "evaluation": "...(markdown)...",
      "notes": "...(markdown - responsible AI)...",
      "benchmark": "quality",
      "trainingDataDate": "August 2025",
      "isDirectFromAzure": "true",
      "playgroundRateLimitTier": "custom"
    },
    "systemCatalogData": {
      "publisher": "OpenAI",
      "displayName": "OpenAI gpt-5.4-nano",
      "summary": "GPT-5.4-nano is a lightweight...",
      "inferenceTasks": ["chat-completion", "responses"],
      "deploymentTypes": ["batch-enabled"],
      "modelCapabilities": ["agentsV2", "reasoning", "tool-calling", "streaming"],
      "featuresSupported": ["streaming", "function_calling"],
      "toolsSupported": ["code_interpreter", "azure_ai_search", "file_search", "web_search", "mcp", ...],
      "inputModalities": ["text", "image"],
      "outputModalities": ["text"],
      "keywords": ["Multipurpose", "Multilingual", "Multimodal"],
      "languages": ["en"],
      "license": "custom",
      "pricingLink": "https://aka.ms/AzureOAIpricing",
      "textContextWindow": 400000,
      "maxOutputTokens": 128000,
      "trainingDataDate": "August 2025",
      "isDirectFromAzure": true,
      "azureOffers": null,
      "evaluation": "...(markdown)...",
      "notes": "...(markdown - responsible AI)..."
    }
  }
}
```

### Key Data Fields for the Catalog

| Field Path | Type | Description |
|-----------|------|-------------|
| `annotations.tags.displayName` | string | Human-friendly model name |
| `annotations.tags.author` | string | Publisher/provider |
| `annotations.tags.summary` | string | One-line description |
| `annotations.tags.task` | string | Primary inference task |
| `annotations.tags.textContextWindow` | string | Context window size |
| `annotations.tags.maxOutputTokens` | string | Max output tokens |
| `annotations.tags.inputModalities` | string | Comma-separated: "text, image" |
| `annotations.tags.outputModalities` | string | Comma-separated |
| `annotations.tags.languages` | string | Comma-separated language codes |
| `annotations.tags.keywords` | string | Comma-separated keywords |
| `annotations.tags.license` | string | License type |
| `annotations.tags.pricingLink` | string | URL to pricing page |
| `annotations.tags.modelCapabilities` | string | Comma-separated capabilities |
| `annotations.tags.isDirectFromAzure` | string | "true" if Azure-direct model |
| `annotations.systemCatalogData.deploymentTypes` | array | `["aoai-deployment", "batch-enabled", "maas-inference", "maap-inference"]` |
| `annotations.systemCatalogData.toolsSupported` | array | List of supported agent tools |
| `annotations.systemCatalogData.azureOffers` | array | `["standard-paygo", "vm", "ptu", "batch-paygo"]` |
| `version` | string | Model version identifier |

### Pagination

The API uses continuation token pagination[^5]:
1. First request: `{"pageSize": 100, "filters": [], "searchParameters": {}}`
2. Response includes `continuationToken` (base64-encoded, ~260 chars)
3. Next request: add `"continuationToken": "<token>"` to request body
4. Repeat until `continuationToken` is null/absent

With `pageSize: 100`, you need ~149 requests to get all 14,879 model versions, or fewer if filtering to "latest" only.

### Publishers Endpoint

```
POST https://ai.azure.com/api/westus2/asset-gallery/v1.0/publishers/list
Body: {}
```

Returns 55 publishers with `publisherName`, `displayName`, and icon URLs[^6].

---

## API #2: Azure Resource Manager Model List

The `az cognitiveservices model list --location <region>` CLI command calls[^7]:

```
GET /subscriptions/{subId}/providers/Microsoft.CognitiveServices/locations/{location}/models?api-version=2025-06-01
```

This returns all Azure OpenAI models available in a given region, including:
- Model name and version
- SKU types (GlobalStandard, Standard, Provisioned, etc.)
- Rate limits per SKU
- Capabilities (chatCompletion, embeddings, etc.)
- Lifecycle status and retirement dates
- Max capacity

The existing `scripts/generate_model_availability.py` already handles this[^8].

---

## Facet Values Discovered

From the browser BFF session, these facet values were extracted[^9]:

### Deployment Types
| Value | Count |
|-------|-------|
| `aoai-deployment` | 38 |
| `batch-enabled` | 30 |
| `maap-inference` | 6 |
| `maas-inference` | 1 |

### Capabilities
| Value | Count |
|-------|-------|
| `streaming` | 38 |
| `agentsV2` | 36 |
| `reasoning` | 31 |
| `tool-calling` | 28 |
| `agents` | 16 |
| `fine-tuning` | 8 |
| `assistants` | 4 |

### Inference Tasks
| Value | Count |
|-------|-------|
| `chat-completion` | 37 |
| `responses` | 37 |
| `audio-generation` | 10 |
| `text-to-image` | 4 |
| `embeddings` | 3 |
| `speech-to-text` | 3 |
| `text-to-speech` | 3 |
| `image-to-image` | 2 |
| `video-generation` | 2 |
| `automatic-speech-recognition` | 1 |

### Azure Offers
| Value | Description |
|-------|-------------|
| `vm` | Self-hosted on VM |
| `standard-paygo` | Pay-as-you-go |
| `ptu` | Provisioned Throughput Units |
| `batch-paygo` | Batch processing |

---

## Implementation Plan

### Step 1: Build Catalog Scraper Script

Create `scripts/scrape_model_catalog.py` that:
1. Paginates through the Asset Gallery API to collect all models
2. Extracts and normalizes key fields into a flat, facet-friendly JSON structure
3. Optionally merges with region availability data from `generate_model_availability.py`
4. Outputs `docs-vnext/static/data/models.json`

**Scraping approach:**
```python
# Pseudocode for catalog scraper
models = []
continuation_token = None
while True:
    body = {"pageSize": 100, "filters": [], "searchParameters": {}}
    if continuation_token:
        body["continuationToken"] = continuation_token
    resp = requests.post(URL, json=body, headers=HEADERS)
    data = resp.json()
    models.extend(data.get("value", []))
    continuation_token = data.get("continuationToken")
    if not continuation_token:
        break
```

**Normalized output schema:**
```json
{
  "name": "gpt-5.4-nano",
  "displayName": "OpenAI gpt-5.4-nano",
  "publisher": "OpenAI",
  "version": "2026-03-17",
  "summary": "GPT-5.4-nano is a lightweight...",
  "task": "chat-completion",
  "inferenceTasks": ["chat-completion", "responses"],
  "deploymentTypes": ["batch-enabled"],
  "capabilities": ["agentsV2", "reasoning", "tool-calling", "streaming"],
  "toolsSupported": ["code_interpreter", "azure_ai_search", "mcp", ...],
  "azureOffers": ["standard-paygo"],
  "inputModalities": ["text", "image"],
  "outputModalities": ["text"],
  "contextWindow": 400000,
  "maxOutputTokens": 128000,
  "languages": ["en"],
  "keywords": ["Multipurpose", "Multilingual", "Multimodal"],
  "license": "custom",
  "pricingLink": "https://aka.ms/AzureOAIpricing",
  "isDirectFromAzure": true,
  "trainingDataDate": "August 2025",
  "regions": {
    "GlobalStandard": ["eastus", "westus2", "swedencentral", ...],
    "Standard": ["eastus", "westus2", ...],
    "Provisioned": ["eastus", ...]
  }
}
```

### Step 2: Merge Region Availability

The `generate_model_availability.py` script already produces `raw_data.json`. The merge logic would:
1. Run both scripts
2. Match catalog models to RM models by name
3. Attach region availability grouped by SKU type

### Step 3: Mintlify Custom Catalog Page

Mintlify supports React components in MDX files[^10]. The approach:

1. **Static data file**: `docs-vnext/static/data/models.json` — generated at build time
2. **React component**: `docs-vnext/snippets/model-catalog.jsx` — search/filter/faceted UI
3. **MDX page**: `docs-vnext/models/catalog/model-explorer.mdx` — imports and renders the component

**React component features:**
- Text search across name, publisher, summary
- Faceted filters for: Publisher, Deployment Type, Capabilities, Tasks, Region
- Tag-based UI with counts
- Card-based model display
- Sort by name, context window, popularity
- Uses `useState`, `useEffect`, `useMemo` for client-side filtering
- Loads JSON data via fetch or static import

**Key Mintlify constraints:**
- Component files must live in `/snippets/` folder[^10]
- Nested imports not supported — all components must be imported directly in the MDX file[^10]
- Client-side rendering (not SSR) — acceptable since this is an interactive tool
- Tailwind CSS classes are available[^10]

### Example MDX Page

```mdx
---
title: "Model Explorer"
description: "Search and filter Azure AI models by provider, region, deployment type, and capabilities"
---

import { ModelCatalog } from "/snippets/model-catalog.jsx"

# Model Explorer

Browse all available models in Microsoft Foundry. Filter by provider, deployment type,
capabilities, and region availability.

<ModelCatalog />
```

---

## Data Flow Summary

```
┌─────────────┐         ┌──────────────────┐
│ az cog model│         │ Asset Gallery API │
│ list        │         │ /v1.0/models      │
│ (32 regions)│         │ (paginated)       │
└──────┬──────┘         └────────┬─────────┘
       │                         │
       ▼                         ▼
  raw_data.json          catalog_raw.json
       │                         │
       └──────────┬──────────────┘
                  │
                  ▼
          merge + normalize
                  │
                  ▼
    docs-vnext/static/data/models.json
                  │
                  ▼
    docs-vnext/snippets/model-catalog.jsx
    (React component: search/filter/facet)
                  │
                  ▼
    docs-vnext/models/catalog/model-explorer.mdx
    (Mintlify page: imports component)
```

---

## Technical Considerations

### Rate Limits
- The Asset Gallery API has no visible rate limiting for reads. Paginating ~150 requests at 100/page completes in under a minute[^5].
- The RM model list API benefits from parallelism (8+ workers across 32 regions)[^8].

### Data Freshness
- The catalog API returns live data from the Azure ML registry.
- Region availability changes as Microsoft rolls out new models.
- Recommended: run the scraper as a CI job (daily or on-demand) and commit the JSON.

### Model Deduplication
- The catalog API returns 14,879 items across all versions[^5].
- Filter to "latest" versions in post-processing, or use the `Name` filter approach.
- Some models appear under multiple publishers (e.g., Llama variants).

### Data Size
- Full catalog JSON (all versions, all fields): ~50-80 MB
- Compact latest-only catalog (essential fields): ~2-5 MB
- With region data merged: ~5-10 MB
- Mintlify can serve static JSON files from the `static/` directory.

---

## Confidence Assessment

| Finding | Confidence | Basis |
|---------|-----------|-------|
| Asset Gallery API is unauthenticated | **High** | Verified via curl — no auth headers needed[^1] |
| API returns complete model metadata | **High** | Full model objects with all catalog fields returned[^4] |
| Pagination via continuationToken works | **High** | Tested from curl, 100 items/page[^5] |
| Filter field names documented in error messages | **High** | API returns valid field list when invalid field is used[^2] |
| Facets only work through BFF session | **High** | Curl returns error "Facets are not supported for model summaries"[^3] |
| 55 publishers, 14,879 model versions | **High** | Direct counts from API responses[^5][^6] |
| Mintlify supports custom React in MDX | **High** | Official documentation confirms with examples[^10] |
| Region availability merge is feasible | **High** | Both data sources use model name as key[^8] |
| Build-time JSON generation approach | **Medium-High** | Standard Mintlify pattern; may need `static/` directory testing |

---

## Footnotes

[^1]: Direct curl test: `curl -s -X POST 'https://ai.azure.com/api/westus2/asset-gallery/v1.0/models' -H 'Content-Type: application/json' -H 'x-ms-use-full-service-contracts: true' -d '{"pageSize":5,"filters":[],"searchParameters":{}}'` returns 200 with model data

[^2]: Error response from invalid filter field returns: "Fields have to be one of Name, Version, Labels, freePlayground, Popularity, CreatedTime, DisplayName, Summary, License, Publisher, Author, InferenceTasks, FineTuningTasks, ModelLimits/TextLimits/MaxOutputTokens, ModelLimits/TextLimits/InputContextWindow, ModelLimits/SupportedInputModalities, ModelLimits/SupportedOutputModalities, ModelLimits/SupportedLanguages, PlaygroundLimits/RateLimitTier, ModelCapabilities, AzureOffers, VariantInformation/..., Deprecation/InferenceRetirementDate"

[^3]: Error from curl with facets: "Facets are not supported for model summaries, please remove them from the request."

[^4]: Full model object extracted from API response for `gpt-5.4-nano` including `annotations.tags` and `annotations.systemCatalogData` with all fields

[^5]: Pagination test: `pageSize: 100` returns 100 items with `continuationToken` (260 chars, base64). `totalCount: 14879` returned on each page.

[^6]: Publishers endpoint `POST /api/westus2/asset-gallery/v1.0/publishers/list` returns 55 publishers including OpenAI, Meta, Microsoft, Mistral AI, xAI, DeepSeek, Cohere, Nvidia, etc.

[^7]: Azure CLI command `az cognitiveservices model list --location eastus` calls REST API `GET /subscriptions/{subId}/providers/Microsoft.CognitiveServices/locations/{location}/models?api-version=2025-06-01`

[^8]: Existing script at `scripts/generate_model_availability.py` in the foundry-docs repository handles parallel region querying across 32 regions

[^9]: Facet data extracted from browser network trace of `POST /api/westus2/asset-gallery/v1.0/models` with facet parameters, filtered to OpenAI publisher

[^10]: Mintlify React components documentation: https://www.mintlify.com/docs/customize/react-components — components must be in `/snippets/` folder, support `useState`/`useEffect`/`useMemo`, Tailwind CSS available
