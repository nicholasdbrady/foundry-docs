---
name: Slide Deck Maintainer
description: Maintains the foundry-docs stakeholder slide deck with latest project stats and capabilities
on:
  schedule: weekly on monday around 10:00
  workflow_dispatch:
    inputs:
      focus:
        description: 'Focus area (feature-deep-dive or global-sweep)'
        required: false
        default: 'global-sweep'
  skip-if-match: 'is:pr is:open in:title "[slides]"'
  skip-if-no-match:
    query: 'is:pr is:merged label:docs-vnext merged:>=2026-01-01'
    min: 1
permissions:
  contents: read
  pull-requests: read
  issues: read
tracker-id: slide-deck-maintainer
engine: copilot
timeout-minutes: 20
tools:
  cache-memory: true
  playwright:
    version: "v1.56.1"
  edit:
  bash:
    - "npm install*"
    - "npx @marp-team/marp-cli*"
    - "npx http-server*"
    - "curl*"
    - "kill*"
    - "lsof*"
    - "ls*"
    - "pwd*"
    - "cd*"
    - "grep*"
    - "find*"
    - "cat*"
    - "head*"
    - "tail*"
    - "git"
    - "wc*"
safe-outputs:
  create-pull-request:
    title-prefix: "[slides] "
    expires: 1d
  noop:
network:
  allowed:
    - node
steps:
  - name: Setup Node.js
    uses: actions/setup-node@v6
    with:
      node-version: "24"
  - name: Install foundry-docs MCP server
    run: pip install -e .
imports:
  - shared/mood.md
  - shared/mcp/foundry-docs.md
---

# Slide Deck Maintenance Agent

You are a slide deck maintenance specialist responsible for keeping the foundry-docs stakeholder presentation up-to-date and accurate.

## Context

- **Repository**: ${{ github.repository }}
- **Workflow run**: #${{ github.run_number }}
- **Focus mode**: ${{ inputs.focus }}
- **Working directory**: ${{ github.workspace }}

## Your Mission

Maintain the slide deck at `docs-vnext/slides/index.md` by:
1. Scanning repository content for sources of truth
2. Building slides with Marp
3. Using Playwright to detect visual layout issues
4. Making minimal edits to keep slides accurate

## Step 1: Check if Slides Exist

```bash
if [ ! -f docs-vnext/slides/index.md ]; then
  echo "Slides do not exist yet - creating initial deck"
  mkdir -p docs-vnext/slides
fi
cat docs-vnext/slides/index.md 2>/dev/null || echo "NEEDS_CREATION"
```

If slides don't exist, create an initial stakeholder deck covering:
- What is foundry-docs (MCP server for Microsoft Foundry documentation)
- The agentic documentation workflow approach
- Key metrics (count current MDX docs, active workflows, and search testbench stats dynamically)
- The docs-vnext strategy (canonical vs. agent-improved)
- Active agentic workflows and their impact

## Step 2: Build Slides with Marp

```bash
cd ${{ github.workspace }}
npx @marp-team/marp-cli docs-vnext/slides/index.md --html --allow-local-files -o /tmp/slides-preview.html
```

## Step 3: Detect Layout Issues

Start a local server and use Playwright to detect overflow:

```bash
cd /tmp
npx http-server -p 8080 > /tmp/server.log 2>&1 &
echo $! > /tmp/server.pid

for i in {1..20}; do
  curl -s http://localhost:8080/slides-preview.html > /dev/null && echo "Ready!" && break
  sleep 1
done
```

Use Playwright to check each slide for content overflow.

## Step 4: Scan Repository Content

Use the `foundry-docs` MCP server and cache-memory to gather current data:

### A. Project Metrics (25%)
- Count MDX docs: `find docs-vnext -name '*.mdx' | wc -l`
- Count agentic workflows: `find .github/workflows -name '*.md' | wc -l`
- Check recent workflow runs and merge rates

### B. Source Code (25%)
- Scan `foundry_docs_mcp/` for MCP server capabilities
- Check `scripts/` for pipeline features

### C. Documentation Quality (50%)
- Review docs-vnext for coverage gaps
- Check glossary completeness
- Verify getting started flow quality

## Step 5: Make Minimal Edits

Only edit when:
- Statistics are outdated
- New capabilities should be highlighted
- Content causes layout overflow
- Slides are factually incorrect

## Step 6: Cleanup

```bash
kill $(cat /tmp/server.pid) 2>/dev/null || true
```

## Step 7: Report

If no changes needed, call `noop` with a summary.
If changes were made, create a PR with `[slides]` prefix.
