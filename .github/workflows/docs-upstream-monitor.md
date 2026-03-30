---
name: Upstream Docs Monitor
description: Monitors azure-ai-docs-pr for changes to Foundry documentation and triggers sync when detected
on:
  schedule: every 12h
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
tracker-id: docs-upstream-monitor

tools:
  cache-memory: true
  repo-memory:
    branch-name: memory/doc-metrics
    file-glob: ["*.json", "*.txt"]
    allowed-extensions: [".json", ".txt", ".md"]
    max-file-size: 524288
  github:
    toolsets: [default]
  bash:
    - "cat *"
    - "grep *"
    - "date *"
    - "echo *"

safe-outputs:
  create-issue:
    title-prefix: "[upstream-docs] "
    labels: [upstream-sync, automation]
    expires: 2d
    close-older-issues: true
  dispatch-workflow:
    workflows: ["sync-and-convert"]
    max: 1
  noop:

network:
  allowed:
    - defaults
    - github

imports:
  - shared/mood.md
  - shared/reporting.md

timeout-minutes: 10
---

# Upstream Docs Monitor

You monitor the upstream documentation repository (`MicrosoftDocs/azure-ai-docs-pr`) for changes to Foundry documentation under `articles/foundry/`. When changes are detected, you dispatch the sync-and-convert workflow and create a summary issue.

## Context

- **Repository**: ${{ github.repository }}
- **Upstream repo**: `MicrosoftDocs/azure-ai-docs-pr`
- **Upstream path**: `articles/foundry/**`
- **MS Learn refresh cadence**: 4x/day from azure-ai-docs-pr main

## Step 1: Load Persisted State

```bash
cat /tmp/gh-aw/repo-memory/default/upstream-docs-state.txt 2>/dev/null || cat /tmp/gh-aw/cache-memory/upstream-docs-state.txt 2>/dev/null || echo "No cached state — first run"
```

## Step 2: Check Upstream Commits

Use the GitHub MCP tools to list recent commits on `MicrosoftDocs/azure-ai-docs-pr` (main branch). Fetch the last 30 commits.

For each commit:
1. Check if the commit message or PR title mentions "foundry" (case-insensitive)
2. If possible, check if the commit's changed files include paths under `articles/foundry/`

## Step 3: Filter for Foundry Changes

From the recent commits, identify those that:
- Modified files under `articles/foundry/`
- Were PR merges (not direct pushes) — look for "Merge pull request" prefix
- Occurred after the last cached check timestamp

## Step 4: Compare with Cache

Read the cached `last_commit_sha` and `last_check_time`. Determine if there are new Foundry-relevant commits since the last check.

## Step 5: Report or Noop

### If New Foundry Changes Detected

Create an issue summarizing what changed:

```markdown
### 📄 Upstream Foundry Docs Changes Detected

### Summary

**Changes since last check**: N commits affecting `articles/foundry/`
**Time range**: YYYY-MM-DD HH:MM to YYYY-MM-DD HH:MM UTC

### Changed Files

<details>
<summary><b>Commits touching articles/foundry/ (N)</b></summary>

| Commit | Author | Description |
|--------|--------|-------------|
| `abc1234` | @author | PR title or commit message |

</details>

### Recommended Action

The sync-and-convert workflow has been dispatched to pull these changes.
```

Also dispatch the `sync-and-convert` workflow:
```json
{"dispatch-workflow": {"workflow": "sync-and-convert.yml"}}
```

### If No Changes

```json
{"noop": {"message": "No new Foundry docs changes in azure-ai-docs-pr. Last check: TIMESTAMP. Reviewed N commits."}}
```

## Step 6: Update Persisted State

Write to both repo memory (durable) and cache memory (backward compatibility):

```bash
echo "last_commit_sha=COMMIT_SHA" > /tmp/gh-aw/repo-memory/default/upstream-docs-state.txt
echo "last_check_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /tmp/gh-aw/repo-memory/default/upstream-docs-state.txt
echo "foundry_commits_found=N" >> /tmp/gh-aw/repo-memory/default/upstream-docs-state.txt
cp /tmp/gh-aw/repo-memory/default/upstream-docs-state.txt /tmp/gh-aw/cache-memory/upstream-docs-state.txt
```

## Guidelines

- Only count commits that touch `articles/foundry/**` — the repo has many other doc areas (Azure Search, Azure OpenAI, etc.) that are irrelevant
- Be conservative: only dispatch sync-and-convert when genuinely new Foundry content has landed
- Track commit SHAs to avoid re-processing the same changes
