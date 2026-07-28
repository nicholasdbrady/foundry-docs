---
name: Model Catalog Sync
description: Scrapes Azure AI model catalog API and regenerates sharded data for the interactive model explorer
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
      generated_dir=/tmp/model-catalog-generated
      rm -rf "$generated_dir"
      mkdir -p "$generated_dir"
      cp docs/static/data/models-core.json "$generated_dir/models-core.json"
      cp docs/static/data/models-huggingface.json "$generated_dir/models-huggingface.json"
      python3 scripts/scrape_model_catalog.py --include-partners --output "$generated_dir"
      python3 scripts/prepare_model_catalog_sync.py \
        --generated-dir "$generated_dir" \
        --primary-dir docs/static/data \
        --mirror-dir docs-vnext/static/data \
        --summary-output /tmp/gh-aw/agent/model-catalog-summary.json
  - name: Prepare model catalog diff evidence
    run: |
      set -euo pipefail
      git diff --stat -- docs/static/data/ docs-vnext/static/data/ \
        > /tmp/gh-aw/agent/model-catalog-diff-stat.txt
      git diff --name-only -- docs/static/data/ docs-vnext/static/data/ \
        > /tmp/gh-aw/agent/model-catalog-changed-files.txt
      patch_bytes=$(git diff --binary -- docs/static/data/ docs-vnext/static/data/ | wc -c)
      printf '%s\n' "$patch_bytes" > /tmp/gh-aw/agent/model-catalog-patch-bytes.txt
      payload_bytes=0
      while IFS= read -r path; do
        [[ -z "$path" ]] && continue
        case "$path" in
          docs/static/data/models-core.json|docs/static/data/models-huggingface.json|docs-vnext/static/data/models-core.json|docs-vnext/static/data/models-huggingface.json)
            ;;
          *)
            echo "Unexpected model catalog output: $path" >&2
            exit 1
            ;;
        esac
        if [[ -f "$path" ]]; then
          file_bytes=$(wc -c < "$path")
          payload_bytes=$((payload_bytes + file_bytes))
        fi
      done < /tmp/gh-aw/agent/model-catalog-changed-files.txt
      printf '%s\n' "$payload_bytes" > /tmp/gh-aw/agent/model-catalog-payload-bytes.txt
      if (( patch_bytes > 10485760 )); then
        echo "Model catalog patch is ${patch_bytes} bytes; maximum is 10485760 bytes." >&2
        exit 1
      fi
      if (( payload_bytes > 10485760 )); then
        echo "Model catalog signed payload is ${payload_bytes} bytes; maximum is 10485760 bytes." >&2
        exit 1
      fi

safe-outputs:
  create-pull-request:
    title-prefix: "[model-catalog] "
    labels: [automation, model-catalog]
    auto-merge: true
    expires: 7d
    draft: false
    max-patch-size: 10240
  report-incomplete:
  noop:
    report-as-issue: false

tools:
  cache-memory: true
  github:
    toolsets: [default]
  bash: ["*"]

imports:
  - shared/mood.md
  - shared/reporting.md

---

# Model Catalog Sync

You are an automation agent that regenerates the model catalog data files for the interactive Model Explorer page.

## Context

- **Repository**: ${{ github.repository }}
- **Script**: `scripts/scrape_model_catalog.py`
- **Output directories**: `docs/static/data/` (live Mintlify site) and its `docs-vnext/static/data/` mirror
- The script scrapes the public Azure AI Asset Gallery API, normalizes model metadata, filters deprecated models, preserves existing region data, and writes JSON files
- Uses `--include-partners` to include all providers (Azure Direct + partners), split into core and HuggingFace shards
- Each shard keeps one compact model object per line to bound full-file payloads without sacrificing diff granularity
- To keep safe-output patches bounded, each run updates one corpus: primary data first, then its docs-vnext mirror on the next run

## Step 1: Verify Prepared Catalog Results

The workflow has already installed the browser runtime, run the signed-out API/UI watchdog, generated the model catalog, selected the bounded primary or mirror phase, and prepared a complete change summary in deterministic pre-agent steps.

Do not install dependencies or rerun the watchdog or scraper. Read the prepared watchdog result:

```bash
cat /tmp/gh-aw/agent/model-catalog-watchdog.json
```

The watchdog must report `"status": "ok"`. If the artifact is missing or reports any other status, call `report_incomplete` with its contents, then STOP. Do not create a PR.

Read the prepared summary and diff evidence:

```bash
cat /tmp/gh-aw/agent/model-catalog-summary.json
cat /tmp/gh-aw/agent/model-catalog-diff-stat.txt
cat /tmp/gh-aw/agent/model-catalog-changed-files.txt
cat /tmp/gh-aw/agent/model-catalog-patch-bytes.txt
cat /tmp/gh-aw/agent/model-catalog-payload-bytes.txt
```

## Step 2: Check for Changes

If the summary reports `"status": "noop"` and `model-catalog-changed-files.txt` is empty, call `noop` with message "Model catalog data is up to date — no changes detected."

If the summary status and changed file list disagree, call `report_incomplete` with both artifacts and STOP.

## Step 3: Summarize Changes

If data files changed, use `model-catalog-summary.json` to summarize:
- Whether this is the `primary` or `mirror` phase
- Model counts before and after
- New models added and models removed
- Changed model and field counts
- The bounded watchdog result from `/tmp/gh-aw/agent/model-catalog-watchdog.json`

The deterministic summary is authoritative. Do not run ad hoc Python, grep, sed, comm, or process-substitution commands to reconstruct it.

## Step 4: Protected File Guard

Before creating a pull request, inspect the prepared changed file list:

```bash
cat /tmp/gh-aw/agent/model-catalog-changed-files.txt
```

If any changed path is outside these data outputs, call `report_incomplete` and STOP:

- `docs/static/data/models-core.json`
- `docs/static/data/models-huggingface.json`
- `docs-vnext/static/data/models-core.json`
- `docs-vnext/static/data/models-huggingface.json`

For a `primary` phase, only `docs/static/data/` files may change. For a `mirror` phase, only `docs-vnext/static/data/` files may change. If both corpora changed in one run, call `report_incomplete` and STOP.

This workflow must never attempt a safe-output PR containing `.github/workflows/**`, `.github/agents/**`, or other protected automation files.

## Step 5: Create Pull Request

Use `create_pull_request` with:
- Title describing the phase and what changed (e.g., "Update primary model catalog: 3 new models, 1 removed" or "Sync model catalog to docs-vnext")
- Body with the phase, prepared change summary, textual patch size, signed payload size, and a short watchdog summary
- Only the changed files for the selected phase

## Error Handling

- If deterministic setup, watchdog, or scraper execution fails: the workflow must stop before agent execution
- If the selected phase's textual patch or signed payload exceeds the 10 MB safe-output ceiling: the workflow must stop before agent execution
- If the watchdog artifact is missing or not `ok`: `report_incomplete` with the artifact detail
- If unexpected files or both corpora changed: `report_incomplete` with the changed path list
- If no changes: `noop` with "up to date" message
- Never commit or PR bad data
