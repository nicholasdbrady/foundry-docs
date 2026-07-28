---
name: Post-Index Search Quality Check
description: Verifies search quality after the search index is updated
on:
  workflow_run:
    workflows: ["Incremental Index Sync"]
    types: [completed]
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: post-index-testbench
max-daily-ai-credits: -1

jobs:
  post_index_regression:
    name: Execute deterministic post-index regression
    needs: pre_activation
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    env:
      RESULT_PATH: /tmp/post-index-regression/post-index-result.json
      LOG_PATH: /tmp/post-index-regression/post-index-testbench.log
      AZURE_SEARCH_ENDPOINT: ${{ secrets.AZURE_SEARCH_ENDPOINT }}
      AZURE_SEARCH_API_KEY: ${{ secrets.AZURE_SEARCH_API_KEY }}
      AZURE_SEARCH_INDEX_NAME: ${{ secrets.AZURE_SEARCH_INDEX_NAME }}
      AZURE_AI_PROJECT_ENDPOINT: ${{ secrets.AZURE_AI_PROJECT_ENDPOINT }}
      AZURE_AI_PROJECT_API_KEY: ${{ secrets.AZURE_AI_PROJECT_API_KEY }}
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT: ${{ secrets.AZURE_OPENAI_EMBEDDING_DEPLOYMENT }}
    outputs:
      decision: ${{ steps.classify.outputs.decision }}
      invoke_agent: ${{ steps.classify.outputs.invoke_agent }}
      status: ${{ steps.classify.outputs.status }}
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
      - name: Gate on the parent workflow conclusion
        id: parent
        env:
          EVENT_NAME: ${{ github.event_name }}
          PARENT_CONCLUSION: ${{ github.event.workflow_run.conclusion }}
        run: |
          set -euo pipefail
          mkdir -p "$(dirname "$RESULT_PATH")"
          if [[ "$EVENT_NAME" == "workflow_run" && "$PARENT_CONCLUSION" != "success" ]]; then
            python scripts/post_index_regression.py write-blocked \
              --parent-conclusion "$PARENT_CONCLUSION" \
              --output "$RESULT_PATH"
            echo "run_regression=false" >> "$GITHUB_OUTPUT"
          else
            echo "run_regression=true" >> "$GITHUB_OUTPUT"
          fi
      - name: Validate required Azure settings
        id: settings
        if: steps.parent.outputs.run_regression == 'true'
        continue-on-error: true
        run: |
          set -euo pipefail
          test -n "$AZURE_SEARCH_ENDPOINT" || { echo "Missing AZURE_SEARCH_ENDPOINT"; exit 1; }
          test -n "$AZURE_SEARCH_API_KEY" || { echo "Missing AZURE_SEARCH_API_KEY"; exit 1; }
          test -n "$AZURE_SEARCH_INDEX_NAME" || { echo "Missing AZURE_SEARCH_INDEX_NAME"; exit 1; }
          test -n "$AZURE_AI_PROJECT_ENDPOINT" || { echo "Missing AZURE_AI_PROJECT_ENDPOINT"; exit 1; }
          test -n "$AZURE_OPENAI_EMBEDDING_DEPLOYMENT" || { echo "Missing AZURE_OPENAI_EMBEDDING_DEPLOYMENT"; exit 1; }
      - name: Install declared dependencies
        id: install
        if: steps.parent.outputs.run_regression == 'true' && steps.settings.outcome == 'success'
        continue-on-error: true
        run: |
          set -o pipefail
          python -m pip install -e . 2>&1 | tee "$LOG_PATH"
      - name: Run the regression suite
        id: testbench
        if: steps.install.outcome == 'success'
        continue-on-error: true
        run: |
          set -o pipefail
          python scripts/run_testbench.py \
            --test-file tests/search_testbench.json \
            --top-k 10 \
            --min-pass-rate 0.85 \
            --min-tests 1 \
            --output-json "$RESULT_PATH" 2>&1 | tee -a "$LOG_PATH"
      - name: Record deterministic setup or execution failure
        if: always() && steps.parent.outputs.run_regression == 'true'
        run: |
          set -euo pipefail
          if [[ -f "$RESULT_PATH" ]]; then
            exit 0
          fi
          if [[ "${{ steps.settings.outcome }}" != "success" ]]; then
            stage=settings
            message="Required Azure settings are missing; see the workflow log."
          elif [[ "${{ steps.install.outcome }}" != "success" ]]; then
            stage=setup
            message="Dependency installation failed; see post-index-testbench.log."
          else
            stage=execution
            message="The regression suite did not produce a result; see post-index-testbench.log."
          fi
          python scripts/post_index_regression.py write-error \
            --stage "$stage" \
            --message "$message" \
            --output "$RESULT_PATH"
      - name: Validate and classify the result
        id: classify
        if: always()
        run: |
          set -euo pipefail
          python scripts/post_index_regression.py validate --input "$RESULT_PATH" --phase schema
          python scripts/post_index_regression.py classify \
            --input "$RESULT_PATH" \
            --github-output "$GITHUB_OUTPUT"
          cat "$RESULT_PATH" >> "$GITHUB_STEP_SUMMARY"
      - name: Upload bounded regression evidence
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: post-index-regression-${{ github.run_id }}
          path: /tmp/post-index-regression
          if-no-files-found: error
          retention-days: 7
      - name: Enforce pre-agent readiness
        if: always()
        run: python scripts/post_index_regression.py validate --input "$RESULT_PATH" --phase prepare
  post_index_conclusion:
    name: Enforce deterministic post-index conclusion
    needs: [post_index_regression, agent]
    if: always()
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - name: Download original regression evidence
        uses: actions/download-artifact@v8
        with:
          name: post-index-regression-${{ github.run_id }}
          path: /tmp/post-index-regression
      - name: Enforce the machine-owned conclusion
        run: >-
          python scripts/post_index_regression.py validate
          --input /tmp/post-index-regression/post-index-result.json
          --phase final
