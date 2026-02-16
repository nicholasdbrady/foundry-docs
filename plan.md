# foundry-docs-mcp: Microsoft Foundry Docs → Mintlify MDX + FastMCP Server

## Problem Statement

Extract ~268 "foundry" (not "foundry-classic") docs from `MicrosoftDocs/azure-ai-docs`, convert them from Microsoft Learn's custom markdown extensions to Mintlify MDX format, and serve them via a FastMCP server that provides searchable documentation context for AI assistants.

## Source Repo Analysis

| Attribute | Value |
|---|---|
| **Source** | `MicrosoftDocs/azure-ai-docs` (public, CC-BY-4.0) |
| **TOC root** | `articles/ai-foundry/default/toc.yml` (`monikerRange: 'foundry'`) |
| **Sub-TOC files** | 16 sections in `articles/ai-foundry/default/toc-files-foundry/` |
| **Top-level doc** | `articles/ai-foundry/what-is-foundry.md` |
| **Total docs** | ~268 .md files across multiple directories |
| **Include files** | `articles/ai-foundry/includes/` (~40+ files) |
| **Repo size** | ~3.3GB total (we only need a subset) |

### Doc locations span multiple directories:
- `articles/ai-foundry/` — main foundry docs, agents, observability, guardrails, control-plane, MCP, fine-tuning
- `articles/openai/` — Azure OpenAI docs (chat completions, responses API, content filters, fine-tuning, etc.)
- `articles/foundry-models/` — model catalog, deployment, endpoints
- `articles/agents/` — agent service docs (overview, hosted agents, tools)
- `articles/ai-services/` — cross-referenced Foundry Tools (speech, language, content safety)
- `articles/quickstarts/` — getting-started quickstart

### TOC Sections (16 sub-TOCs + 1 top-level):
1. What is Microsoft Foundry (top-level)
2. Get started (4 docs)
3. Agent development (~25 docs)
4. Agent tools & integration (~40 docs)
5. Model catalog (~25 docs)
6. Model capabilities (~50 docs)
7. Fine-tuning (~10 docs)
8. Manage agents, models, & tools (~12 docs)
9. Observability, evaluation, & tracing (~30 docs)
10. Developer experience (~12 docs)
11. API & SDK (~20 docs)
12. Guardrails and controls (~12 docs)
13. Responsible AI (~8 docs)
14. Best practices (~4 docs)
15. Setup & configure (~18 docs)
16. Security & governance (~18 docs)
17. Operate & support (~10 docs)

## MS Learn Markdown Extensions → Mintlify MDX Conversion Map

| MS Learn Syntax | Mintlify MDX Equivalent |
|---|---|
| `:::moniker range="foundry"` ... `:::moniker-end` | Keep content, strip markers |
| `:::moniker range="foundry-classic"` ... `:::moniker-end` | **Remove entire block** |
| `[!INCLUDE [name](path)]` | Inline the file content |
| `> [!TIP]` / `> [!NOTE]` / `> [!WARNING]` / `> [!IMPORTANT]` | `<Tip>`, `<Note>`, `<Warning>`, `<Warning>` |
| `> [!div class="nextstepaction"]` | `<Card>` or plain link |
| `:::image type="content" source="..." alt-text="...":::` | `<Frame><img src="..." alt="..." /></Frame>` |
| `# [Tab Title](#tab/id)` ... `---` | `<Tabs><Tab title="...">` ... `</Tab></Tabs>` |
| `:::zone pivot="programming-language-python"` | `<Tabs><Tab title="Python">` |
| `[!code-python[](~/path/file.py)]` | Inline fenced code block |
| YAML front matter (ms.author, ms.service, etc.) | Simplified: `title`, `description`, `sidebarTitle` |
| `?context=/azure/ai-foundry/context/context` | Strip query param, keep relative path or convert to learn.microsoft.com URL |
| `?view=foundry&preserve-view=true` | Strip query params |
| `/azure/path/to/doc` (absolute learn.microsoft.com refs) | `https://learn.microsoft.com/azure/path/to/doc` |

## Approach

### Phase 1: Extract & Catalog (~268 docs)
Build a Python script (`extract_manifest.py`) that:
1. Parses the root `toc.yml` and all 16 sub-TOC YAML files
2. Resolves every `href` relative path to an absolute repo path
3. Deduplicates (some docs appear in multiple TOC locations)
4. Categorizes each reference:
   - **In-repo .md** — needs download + conversion
   - **In-repo .yml** — FAQ/structured content, needs conversion
   - **External URL** — keep as-is (azure.microsoft.com, legal, etc.)
   - **Cross-repo /azure/...** — convert to learn.microsoft.com URL
5. Scans each doc for `[!INCLUDE]` refs and adds those to the manifest
6. Scans each doc for `:::image` refs and adds media files to the manifest
7. Outputs `manifest.json` with full file list, TOC hierarchy, and metadata

### Phase 2: Download & Organize
Build a Python script (`download_docs.py`) that:
1. Reads `manifest.json`
2. Downloads all in-repo .md, .yml, include, and media files via GitHub API (or sparse checkout)
3. Organizes into a Mintlify-friendly directory structure:
   ```
   docs/
   ├── get-started/
   ├── agents/
   │   ├── development/
   │   ├── tools/
   │   └── ...
   ├── models/
   │   ├── catalog/
   │   ├── capabilities/
   │   └── fine-tuning/
   ├── observability/
   ├── guardrails/
   ├── security/
   ├── api-sdk/
   ├── responsible-ai/
   ├── setup/
   ├── operate/
   └── images/
   ```
