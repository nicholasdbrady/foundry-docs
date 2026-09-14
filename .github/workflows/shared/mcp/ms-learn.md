---
mcp-servers:
  microsoft-learn:
    url: "https://learn.microsoft.com/api/mcp"
    allowed: ["*"]
---

# Microsoft Learn MCP Server

The `microsoft-learn` MCP server (configured above) provides search access to
Microsoft's official Learn documentation platform. It covers Azure AI Foundry,
Azure AI Services, Azure OpenAI, and all other Microsoft product documentation
published on learn.microsoft.com.

## Available Tools

The server exposes tools (prefixed `MicrosoftDocs_`) for searching and retrieving
content from the Microsoft Learn corpus. Use these to look up official API references,
service documentation, quickstarts, and conceptual articles.

## When to Use

Use this server **before making changes to docs-vnext** to compare your draft content
against the canonical Microsoft Learn source. This ensures accuracy and alignment with
official documentation:

- **Fact-checking**: Verify parameter names, default values, API signatures, and
  service limits against the official docs.
- **Content alignment**: Confirm that concepts, terminology, and recommended practices
  in docs-vnext match what Microsoft publishes.
- **Gap analysis**: Identify topics covered on Learn that are missing or incomplete
  in docs-vnext.

## Eval Harness: Control A

This is the same data source used as **"Control A"** in the eval harness
(`scripts/run_docs_eval.py`). The eval compares answers from the docs-vnext corpus
against answers sourced from Microsoft Learn to measure documentation quality. When
reviewing eval results, queries answered by the `microsoft-learn` source represent
the official baseline.
