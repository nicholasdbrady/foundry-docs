---
name: Docs-vnext Baseline Sync
description: Produces a deterministic dry-run manifest for the docs-vnext baseline
on:
  schedule: weekly on sunday
  workflow_dispatch:

permissions:
  contents: read

steps:
  - name: Generate deterministic docs-vnext sync manifest
    run: |
      set -euo pipefail
      mkdir -p /tmp/gh-aw/agent
      python3 scripts/generate_docs_vnext_sync_manifest.py \
        --source-dir docs \
        --target-dir docs-vnext \
        --allowlist .github/docs-vnext-sync-preserve.json \
        --output /tmp/gh-aw/agent/docs-vnext-sync-manifest.json
  - name: Retain docs-vnext sync manifest
    uses: actions/upload-artifact@v7.0.1
    with:
      name: docs-vnext-sync-manifest-${{ github.run_id }}
      path: /tmp/gh-aw/agent/docs-vnext-sync-manifest.json
      if-no-files-found: error
      retention-days: 30

tools:
  bash:
    - "cat /tmp/gh-aw/agent/docs-vnext-sync-manifest.json"

safe-outputs:
  report-incomplete:
  noop:
    report-as-issue: false

engine: copilot
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
timeout-minutes: 10
---

# Docs-vnext Baseline Sync

Review the deterministic dry-run synchronization manifest generated before agent execution.

## Process

1. Read `/tmp/gh-aw/agent/docs-vnext-sync-manifest.json` once.
2. Verify that it is valid JSON with `schemaVersion: 1`.
3. Call `noop` with the aggregate add, modify, remove, preserve, and payload-byte totals.

## Important

- This workflow is a dry run. Do not modify files or create a pull request.
- Do not walk, hash, compare, or recalculate the documentation trees.
- The retained manifest is the complete source of truth for downstream synchronization work.
- If the manifest is missing, unreadable, or invalid, call `report_incomplete` and stop.
