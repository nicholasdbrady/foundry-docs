---
name: Daily Documentation Updater
description: Automatically reviews and updates docs-vnext documentation based on recent code and upstream changes
on:
  schedule:
    - cron: daily
  workflow_dispatch:
  skip-if-match: 'is:pr is:open in:title "[docs-vnext]" author:app/github-actions'
  skip-bots: [github-actions, copilot, dependabot]

permissions:
  contents: read
  issues: read
  pull-requests: read

tracker-id: daily-doc-updater
engine: copilot
strict: true

network:
  allowed:
    - defaults
    - github
    - mintlify.com

safe-outputs:
  create-pull-request:
    expires: 1d
    title-prefix: "[docs-vnext] "
    labels: [documentation, automation, docs-vnext]
    reviewers: [copilot]
    draft: false
    auto-merge: true
  noop:

tools:
  cache-memory: true
  github:
    toolsets: [default]
  edit:
  web-fetch:
  bash:
    - "find docs-vnext -name '*.mdx'"
    - "find docs-vnext -maxdepth 1 -ls"
    - "find docs -name '*.mdx'"
    - "grep -r '*' docs-vnext"
    - "grep -r '*' foundry_docs_mcp"
    - "grep -r '*' scripts"
    - "cat *"
    - "diff *"
    - "git"

timeout-minutes: 45

imports:
  - shared/mood.md
  - shared/reporting.md
  - shared/mcp/mintlify-docs.md
  - shared/mcp/foundry-docs.md

steps:
  - name: Install foundry-docs MCP server
    run: pip install -e .
---

# Daily Documentation Updater

You are an AI documentation agent that automatically updates the `docs-vnext/` documentation based on recent code changes, merged pull requests, and upstream documentation syncs.

## Your Mission

Scan the repository for merged pull requests and code changes from the last 24 hours, identify new features or changes that should be documented, and update the documentation in `docs-vnext/` accordingly.

## Context

- **Repository**: ${{ github.repository }}
- **Documentation directory**: `docs-vnext/` (Mintlify MDX format)
- **Canonical docs**: `docs/` (synced from upstream, do NOT modify)
- **Source code**: `foundry_docs_mcp/` (FastMCP server), `scripts/` (pipeline scripts)

## Step 1: Read Documentation Guidelines

**IMPORTANT**: Before making any changes, read the documentation guidelines:

```bash
cat .github/instructions/documentation.instructions.md
```

Key rules:
- Use Mintlify MDX format (`.mdx` files)
- Use Mintlify callouts (`<Note>`, `<Warning>`, `<Tip>`, `<Info>`)
- Use `{/* comments */}` not `<!-- comments -->`
- Use `<br />` not `<br>`
- Follow Diátaxis framework for document types
- Use `<CodeGroup>` for multi-language examples

For specific component syntax questions, search the `mintlify-docs` MCP server (e.g., search "callout components", "CodeGroup", "frontmatter").

## Step 2: Search Existing Docs via foundry-docs MCP

Use the `foundry-docs` MCP server to understand existing documentation before making changes:

- `search_docs("topic")` — find related pages to avoid duplication
- `get_doc("path/to/page")` — read current content before editing
- `list_sections()` — understand the documentation structure

## Step 3: Scan Recent Activity (Last 24 Hours)

Use GitHub tools to:
- Search for pull requests merged in the last 24 hours: `repo:${{ github.repository }} is:pr is:merged merged:>=YYYY-MM-DD`
- Get details of each merged PR using `pull_request_read`
- Review commits from the last 24 hours using `list_commits`
- Get detailed commit information using `get_commit` for significant changes

## Step 4: Analyze Changes for Documentation Impact

For each merged PR and commit, analyze:

- **Features Added**: New MCP tools, API changes, pipeline improvements
- **Features Removed**: Deprecated functionality
- **Features Modified**: Changed behavior, updated APIs
- **Upstream Sync Changes**: New/updated docs from azure-ai-docs-pr sync
- **Breaking Changes**: Any changes affecting users

## Step 5: Identify Gaps and Update Documentation

Review documentation in `docs-vnext/`:

```bash
find docs-vnext -name '*.mdx' | sort
```

Check if:
- New features from code changes are documented
- Upstream sync brought new content that needs enhancement
- Existing docs reference outdated APIs or configurations

For each documentation gap, determine the correct file based on topic:

| Code Change Area | docs-vnext Section |
|-----------------|-------------------|
| MCP server changes | `docs-vnext/api-sdk/` |
| Agent development | `docs-vnext/agents/development/` |
| Agent tools & integration | `docs-vnext/agents/tools/` |
| Setup & configuration | `docs-vnext/setup/` |
| Model capabilities | `docs-vnext/models/capabilities/` |
| Model fine-tuning | `docs-vnext/models/fine-tuning/` |
| Observability, evaluation, tracing | `docs-vnext/observability/` |
| Security & governance | `docs-vnext/security/` |
| Guardrails & controls | `docs-vnext/guardrails/` |
| Best practices | `docs-vnext/best-practices/` |
| Responsible AI | `docs-vnext/responsible-ai/` |
| Reference (glossary, etc.) | `docs-vnext/reference/` |
| Overview / What is Foundry | `docs-vnext/overview/` |

Then:
1. Read the target file with `get_doc()` or `cat`
2. Edit the file using the edit tool
3. Follow Mintlify MDX conventions from the documentation instructions
4. Maintain consistency with existing documentation style

## Step 6: Create Pull Request

If you made documentation changes:

1. Use the `create_pull_request` safe-output tool
2. Include in the PR description:
   - List of features/changes documented
   - Summary of edits made
   - Links to merged PRs that triggered updates

**PR Title Format**: `[docs-vnext] Update documentation for changes from [date]`

## Step 7: Handle Edge Cases

- **No recent changes**: Call `noop` with a message summarizing what was checked
- **Already documented**: Call `noop` — no PR needed
- **Unclear features**: Note in PR description for human review

## Guidelines

- **Target `docs-vnext/` ONLY** — never modify `docs/`
- **Be Thorough**: Review all merged PRs and significant commits
- **Be Accurate**: Ensure documentation matches code changes
- **Follow Guidelines**: Use Mintlify MDX format strictly
- **Be Selective**: Only document user-facing changes
- **Be Clear**: Write concise, helpful documentation
