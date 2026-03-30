# Copilot Instructions for foundry-docs

## Project overview

This repository is a **FastMCP MCP server** that extracts Microsoft Foundry documentation from the upstream `MicrosoftDocs/azure-ai-docs-pr` repo, converts it from Microsoft Learn markdown to **Mintlify MDX**, and serves it via two MCP servers:

- `foundry_docs_mcp` — serves `docs/` (primary content set)
- `foundry_docs_vnext_mcp` — serves `docs-vnext/` (A/B/C/D comparison variant)

Both servers are thin wrappers around `foundry_docs_mcp._server_factory.build_server()`, which accepts a `ServerConfig` dataclass to differentiate paths, env vars, and index names. The factory wires up lifespan-managed search indexes, Azure AI Search hybrid retrieval (when configured), and OpenTelemetry telemetry.

## Build, test, and lint

```bash
# Install (editable)
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file or class
pytest tests/test_chunker.py
pytest tests/test_chunker.py::TestMarkdownChunker

# Lint
ruff check .

# Lint with auto-fix
ruff check --fix .
```

Ruff line-length is set to **120** in `pyproject.toml`.

## Architecture

### Doc ingestion pipeline (`scripts/`)

A multi-step pipeline regenerates docs from upstream:

1. `extract_manifest.py` — parse TOC files into a manifest
2. `download_docs.py` — fetch raw docs from GitHub
3. `convert_to_mdx.py` — convert Microsoft Learn markdown → Mintlify MDX
4. `build_navigation.py` — generate `docs.json` / `docs-vnext/docs.json` nav config
5. `ingest_to_azure_search.py` — chunk docs, embed, and upsert into Azure AI Search (incremental hash-based sync)
6. `build_testbench.py` / `run_testbench.py` — build and run search relevance regression tests

### Search dual-mode

The server uses two search backends:

- **Local TF-IDF** (`SearchIndex` in `indexer.py`) — always loaded at startup from `.mdx` files on disk. Used as fallback.
- **Azure AI Search hybrid** (`AzureSearchIndex` in `indexer.py`) — keyword + vector + semantic reranking. Activated when `AZURE_SEARCH_ENDPOINT` is set. Uses `FoundryProjectOpenAI` (`foundry_client.py`) for embeddings and optional query rewriting via the OpenAI Responses API.

### Chunking

`chunker.py` splits MDX docs by heading structure (h2–h4) with sentence-boundary-aware overlap for long sections. Each chunk gets a base64-encoded deterministic ID derived from `doc_path#heading_slug#section_index-split_index`.

### Retry and throttling

`retry.py` provides `with_retry()` (exponential backoff + jitter + `Retry-After` header support) and `AdaptiveThrottle` (shared gate across concurrent workers for 429 back-pressure). All Azure Search and OpenAI calls go through `with_retry()`.

### Telemetry

`telemetry.py` emits OpenTelemetry spans/logs to Application Insights when `APPLICATIONINSIGHTS_CONNECTION_STRING` is set, and always appends search feedback to a local JSONL file for testbench generation.

### GitHub Actions workflows (`.github/aw/`)

Workflows are authored as `.md` files compiled by `gh-aw`. Key workflows:

- `index-sync.yml` — incremental Azure Search index sync on docs changes
- `testbench-regression.yml` — search relevance regression gate (default: 90% pass rate, top-k=10)
- `sync-and-convert.yml` — upstream doc sync pipeline

## Key conventions

### Python

- **Python 3.11+** required
- Use `from __future__ import annotations` for deferred type evaluation
- Use `dataclass(slots=True)` or `dataclass(frozen=True)` for data containers
- All retry-eligible calls must use `with_retry()` from `retry.py` — never bare `try/except` with manual sleep
- Environment config uses `_env_int()` / `_env_float()` helpers with sensible defaults, prefixed `FOUNDRY_`

### Documentation (docs-vnext/)

Full guidelines are in `.github/instructions/documentation.instructions.md`. Key points:

- **Mintlify MDX format** — use `<Note>`, `<Tip>`, `<Warning>`, `<Info>` callouts, not GitHub `> [!NOTE]` syntax
- **JSX comments** — `{/* comment */}`, not `<!-- comment -->`
- **Self-closing tags** — `<br />` not `<br>`
- Required frontmatter: `title` and `description`
- Multi-language code examples use `<CodeGroup>`
- Follow the **Diátaxis framework**: tutorials, how-to guides, reference, explanation — don't mix types
- Use neutral technical tone; avoid "we"/"our"; use ALL_CAPS placeholders (`YOUR_ENDPOINT`)
- Terminology: "Foundry resource" not "AI hub", "Agent" not "Bot", "Project endpoint" not "API key"
