---
name: Docs-vnext Baseline Sync Summary
description: Optionally summarizes the latest independently retained docs-vnext sync manifest
on:
  workflow_dispatch:

permissions:
  contents: read
  actions: read

tools:
  bash:
    - "gh run list *"
    - "gh run download *"
    - "mkdir *"
    - "cat /tmp/gh-aw/agent/docs-vnext-sync-manifest.json"
  github:
    mode: gh-proxy
    toolsets: [actions]

network:
  allowed:
    - defaults
    - github

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

# Docs-vnext Baseline Sync Summary

Summarize the latest dry-run manifest retained by the independent
`docs-vnext-sync-manifest.yml` workflow.

## Process

1. Find the latest successful `docs-vnext-sync-manifest.yml` run:

   ```bash
   run_id=$(gh run list \
     --workflow docs-vnext-sync-manifest.yml \
     --status success \
     --limit 1 \
     --json databaseId \
     --jq '.[0].databaseId')
   ```

2. If no run exists, call `report_incomplete` and stop.
3. Download its retained artifact:

   ```bash
   mkdir -p /tmp/gh-aw/agent
   gh run download "$run_id" \
     --name "docs-vnext-sync-manifest-$run_id" \
     --dir /tmp/gh-aw/agent
   ```

4. Read `/tmp/gh-aw/agent/docs-vnext-sync-manifest.json` once.
5. Verify that it is valid JSON with `schemaVersion: 2`.
6. Call `noop` with the aggregate add, modify, remove, preserve, and conservative payload-byte totals.

## Important

- This optional workflow does not generate or retain the manifest.
- The independent host workflow remains durable even when gh-aw activation is skipped for daily AI-credit limits.
- Do not walk, hash, compare, or recalculate the documentation trees.
- The retained manifest is the complete source of truth for downstream synchronization work.
- If the manifest is missing, unreadable, or invalid, call `report_incomplete` and stop.
