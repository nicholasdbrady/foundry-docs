---
name: Post-Sync Unbloat
description: Triggers documentation unbloating after the weekly docs-vnext baseline sync completes
on:
  workflow_run:
    workflows: ["Docs-vnext Baseline Sync"]
    types: [completed]
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: read
  issues: read

strict: true

engine: copilot

imports:
  - shared/mood.md
  - shared/reporting.md
  - shared/mcp/mintlify-docs.md

network:
  allowed:
    - defaults
    - github
    - mintlify.com

tools:
  cache-memory: true
  github:
    toolsets: [default]
  edit:
  web-fetch:
  bash:
    - "find docs-vnext -name '*.mdx'"
    - "wc -l *"
    - "grep -n *"
    - "git"
    - "cat *"
    - "head *"
    - "tail *"

safe-outputs:
  create-pull-request:
    expires: 2d
    title-prefix: "[docs-vnext] "
    labels: [documentation, automation, docs-vnext, unbloat]
    reviewers: [copilot]
    draft: true
    auto-merge: true
    fallback-as-issue: false
  noop:

timeout-minutes: 30
---

# Post-Sync Unbloat

You run automatically after the "Docs-vnext Baseline Sync" workflow completes. The sync just refreshed `docs-vnext/` from the canonical `docs/`, so there may be new verbose content to compress.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: docs-vnext baseline sync just completed

## Step 1: Identify New Content from Sync

Check which files were refreshed by the sync:

```bash
git log --oneline -3
git diff --stat HEAD~1 -- docs-vnext/
```

## Step 2: Find Bloated Files

From the synced files, find candidates for unbloating:

```bash
find docs-vnext -name '*.mdx' -exec wc -l {} + | sort -rn | head -20
```

Choose ONE file that:
- Was refreshed by the sync (appears in recent diff)
- Has high line count
- Has NOT been recently cleaned (check cache)

## Step 3: Read Documentation Guidelines

```bash
cat .github/instructions/documentation.instructions.md
```

## Step 4: Unbloat the File

Apply the same unbloating rules as the daily unbloat workflow:
- Consolidate bullet points into prose or tables
- Eliminate duplicate content
- Condense verbose descriptions
- Simplify redundant code examples

**DO NOT REMOVE** essential content, links, code examples, warnings, or frontmatter.

## Step 5: Create PR or Noop

If improvements were made, create a PR. If the synced content is already lean, call `noop`.

## Guidelines

- Focus on files that were just synced — they're the ones most likely to have upstream verbosity
- One file per run for quality control
- Preserve all essential information
- Target `docs-vnext/` ONLY
