---
name: Model Catalog Sync
description: Scrapes Azure AI model catalog API and regenerates models.json for the interactive model explorer
on:
  schedule:
    - cron: daily
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

tracker-id: model-catalog-sync
engine: copilot
strict: true
timeout-minutes: 15
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true

network:
  allowed:
    - defaults
    - github

steps:
  - name: Install model catalog browser runtime
    run: |
      set -euo pipefail
      python3 -m pip install "playwright>=1.57.0"
      python3 -m playwright install --with-deps chromium
  - name: Run model catalog watchdog
    run: |
      set -euo pipefail
      mkdir -p /tmp/gh-aw/agent
      python3 scripts/check_model_catalog_watchdog.py \
        --output /tmp/gh-aw/agent/model-catalog-watchdog.json
  - name: Generate model catalog data
    run: |
      set -euo pipefail
      python3 scripts/scrape_model_catalog.py --include-partners --output docs/static/data
      cp docs/static/data/models-core.json docs-vnext/static/data/models-core.json
      cp docs/static/data/models-huggingface.json docs-vnext/static/data/models-huggingface.json
      cp docs/static/data/models.json docs-vnext/static/data/models.json
  - name: Prepare model catalog diff evidence
    run: |
      set -euo pipefail
      git diff --stat -- docs/static/data/ docs-vnext/static/data/ \
        > /tmp/gh-aw/agent/model-catalog-diff-stat.txt
      git diff --name-only -- docs/static/data/ docs-vnext/static/data/ \
        > /tmp/gh-aw/agent/model-catalog-changed-files.txt

safe-outputs:
  create-pull-request:
    title-prefix: "[model-catalog] "
    labels: [automation, model-catalog]
    auto-merge: true
    expires: 7d
    draft: false
  report-incomplete:
  noop:
    report-as-issue: false

tools:
  cache-memory: true
  github:
    toolsets: [default]
  bash: [cat, git, wc]

imports:
  - shared/mood.md
  - shared/reporting.md

---

# Model Catalog Sync

You are an automation agent that regenerates the model catalog data files for the interactive Model Explorer page.

## Context

- **Repository**: ${{ github.repository }}
- **Script**: `scripts/scrape_model_catalog.py`
- **Output directories**: `docs/static/data/` (live Mintlify site) and `docs-vnext/static/data/`
- The script scrapes the public Azure AI Asset Gallery API, normalizes model metadata, filters deprecated models, preserves existing region data, and writes JSON files
- Uses `--include-partners` to include all providers (Azure Direct + partners), split into core and HuggingFace shards

## Step 1: Verify Prepared Catalog Results

The workflow has already installed the browser runtime, run the signed-out API/UI watchdog, generated the model catalog, and copied the bounded outputs to both docs corpora in deterministic pre-agent steps.

Do not install dependencies or rerun the watchdog or scraper. Read the prepared watchdog result:

```bash
cat /tmp/gh-aw/agent/model-catalog-watchdog.json
```

The watchdog must report `"status": "ok"`. If the artifact is missing or reports any other status, call `report_incomplete` with its contents, then STOP. Do not create a PR.

Read the prepared diff evidence:

```bash
cat /tmp/gh-aw/agent/model-catalog-diff-stat.txt
cat /tmp/gh-aw/agent/model-catalog-changed-files.txt
```

## Step 2: Check for Changes

If `model-catalog-changed-files.txt` is empty, call `noop` with message "Model catalog data is up to date — no changes detected."

## Step 3: Summarize Changes

If data files changed, analyze the diff to summarize:
- Number of models before vs after
- New models added
- Models removed
- Changed fields
- The bounded watchdog result from `/tmp/gh-aw/agent/model-catalog-watchdog.json`

Use this to build the PR description.

## Step 4: Protected File Guard

Before creating a pull request, inspect the prepared changed file list:

```bash
cat /tmp/gh-aw/agent/model-catalog-changed-files.txt
```

If any changed path is outside these data outputs, call `report_incomplete` and STOP:

- `docs/static/data/models-core.json`
- `docs/static/data/models-huggingface.json`
- `docs/static/data/models.json`
- `docs-vnext/static/data/models-core.json`
- `docs-vnext/static/data/models-huggingface.json`
- `docs-vnext/static/data/models.json`

This workflow must never attempt a safe-output PR containing `.github/workflows/**`, `.github/agents/**`, or other protected automation files.

## Step 5: Create Pull Request

Use `create_pull_request` with:
- Title describing what changed (e.g., "Update model catalog: 3 new models, 1 removed")
- Body with the change summary from Step 3 and a short watchdog summary
- The changed files in both `docs/static/data/` and `docs-vnext/static/data/`

## Error Handling

- If deterministic setup, watchdog, or scraper execution fails: the workflow must stop before agent execution
- If the watchdog artifact is missing or not `ok`: `report_incomplete` with the artifact detail
- If unexpected files changed: `report_incomplete` with the changed path list
- If no changes: `noop` with "up to date" message
- Never commit or PR bad data
