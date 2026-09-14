# Reverse Engineering: https://model-availability.azurewebsites.net/

## Executive Summary

The Azure OpenAI Model Regional Availability website is a **Python Flask application** served by **gunicorn**, hosted on **Azure App Service**. It has no external API calls from the browser — all data is pre-rendered server-side from markdown files and served as HTML table fragments via simple same-origin AJAX GET requests. The frontend is a minimal jQuery 1.10.2 + Bootstrap app. Telemetry flows to **Azure Application Insights** in the Central US region. The underlying data source is strongly correlated with the `model-matrix` markdown files maintained in the public [MicrosoftDocs/azure-ai-docs](https://github.com/MicrosoftDocs/azure-ai-docs) GitHub repository.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         BROWSER (Client)                         │
│                                                                  │
│  ┌────────────┐   jQuery $.ajax()    ┌─────────────────────┐    │
│  │  index.html │ ──── GET /sku ────▶ │  Same-origin server │    │
│  │  (jQuery +  │ ◀── HTML table ──── │  (no external API)  │    │
│  │  Bootstrap) │                     └─────────────────────┘    │
│  └─────┬──────┘                                                  │
│        │                                                         │
│        │  POST /v2/track (telemetry)                             │
│        ▼                                                         │
│  ┌─────────────────────────────────────────┐                    │
│  │  Application Insights SDK (ai.3.gbl.js) │                    │
│  └──────────────┬──────────────────────────┘                    │
└─────────────────┼────────────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────┐
│  centralus-0.in.applicationinsights.azure.com│
│  (Azure Monitor telemetry ingestion)         │
│  iKey: d1a4755f-6372-4086-9d2b-04b1b8b43d2c │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    AZURE APP SERVICE (Server)                     │
│          model-availability.azurewebsites.net                     │
│                                                                  │
│  ┌──────────┐     ┌──────────────────────┐                      │
│  │ gunicorn │────▶│  Flask Application   │                      │
│  │  (WSGI)  │     │                      │                      │
│  └──────────┘     │  Routes:             │                      │
│                   │  GET /               │  → index.html         │
│                   │  GET /{sku_name}     │  → HTML table frag   │
│                   │  GET /download_      │                      │
│                   │    unified_markdown  │  → .md file download  │
│                   │                      │                      │
│                   │  Reads from:         │                      │
│                   │  Pre-generated       │                      │
│                   │  markdown → HTML     │                      │
│                   └──────────┬───────────┘                      │
│                              │                                   │
│                              ▼                                   │
│                   ┌──────────────────────┐                      │
│                   │  Markdown data files │                      │
│                   │  (server-side disk)  │                      │
│                   │                      │                      │
│                   │  Same structure as:  │                      │
│                   │  MicrosoftDocs/      │                      │
│                   │  azure-ai-docs/      │                      │
│                   │  model-matrix/       │                      │
│                   └──────────────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Backend Technology Stack

| Component | Technology | Evidence |
|-----------|-----------|----------|
| **Web Server** | gunicorn | `Server: gunicorn` response header[^1] |
| **Framework** | Flask (Python) | Flask-style 404 page: `<!doctype html><html lang=en><title>404 Not Found</title>...`[^2] |
| **Hosting** | Azure App Service (Linux) | `*.azurewebsites.net` domain + `ARRAffinity` cookie for instance pinning[^3] |
| **Static files** | Flask `static/` convention | `/static/content/style.css`, `/static/scripts/jquery-1.10.2.min.js`[^4] |
| **Frontend** | jQuery 1.10.2 + Bootstrap | Loaded via `<script>` and `<link>` tags[^4] |
| **Telemetry** | Azure Application Insights SDK v3.3.11 | `ai.3.gbl.min.js` loaded from `js.monitor.azure.com`[^5] |

---

## Network Traffic Analysis

### Outbound Requests (from browser)

All API calls are **same-origin** — the browser makes **zero cross-origin data requests**. The only external calls are:

| # | Request | Type | Purpose |
|---|---------|------|---------|
| 1 | `GET /` | Document | Initial HTML page load |
| 2 | `GET /globalstandard` | XHR (jQuery.ajax) | Default SKU data table (HTML fragment) |
| 3 | `GET /static/content/bootstrap.min.css` | CSS | Styling |
| 4 | `GET /static/content/style.css` | CSS | Custom dark-theme styling |
| 5 | `GET /static/scripts/jquery-1.10.2.min.js` | Script | jQuery library |
| 6 | `GET https://js.monitor.azure.com/scripts/b/ai.3.gbl.min.js` | Script | Application Insights SDK[^5] |
| 7 | `GET https://js.monitor.azure.com/scripts/b/ai.config.1.cfg.json` | Fetch | App Insights config |
| 8 | `POST https://centralus-0.in.applicationinsights.azure.com/v2/track` | XHR | Telemetry (pageviews, performance)[^6] |

**Key finding**: There is **no external API** being called for data. All model availability data is served by the Flask backend itself at same-origin paths.

---

## Complete API Endpoint Map

### Data Endpoints (all return HTML table fragments)

These are the 13 SKU endpoints discovered from the DOM's `data-value` attributes on `.sku-option` elements[^7]:

| Endpoint | SKU Label | HTTP Methods | Response Size |
|----------|-----------|-------------|---------------|
| `GET /standard` | Standard | HEAD, OPTIONS, GET | ~9.2 KB |
| `GET /globalstandard` | Global Standard | HEAD, OPTIONS, GET | ~36.2 KB |
| `GET /datazonestandard` | Data Zone Standard | HEAD, OPTIONS, GET | ~8.8 KB |
| `GET /globalbatch` | Global Batch | HEAD, OPTIONS, GET | ~6.5 KB |
| `GET /datazonebatch` | Data Zone Batch | HEAD, OPTIONS, GET | ~3.7 KB |
| `GET /provisioned` | Provisioned | HEAD, OPTIONS, GET | ~9.8 KB |
| `GET /globalprovisionedmanaged` | Global Provisioned Managed | HEAD, OPTIONS, GET | ~11.7 KB |
| `GET /datazoneprovisioned` | Data Zone Provisioned | HEAD, OPTIONS, GET | ~5.5 KB |
| `GET /standardfinetune` | Fine-tuning Standard | HEAD, OPTIONS, GET | ~1.0 KB |
| `GET /globalstandardfinetune` | Fine-tuning Global Standard | HEAD, OPTIONS, GET | ~4.9 KB |
| `GET /developertier` | Fine-tuning Developer Tier | HEAD, OPTIONS, GET | ~3.9 KB |
| `GET /priorityglobalstandard` | Priority Global Standard | HEAD, OPTIONS, GET | ~3.7 KB |
| `GET /prioritydatazonestandard` | Priority Data Zone Standard | HEAD, OPTIONS, GET | ~1.2 KB |

### File Download Endpoint

| Endpoint | Purpose | Content-Type |
|----------|---------|-------------|
| `GET /download_unified_markdown` | Download all data as a single markdown file | `application/octet-stream` (~544 KB)[^8] |

The download endpoint serves a file named `unified_markdown.md` which contains **28 markdown table sections** covering all SKUs and capability types[^9].

### Response Format

Each SKU endpoint returns a **complete HTML fragment** (not JSON) containing:
- A `<head>` tag linking to the stylesheet
- A `<table>` with class `dark-theme` containing:
  - Row 1: Model names (some with `colspan` for multi-version models)
  - Row 2: Version dates
  - Body rows: One per Azure region, with ✅ or `-` indicators[^10]

Example response structure:
```html
<head><link rel="stylesheet" type="text/css" href="/static/content/style.css"></head>
<table border="1" class="dark-theme">
  <thead>
    <tr>
      <th>Region</th>
      <th>gpt-5.4-mini</th>
      <th colspan="2">gpt-5.2-chat</th>
      ...
    </tr>
    <tr>
      <th>Version</th>
      <th>2026-03-17</th>
      <th>2026-02-10</th>
      <th>2025-12-11</th>
      ...
    </tr>
  </thead>
  <tbody>
    <tr><td>eastus</td><td>✅</td><td>✅</td>...</tr>
    ...
  </tbody>
</table>
```

---

## Frontend JavaScript Architecture

The frontend is entirely contained in **two inline `<script>` blocks**[^11]:

### Script 0: Application Insights Instrumentation
- Standard Azure Application Insights bootstrap snippet (minified)
- Connection string: `InstrumentationKey=d1a4755f-6372-4086-9d2b-04b1b8b43d2c;IngestionEndpoint=https://centralus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://centralus.livediagnostics.monitor.azure.com/`[^5]

### Script 1: Application Logic
The entire app logic fits in a single inline script with these key functions:

| Function | Purpose |
|----------|---------|
| `changeContent(page)` | Core data loader — calls `$.ajax({ url: page, type: "GET" })` and injects response HTML into `#displayArea`[^12] |
| `buildModelSelector()` | Parses the loaded table headers to build model filter checkboxes |
| `buildRegionSelector()` | Parses table body to build region filter checkboxes |
| `applyFilters()` | Client-side column/row visibility toggling (CSS `display: none`) |
| `toggleSkuSelector()` | Opens/closes the SKU dropdown |
| `downloadLatestLogs()` | Fetches `/download_unified_markdown` and triggers browser download[^13] |
| `filterDropdownList()` | Search-as-you-type filtering within dropdowns |

**Data flow on page load**:
1. `$(document).ready()` calls `changeContent('/globalstandard')`[^12]
2. jQuery AJAX fetches the HTML table from the server
3. HTML is injected into `#displayArea` via `.html()`
4. `buildModelSelector()` and `buildRegionSelector()` parse the table DOM to populate filter UI
5. `applyFilters()` applies any active filters

**Data flow on SKU change**:
1. User clicks a `.sku-option` div
2. Click handler reads `data-value` attribute (e.g., `/provisioned`)
3. Calls `changeContent(value)` which fetches new table HTML
4. Steps 3-5 from above repeat

---

## Telemetry Details

### Application Insights Configuration[^5][^6]

| Property | Value |
|----------|-------|
| Instrumentation Key | `d1a4755f-6372-4086-9d2b-04b1b8b43d2c` |
| Ingestion Endpoint | `https://centralus-0.in.applicationinsights.azure.com/` |
| Live Endpoint | `https://centralus.livediagnostics.monitor.azure.com/` |
| SDK Version | `javascript:3.3.11` |
| Snippet Version | `7` |

### Telemetry Events Sent

The App Insights SDK sends two types of telemetry to `centralus-0.in.applicationinsights.azure.com/v2/track`:

1. **PageviewData** — page title, URL, duration
2. **PageviewPerformanceData** — detailed timing breakdown (network, request, response, DOM processing)[^6]

---

## Data Source Analysis

### Unified Markdown Sections

The `/download_unified_markdown` endpoint serves a file containing 28 markdown table sections[^9]:

```
ProvisionedManaged_Chat_Completions.md
DataZoneStandard_Chat_Completions.md
GlobalBatch_Chat_Completions.md
model_metadata.md
GlobalProvisionedManaged_Chat_Completions.md
DataZoneStandard.md
Standard_Image_Generation.md
DataZoneProvisionedManaged_Chat_Completions.md
GlobalStandard_Chat_Completions.md
DeveloperTier.md
GlobalStandard_Embeddings.md
GlobalStandard_Audio.md
Standard.md
Standard_Embeddings.md
Standard_Chat_Completions.md
DataZoneBatch.md
GlobalStandardFineTune.md
DataZoneProvisionedManaged.md
ProvisionedManaged.md
DataZoneStandard_Embeddings.md
StandardFineTune.md
PriorityGlobalStandard.md
PriorityDataZoneStandard.md
GlobalProvisionedManaged.md
GlobalStandard.md
DataZoneBatch_Chat_Completions.md
GlobalBatch.md
Standard_Audio.md
```

### Correlation with Azure AI Docs Repository

The data structure closely mirrors the **model-matrix** include files in [MicrosoftDocs/azure-ai-docs](https://github.com/MicrosoftDocs/azure-ai-docs)[^14]:

| Website Endpoint | Unified MD Section | Docs Repo File |
|-----------------|-------------------|----------------|
| `/globalstandard` | `GlobalStandard.md` | `model-matrix/standard-global.md` |
| `/standard` | `Standard.md` | `model-matrix/standard-models.md` |
| `/provisioned` | `ProvisionedManaged.md` | `model-matrix/provisioned-models.md` |
| `/globalprovisionedmanaged` | `GlobalProvisionedManaged.md` | `model-matrix/provisioned-global.md` |
| `/globalbatch` | `GlobalBatch.md` | `model-matrix/global-batch.md` |
| `/datazonebatch` | `DataZoneBatch.md` | `model-matrix/global-batch-datazone.md` |
| `/datazonestandard` | `DataZoneStandard.md` | `model-matrix/datazone-standard.md` |
| `/datazoneprovisioned` | `DataZoneProvisionedManaged.md` | `model-matrix/datazone-provisioned-managed.md` |
| `/priorityglobalstandard` | `PriorityGlobalStandard.md` | `model-matrix/standard-global-priority-processing.md` |
| `/prioritydatazonestandard` | `PriorityDataZoneStandard.md` | `model-matrix/datazone-standard-priority-processing.md` |

The docs repo files live at: `articles/foundry/openai/includes/model-matrix/`[^14]

### model_metadata.md Section

The unified markdown includes a `model_metadata.md` section with ~120 rows of model metadata including[^15]:
- Model name, version, lifecycle status
- Capability flags (chatCompletion, embeddings, audio, realtime, imageGenerations, etc.)
- Rate limits per SKU tier (Standard, GlobalStandard, DataZoneStandard, DeveloperTier)
- Fine-tuning configuration parameters
- Token limits, context windows, and output limits
- Retirement dates and deprecation status

This metadata is more detailed than what the public docs contain and likely comes from an internal model registry/configuration system.

---

## Azure App Service Infrastructure

### Hosting Evidence

| Signal | Value | Implication |
|--------|-------|-------------|
| Domain | `*.azurewebsites.net` | Azure App Service |
| ARRAffinity cookie | `e9cd5ec577e988e...` | Multi-instance App Service with sticky sessions[^3] |
| Server header | `gunicorn` | Python WSGI server |
| 404 format | Flask default HTML | Flask web framework[^2] |
| Static files | `/static/` path convention | Flask default static folder[^4] |
| Response times | 48-69ms (from browser) | Pre-rendered content, not computed on-the-fly |
| `download_unified_markdown` ETag | `"1775666705.1721544-544500-2959610287"` | Unix timestamp-based, indicating file serving[^8] |
| `download_unified_markdown` Last-Modified | `Wed, 08 Apr 2026 16:45:05 GMT` | File was recently updated/regenerated[^8] |

### Interesting HTML Comments

The source contains commented-out alternative titles suggesting a planned rebrand[^16]:
```html
<!--<title>Foundry Model Regional Availability</title>-->
<!--<h1>Foundry Model Regional Availability</h1>-->
```

This aligns with Microsoft's rebranding of "Azure AI" to "Microsoft Foundry".

---

## What the Site Does NOT Do

1. **No external API calls for data** — All availability data is served from the Flask backend itself
2. **No authentication** — Completely public, no login required
3. **No client-side data transformation** — Server returns pre-rendered HTML tables
4. **No WebSocket connections** — Purely HTTP request/response
5. **No localStorage/sessionStorage usage** — No client-side state persistence
6. **No service workers** — No offline capability
7. **No CORS headers** — Same-origin only (except telemetry)

---

## Confidence Assessment

| Finding | Confidence | Basis |
|---------|-----------|-------|
| Flask + gunicorn backend | **High** | Server header + 404 page format are definitive |
| Azure App Service hosting | **High** | Domain, ARRAffinity cookie are definitive |
| All data served same-origin | **High** | Complete network trace shows no external data APIs |
| Application Insights telemetry | **High** | SDK loaded, connection string visible, POST requests observed |
| Data sourced from markdown files | **High** | ETag/Last-Modified on download endpoint, naming patterns match docs repo |
| Correlation with MicrosoftDocs/azure-ai-docs | **Medium-High** | File naming patterns match closely; exact pipeline from repo to site is inferred |
| No public source repository | **High** | Searched GitHub extensively — no matching repo found |
| Periodic data refresh mechanism | **Medium** | Last-Modified header was very recent (3 min before request), suggesting automated updates |

---

## Footnotes

[^1]: HTTP response header `Server: gunicorn` observed on all responses from `model-availability.azurewebsites.net`

[^2]: 404 responses return `<!doctype html><html lang=en><title>404 Not Found</title><h1>Not Found</h1><p>The requested URL was not found on the server...` — this is the default Flask 404 template

[^3]: `curl -sI` reveals `Set-Cookie: ARRAffinity=e9cd5ec577e988e26c6aeea6b26633bcce9c726369b3780126ec189abfe4b215;Path=/;HttpOnly;Secure;Domain=model-availability.azurewebsites.net` — Azure App Service Application Request Routing affinity cookie

[^4]: Page source `<head>` section loads `/static/content/bootstrap.min.css`, `/static/content/style.css`, `/static/scripts/jquery-1.10.2.min.js`

[^5]: Application Insights connection string extracted from inline script: `InstrumentationKey=d1a4755f-6372-4086-9d2b-04b1b8b43d2c;IngestionEndpoint=https://centralus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://centralus.livediagnostics.monitor.azure.com/`

[^6]: Network trace shows `POST https://centralus-0.in.applicationinsights.azure.com/v2/track` with JSON body containing `PageviewData` and `PageviewPerformanceData` telemetry events

[^7]: HTML source contains `<div class="sku-option" data-value="/globalstandard">Global Standard</div>` and 12 other similar elements defining all available endpoints

[^8]: Response headers from `/download_unified_markdown`: `Content-Disposition: attachment; filename=unified_markdown.md`, `Content-Length: 544500`, `ETag: "1775666705.1721544-544500-2959610287"`, `Last-Modified: Wed, 08 Apr 2026 16:45:05 GMT`

[^9]: Unified markdown file contains 28 `## SectionName.md` headings extracted via regex match on the full downloaded content

[^10]: Response body from `/globalstandard` starts with `<head><link rel="stylesheet"...></head><table border="1" class="dark-theme"><thead>...` containing model availability data in ✅/- format

[^11]: Page source contains exactly 2 inline `<script>` blocks (no `src` attribute): Script 0 = App Insights bootstrap, Script 1 = all application logic

[^12]: JavaScript function `changeContent(page)` uses `$.ajax({ url: page, type: "GET", success: function(response) { $("#displayArea").html(response); ... } })` — discovered via DOM extraction of inline scripts

[^13]: JavaScript function `downloadLatestLogs()` uses `$.ajax({ url: '/download_unified_markdown', type: "GET", ... })` with blob download pattern

[^14]: [MicrosoftDocs/azure-ai-docs](https://github.com/MicrosoftDocs/azure-ai-docs) repository, path `articles/foundry/openai/includes/model-matrix/` contains: `standard-global.md`, `standard-models.md`, `provisioned-models.md`, `provisioned-global.md`, `global-batch.md`, `global-batch-datazone.md`, `datazone-standard.md`, `datazone-provisioned-managed.md`, `standard-global-priority-processing.md`, `datazone-standard-priority-processing.md`

[^15]: `model_metadata.md` section in unified markdown contains a wide table with 120 rows and 40+ columns including: Model Name, Version, Lifecycle Status, capability flags, rate limits, token limits, and retirement dates

[^16]: HTML comments in page source: `<!--<title>Foundry Model Regional Availability</title>-->` and `<!--<h1>Foundry Model Regional Availability</h1>-->`
