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

## Pipeline Scripts

To regenerate the docs from upstream:

```bash
# 1. Extract manifest from TOC files
python scripts/extract_manifest.py

# 2. Download docs from GitHub
python scripts/download_docs.py

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

# Full rebuild when schema/chunking changes
python scripts/ingest_to_azure_search.py --recreate
```

### Ongoing automation

GitHub Actions workflow [.github/workflows/index-sync.yml](.github/workflows/index-sync.yml) runs incremental index sync on docs/code changes and supports manual full rebuild.

Required repository secrets:

- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_API_KEY`
- `AZURE_SEARCH_INDEX_NAME` (optional)
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_PROJECT_API_KEY`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`

## Attribution

Documentation content is derived from Microsoft's azure-ai-docs repository under CC BY 4.0. See [ATTRIBUTION.md](ATTRIBUTION.md).
