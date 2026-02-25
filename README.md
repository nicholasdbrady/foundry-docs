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
```

## Attribution

Documentation content is derived from Microsoft's azure-ai-docs repository under CC BY 4.0. See [ATTRIBUTION.md](ATTRIBUTION.md).
