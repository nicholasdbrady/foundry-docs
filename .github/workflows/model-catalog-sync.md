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
    - ai.azure.com

safe-outputs:
  create-pull-request:
    title-prefix: "[model-catalog] "
    labels: [automation, model-catalog]
    auto-merge: true
    expires: 2d
    draft: false
  noop:

tools:
  cache-memory: true
  github:
    toolsets: [default]
  edit:
  bash:
    - "python3 scripts/*"
    - "git *"
    - "cat *"
    - "diff *"
    - "wc *"
    - "ls *"
    - "pip *"

imports:
  - shared/mood.md
  - shared/reporting.md

---

# Model Catalog Sync

You are an automation agent that regenerates the model catalog data file for the interactive Model Explorer page.

## Context

- **Repository**: ${{ github.repository }}
- **Script**: `scripts/scrape_model_catalog.py`
- **Output**: `docs-vnext/static/data/models.json`
- The script scrapes the public Azure AI Asset Gallery API, normalizes model metadata, and writes a JSON file

## Step 1: Run the Catalog Scraper

Run the scraper script to regenerate models.json:

```bash
python3 scripts/scrape_model_catalog.py --output docs-vnext/static/data
```

If the script exits with a non-zero code, call `noop` with the error output and STOP — do NOT create a PR with bad data.

## Step 2: Check for Changes

```bash
git diff --stat docs-vnext/static/data/models.json
```

If there are no changes, call `noop` with message "Model catalog data is up to date — no changes detected."

## Step 3: Summarize Changes

If models.json changed, analyze the diff to summarize:
- Number of models before vs after
- New models added
- Models removed
- Changed fields

Use this to build the PR description.

## Step 4: Create Pull Request

Use `create_pull_request` with:
- Title describing what changed (e.g., "Update model catalog: 3 new models, 1 removed")
- Body with the change summary from Step 3
- The changed file: `docs-vnext/static/data/models.json`

## Error Handling

- If the scraper fails: `noop` with error message
- If no changes: `noop` with "up to date" message
- Never commit or PR bad data
