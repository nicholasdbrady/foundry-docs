---
mcp-servers:
  foundry-docs:
    command: "foundry-docs"
    allowed: ["search_docs", "get_doc", "list_sections", "get_section"]
---

# Foundry Documentation MCP Server

This MCP server provides search access to the project's own Microsoft Foundry documentation (~267 pages).

## Available Tools

- `search_docs(query)` — Full-text search across all Foundry docs (returns ranked results with path, title, description, score)
- `get_doc(path)` — Retrieve full MDX content of a specific page by path
- `list_sections()` — List all documentation sections and page counts
- `get_section(section)` — List all pages in a specific section

## When to Use

- **Before writing content**: Search existing docs to avoid duplication and ensure consistency
- **Before editing a file**: Read the current content with `get_doc()` to understand context
- **Understanding structure**: Use `list_sections()` and `get_section()` to find the right location for content
- **Cross-referencing**: Search for related topics to add appropriate internal links

## Prerequisites

The server requires `pip install -e .` to be run first. Add this as a build step:

```yaml
steps:
  - name: Install foundry-docs MCP server
    run: pip install -e .
```
