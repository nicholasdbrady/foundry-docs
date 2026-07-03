# foundry-docs

A FastMCP server that provides searchable Microsoft Foundry documentation for AI assistants.

## Overview

This project extracts ~250 Microsoft Foundry docs from [MicrosoftDocs/azure-ai-docs](https://github.com/MicrosoftDocs/azure-ai-docs), converts them from Microsoft Learn markdown to Mintlify MDX format, and serves them via a [FastMCP](https://github.com/jlowin/fastmcp) server.

## Quick Start

```bash
# Install
pip install -e .

# Run the MCP server
foundry-docs
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_docs(query)` | Full-text search across all Foundry docs |
| `get_doc(path)` | Retrieve a specific doc by path |
| `list_sections()` | List all TOC sections and their pages |
| `get_section(section)` | List all docs in a specific section |
| `submit_search_feedback(...)` | Record failed/weak search cases for testbench generation |

When Azure Search variables are configured, `search_docs` uses hybrid retrieval
(keyword + vector + semantic reranking). Otherwise it falls back to local TF-IDF.

Both servers (`foundry_docs_mcp` over `docs/`, `foundry_docs_vnext_mcp` over
`docs-vnext/`) expose the same tool/resource/prompt surface — they differ only
in the content set and URI prefix, since both are built by
`foundry_docs_mcp._server_factory.build_server()`.

| Resource / template | Description |
|---|---|
| `docs://navigation` (`docs://vnext/navigation`) | Full Mintlify navigation JSON |
| `docs://page/{section}/{page}` | Read a page by section/page |
| `docs://page/{section}/{subsection}/{page}` | Read a nested page |

| Prompt | Description |
|---|---|
| `explain_foundry_concept(concept)` | Ground an explanation of a Foundry concept in the docs |
| `build_foundry_agent(agent_type, tools)` | Step-by-step agent-building guidance |
| `compare_foundry_options(option_a, option_b, context)` | Compare two Foundry options |

## Agent Readiness: MCP & Mintlify Discovery

This repo verifies its own agent-readiness surface deterministically instead of
relying on an LLM to "vibe-check" it. See `.github/agent-harness-map.md` for the
full harness routing and current known gaps.

**FastMCP server inspection (deterministic, in-memory, no LLM):**

```bash
pytest tests/test_mcp_server_inspection.py -v
```

Uses FastMCP's standard in-memory `Client(server)` testing pattern
(<https://gofastmcp.com/development/tests>) to assert tool/resource/prompt
inventories, schemas, and server metadata for both `foundry-docs` and
`foundry-docs-vnext`. This is the hard gate in
[`.github/workflows/mintlify-fastmcp-readiness.yml`](.github/workflows/mintlify-fastmcp-readiness.yml).

**MCP/tool discovery state report (local + hosted + Azure-backed):**

```bash
python scripts/check_mcp_discovery.py --output tests/eval_results/mcp_discovery.json
```

Reports, for each variant, only what was actually verified — it never
fabricates a "pass":

- **Local FastMCP** (`foundry-docs`, `foundry-docs-vnext`) — verified live via
  an in-memory client.
- **Hosted Mintlify MCP** (the docs-vnext site configured in `.mcp.json`) —
  live HTTP checks against `/mcp`, `/.well-known/mcp`,
  `/.well-known/mcp/server-card.json`, `/skill.md`, `/llms.txt`, and
  `/llms-full.txt`. As of this writing: `/mcp` responds `405` to a plain `GET`
  (present, POST-only streamable-HTTP transport); the other five endpoints
  return `200`. `mint score <url>` (Mintlify's hosted agent-readiness scoring)
  requires an authenticated Mintlify account (`mint login`) and is reported as
  **not configured** rather than guessed.
- **Azure-backed hybrid search** — reports whether `AZURE_SEARCH_ENDPOINT` /
  `AZURE_AI_PROJECT_ENDPOINT` are configured (env-var presence only; this does
  not make a live Azure call).

Pass a discovery JSON to `scripts/eval_report.py --mcp-discovery <path>` to
include an "MCP & Tool Discovery State" section in the eval report, alongside
the existing local/hosted-Mintlify/FastMCP/Azure-backed comparison rows.

**Mintlify CLI readiness (`mint validate`, `mint broken-links`, `mint a11y`):**

These must be run with `docs/` or `docs-vnext/` as the working directory —
running from the repo root picks up unrelated content (`raw_docs/`, `research/`,
etc.) via the root `docs.json`.

```bash
cd docs && npx --yes mint validate && npx --yes mint broken-links && npx --yes mint a11y
cd docs-vnext && npx --yes mint validate && npx --yes mint broken-links && npx --yes mint a11y
```

These run as informational (non-blocking) checks in
[`.github/workflows/mintlify-fastmcp-readiness.yml`](.github/workflows/mintlify-fastmcp-readiness.yml)
on docs changes and weekly — they report current state rather than gate merges,
since `docs/`/`docs-vnext/` content quality is owned by separate tranches. See
`.github/agent-harness-map.md` for currently known content gaps this surfaced.

## Azure Configuration

The server uses Azure AI Foundry project endpoints and the OpenAI Responses API
through the Foundry client wrapper.

Set these environment variables before running ingestion/search in Azure mode:

- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_API_KEY` (or RBAC)
- `AZURE_SEARCH_INDEX_NAME` (optional, default `foundry-docs`)
- `AZURE_AI_PROJECT_ENDPOINT` (required)
- `AZURE_AI_PROJECT_API_KEY` (optional; if omitted, `DefaultAzureCredential` is used)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (optional, default `text-embedding-3-small`)
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` (optional, enables query rewrite via Responses API)
- `FOUNDRY_RETRY_MAX_ATTEMPTS` (optional, default `5`)
- `FOUNDRY_RETRY_BASE_DELAY_S` (optional, default `0.5`)
- `FOUNDRY_RETRY_MAX_DELAY_S` (optional, default `8.0`)
- `FOUNDRY_RETRY_JITTER_RATIO` (optional, default `0.2`)
- `FOUNDRY_INGEST_MAX_CONCURRENCY` (optional, default `4`)
- `FOUNDRY_ADAPTIVE_THROTTLE_ENABLED` (optional, default `1`)
- `FOUNDRY_ADAPTIVE_THROTTLE_MAX_PAUSE_S` (optional, default `60`)

Transient OpenAI/Foundry/Azure Search calls now use exponential backoff with jitter and Retry-After support.
Ingestion also supports bounded parallel batching with shared adaptive throttling for 429-style pressure.

## Pipeline Scripts

To regenerate the docs from upstream:

```bash
# 1. Extract manifest from TOC files
python scripts/extract_manifest.py

# 2. Download docs from GitHub
python scripts/download_docs.py

# Force a fresh download of files that already exist in raw_docs/
python scripts/download_docs.py --force

# 3. Convert to Mintlify MDX
python scripts/convert_to_mdx.py

# 4. Build navigation config
python scripts/build_navigation.py

# 5. Ingest chunked docs into Azure AI Search
python scripts/ingest_to_azure_search.py

# 6. Build and run relevance testbench from feedback events
python scripts/build_testbench.py
python scripts/run_testbench.py
```

### Incremental indexing strategy

`scripts/ingest_to_azure_search.py` now performs hash-based incremental sync:

- Computes `content_hash` per chunk
- Reads existing `{chunk_id, content_hash}` metadata from Azure Search
- Embeds and upserts only new/changed chunks
- Deletes removed chunks

Useful modes:

```bash
# Normal incremental sync
python scripts/ingest_to_azure_search.py

# Preview changes only (no writes)
python scripts/ingest_to_azure_search.py --dry-run

# Bounded concurrent sync (use with service quotas in mind)
python scripts/ingest_to_azure_search.py --max-concurrency 4 --batch-size 100

# Full rebuild when schema/chunking changes
python scripts/ingest_to_azure_search.py --recreate
```

### Ongoing automation

GitHub Actions workflow [.github/workflows/index-sync.yml](.github/workflows/index-sync.yml) runs incremental index sync on docs/code changes and supports manual full rebuild.
The workflow defaults ingestion concurrency to `4` based on measured throughput in this repository.

GitHub Actions workflow [.github/workflows/testbench-regression.yml](.github/workflows/testbench-regression.yml) runs relevance regression checks against `tests/search_testbench.json` and enforces a pass-rate gate.

Required repository secrets:

- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_API_KEY`
- `AZURE_SEARCH_INDEX_NAME` (optional)
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_PROJECT_API_KEY`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`

For testbench regression workflow, use the same secrets above.

Default regression gate:

- `top-k`: 10
- `min-pass-rate`: 0.90
- `min-tests`: 1

## Attribution

Documentation content is derived from Microsoft's azure-ai-docs repository under CC BY 4.0. See [ATTRIBUTION.md](ATTRIBUTION.md).