network:
  allowed:
    - defaults
    - github

tools:
  github:
    toolsets: [default]
  bash:
    - "cat /tmp/gh-aw/agent/post-index-result.json"

steps:
  - name: Download deterministic regression evidence
    uses: actions/download-artifact@v8
    with:
      name: post-index-regression-${{ github.run_id }}
      path: /tmp/gh-aw/agent
  - name: Materialize deterministic safe outputs and skip model invocation
    env:
      GH_AW_SAFE_OUTPUTS: ${{ steps.set-runtime-paths.outputs.GH_AW_SAFE_OUTPUTS }}
    run: |
      set -euo pipefail
      python scripts/post_index_regression.py render-safe-outputs-jsonl \
        --input /tmp/gh-aw/agent/post-index-result.json \
        --output "$GH_AW_SAFE_OUTPUTS"

safe-outputs:
  threat-detection:
    engine: false
  create-issue:
    title-prefix: "[search-quality] "
    labels: [search, automation]
    expires: 7d
    close-older-issues: true
  report-incomplete:
  noop:
    report-as-issue: false

imports:
  - shared/mood.md
  - shared/reporting.md

timeout-minutes: 10
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
---

# Post-Index Search Quality Check

Deterministic host steps execute and validate the search regression suite, materialize the corresponding safe outputs, and
write a `noop` before engine startup. The `noop` is a mandatory short-circuit: no model invocation is required or permitted for
this workflow's regression decision.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: A successful index sync or a manual dispatch
- **Deterministic result**: `/tmp/gh-aw/agent/post-index-result.json`

## Step 1: Read the Prepared Result

Read the result exactly once:

```bash
cat /tmp/gh-aw/agent/post-index-result.json
```

The host steps have already validated schema version `1.0`, preserved all failed queries and scores, and computed the
inclusive 85% threshold decision. If the file is missing or has a status other than `passed` or `failed`, call
`report_incomplete` and stop.

## Step 2: Report the Machine Decision

### If `status` is `passed`

```json
{"noop": {"message": "Search quality check passed. N/M tests passed (X%). Index update is clean."}}
```

Copy N, M, and X from the prepared result.

### If `status` is `failed`

Create an issue:

```markdown
### Search Quality Regression Detected

**Trigger**: Post-index-sync check
**Pass rate**: X% (machine threshold: 85%)

### Failed Queries

Copy every entry from `failed_queries`, including its expected paths, returned paths, and score.

### Recommended Actions

- Review the index sync for data issues
- Check if new/modified documents have correct metadata
- Consider running a full index rebuild
```

## Guidelines

- Never run Python, install dependencies, query Azure, or calculate a pass rate
- Never change `status`, `decision`, `threshold`, totals, failed queries, scores, or diagnostics
- A pass rate below 85% is a machine-owned failure; 85% and above is a machine-owned pass
- Report every failed query so it can be investigated
- This is a quick sanity check, not a comprehensive evaluation