4. Creates a path mapping file (`path_map.json`) from old paths → new paths

### Phase 3: Convert to Mintlify MDX
Build a Python script (`convert_to_mdx.py`) that processes each .md file:
1. **Moniker filtering**: Parse `:::moniker range="..."` blocks; keep `foundry` content, remove `foundry-classic` blocks entirely
2. **Include resolution**: Inline all `[!INCLUDE [name](path)]` content recursively
3. **Front matter simplification**: Keep `title`, `description`; add `sidebarTitle`; strip MS-specific fields
4. **Callout conversion**: `> [!TIP]` → `<Tip>`, `> [!NOTE]` → `<Note>`, etc.
5. **Tab conversion**: `# [Tab Title](#tab/id)` ... `---` → `<Tabs>/<Tab>` components
6. **Image conversion**: `:::image` → `<Frame><img>` or standard markdown
7. **Zone pivot conversion**: `:::zone pivot="..."` → `<Tabs>` components
8. **Link rewriting**: Update internal links using `path_map.json`, externalize cross-repo refs
9. **Code include resolution**: Inline any `[!code-*]` file references
10. **Rename .md → .mdx**

### Phase 4: Build Mintlify Navigation
Build a Python script (`build_navigation.py`) that:
1. Reads the TOC YAML hierarchy
2. Maps to Mintlify `docs.json` `navigation` structure with groups/pages
3. Generates complete `docs.json` with theme, colors, navigation

### Phase 5: Build FastMCP Server
Create a Python FastMCP server (`foundry_docs_mcp/server.py`) that:
1. Loads all converted .mdx docs at startup
2. Builds a search index (text-based, possibly with TF-IDF or embeddings)
3. Exposes MCP tools:
   - `search_docs(query)` — full-text search across all docs
   - `get_doc(path)` — retrieve a specific doc by path
   - `list_sections()` — list all TOC sections and their pages
   - `get_section(section_name)` — list all docs in a section
4. Exposes MCP resources:
   - `docs://navigation` — the full navigation structure
   - `docs://page/{path}` — individual doc content

### Phase 6: Package & Repo Setup
1. Create private repo `nicholasdbrady/foundry-docs-mcp`
2. Project structure:
   ```
   foundry-docs-mcp/
   ├── docs/                    # Converted Mintlify MDX docs
   ├── docs.json                # Mintlify navigation config
   ├── scripts/
   │   ├── extract_manifest.py  # Phase 1
   │   ├── download_docs.py     # Phase 2
   │   ├── convert_to_mdx.py    # Phase 3
   │   └── build_navigation.py  # Phase 4
   ├── foundry_docs_mcp/
   │   ├── __init__.py
   │   ├── server.py            # FastMCP server
   │   └── indexer.py           # Search indexing
   ├── pyproject.toml
   ├── README.md
   ├── ATTRIBUTION.md           # CC-BY-4.0 attribution
   └── .github/
       └── workflows/
           └── sync-and-convert.yml  # Periodic upstream sync
   ```
3. Add CC-BY-4.0 attribution notice
4. GitHub Actions workflow for periodic re-sync and conversion

## Todos

1. **extract-manifest** — Parse all TOC YMLs, resolve paths, build manifest.json (~268 docs)
2. **download-docs** — Fetch all .md, .yml, includes, and media from GitHub
3. **convert-mdx** — Convert MS Learn markdown → Mintlify MDX (moniker filter, includes, callouts, tabs, images, links)
4. **build-navigation** — Convert TOC hierarchy → Mintlify docs.json
5. **build-mcp-server** — FastMCP server with search_docs, get_doc, list_sections, get_section tools
6. **create-repo** — Private repo nicholasdbrady/foundry-docs-mcp with full project structure
7. **add-sync-workflow** — GitHub Actions for periodic upstream re-sync + conversion
8. **attribution** — CC-BY-4.0 attribution notice (ATTRIBUTION.md)

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Docs reference files outside the repo (code samples in separate repos) | Missing code snippets | Replace with placeholder + link to source |
| Moniker filtering removes too much content | Sparse docs | Validate each doc has meaningful content post-filter |
| Relative path resolution is complex (3-4 levels of `../`) | Broken links | Build comprehensive path_map.json, validate all links |
| ~268 docs is a lot of conversion | Conversion errors | Build robust tests, validate a sample set first |
| Some TOC entries are .yml (FAQ pages) | Different format | Handle YAML-based structured content separately |
| Cross-repo `/azure/...` refs are learn.microsoft.com links | Can't be internalized | Convert to external URLs |

## Considerations

- **License**: CC-BY-4.0 allows this with attribution — ATTRIBUTION.md is required
- **No full repo mirror needed**: We only need ~268 specific files + includes + media, not the 3.3GB repo
- **Sparse checkout or API**: Use GitHub API to fetch individual files rather than cloning the entire repo
- **Existing fork**: `nicholasdbrady/azure-ai-docs` already exists as a public fork — could use as a read source
- **Conversion quality**: Start with a POC on one section (e.g., "Get started" — 4 docs) to validate the conversion pipeline before running on all 268 docs
