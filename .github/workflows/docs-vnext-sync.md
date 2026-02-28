---
name: Docs-vnext Baseline Sync
description: Refreshes docs-vnext from canonical docs as a weekly baseline
on:
  schedule:
    - cron: "0 18 * * 0"
  workflow_dispatch:
  skip-if-match: 'is:pr is:open in:title "[docs-vnext-sync]"'

permissions:
  contents: read

tools:
  bash:
    - "cp *"
    - "find *"
    - "diff *"
    - "git"

safe-outputs:
  create-pull-request:
    title-prefix: "[docs-vnext-sync] "
    labels: [documentation, docs-vnext, sync]
    expires: 3d
  noop:

engine: copilot
timeout-minutes: 10
---

# Docs-vnext Baseline Sync

Synchronize `docs-vnext/` from the canonical `docs/` directory as a weekly baseline refresh.

## Process

1. Copy all MDX files from `docs/` to `docs-vnext/`, preserving directory structure
2. Preserve any files unique to `docs-vnext/` (glossary, slides, README)
3. Commit changes if any upstream updates were detected

## Important

- This workflow refreshes the baseline content only
- Agent-created improvements (glossary, unbloated prose) in files unique to docs-vnext/ are preserved
- Files that exist in both directories are overwritten from the canonical source
- The `docs-vnext/README.md`, `docs-vnext/reference/glossary.mdx`, and `docs-vnext/slides/` are NOT overwritten
