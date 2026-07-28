---
name: Post-Index Search Quality Check
description: Verifies search quality after the search index is updated
on:
  workflow_run:
    workflows: ["Incremental Index Sync"]
    types: [completed]
    branches: [main]
  workflow_dispatch:
  needs: [post_index_regression]

permissions:
  actions: read
  contents: read

engine: copilot
strict: true
tracker-id: post-index-testbench
if: ${{ always() && needs.post_index_regression.outputs.invoke_agent == 'true' }}

jobs:
  post_index_regression:
    name: Execute deterministic post-index regression
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
          python scripts/post_index_regression.py render-decision-output \
            --input "$RESULT_PATH" \
            --output /tmp/post-index-regression/decision-output.json
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
    name: Report and enforce deterministic post-index conclusion
    needs: post_index_regression
    if: always()
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      issues: write
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - name: Download original regression evidence
        uses: actions/download-artifact@v8
        with:
          name: post-index-regression-${{ github.run_id }}
          path: /tmp/post-index-regression
      - name: Resolve retained artifact and incident candidates
        id: report_context
        env:
          REPOSITORY: ${{ github.repository }}
          RUN_ID: ${{ github.run_id }}
          SERVER_URL: ${{ github.server_url }}
          RESULT_STATUS: ${{ needs.post_index_regression.outputs.status }}
        run: |
          set -euo pipefail
          artifact_name="post-index-regression-${RUN_ID}"
          artifact_id=$(
            gh api "repos/${REPOSITORY}/actions/runs/${RUN_ID}/artifacts" \
              --jq ".artifacts[] | select(.name == \"${artifact_name}\") | .id" |
              head -n 1
          )
          test -n "$artifact_id" || {
            echo "Could not resolve retained artifact ${artifact_name}" >&2
            exit 1
          }
          artifact_url="${SERVER_URL}/${REPOSITORY}/actions/runs/${RUN_ID}/artifacts/${artifact_id}"
          echo "artifact_name=${artifact_name}" >> "$GITHUB_OUTPUT"
          echo "artifact_url=${artifact_url}" >> "$GITHUB_OUTPUT"

          printf '[]\n' > /tmp/post-index-regression/incident-candidates.json
          if [[ "$RESULT_STATUS" == "failed" ]]; then
            gh issue list \
              --state open \
              --label search \
              --label automation \
              --limit 100 \
              --json number,title,body \
              > /tmp/post-index-regression/incident-candidates.json
          fi
          python scripts/post_index_regression.py select-incident \
            --input /tmp/post-index-regression/incident-candidates.json \
            --output /tmp/post-index-regression/incident-selection.json
          canonical_number=$(
            jq -r '.canonical_number // empty' /tmp/post-index-regression/incident-selection.json
          )
          echo "canonical_number=${canonical_number}" >> "$GITHUB_OUTPUT"
          : > /tmp/post-index-regression/existing-incident.md
          if [[ -n "$canonical_number" ]]; then
            gh issue view "$canonical_number" --json body --jq '.body' \
              > /tmp/post-index-regression/existing-incident.md
          fi
      - name: Render validated result report
        env:
          REPOSITORY: ${{ github.repository }}
          RUN_ID: ${{ github.run_id }}
          SERVER_URL: ${{ github.server_url }}
          ARTIFACT_NAME: ${{ steps.report_context.outputs.artifact_name }}
          ARTIFACT_URL: ${{ steps.report_context.outputs.artifact_url }}
        run: |
          set -euo pipefail
          python scripts/post_index_regression.py render-report \
            --input /tmp/post-index-regression/post-index-result.json \
            --repository "$REPOSITORY" \
            --run-id "$RUN_ID" \
            --artifact-name "$ARTIFACT_NAME" \
            --artifact-url "$ARTIFACT_URL" \
            --server-url "$SERVER_URL" \
            --existing-body /tmp/post-index-regression/existing-incident.md \
            --output /tmp/post-index-regression/report-output.json \
            --summary-output /tmp/post-index-regression/report-summary.md \
            --incident-title-output /tmp/post-index-regression/issue-title.txt \
            --incident-body-output /tmp/post-index-regression/issue-body.md
          cat /tmp/post-index-regression/report-summary.md >> "$GITHUB_STEP_SUMMARY"
      - name: Upsert one durable regression incident
        if: needs.post_index_regression.outputs.status == 'failed'
        env:
          CANONICAL_NUMBER: ${{ steps.report_context.outputs.canonical_number }}
        run: |
          set -euo pipefail
          if [[ -n "$CANONICAL_NUMBER" ]]; then
            gh issue edit "$CANONICAL_NUMBER" \
              --title "$(cat /tmp/post-index-regression/issue-title.txt)" \
              --body-file /tmp/post-index-regression/issue-body.md \
              --add-label search \
              --add-label automation
          else
            gh issue create \
              --title "$(cat /tmp/post-index-regression/issue-title.txt)" \
              --body-file /tmp/post-index-regression/issue-body.md \
              --label search \
              --label automation
          fi
          jq -r '.duplicate_numbers[]' /tmp/post-index-regression/incident-selection.json |
            while read -r duplicate_number; do
              gh issue close "$duplicate_number" --reason "not planned"
            done
      - name: Enforce the machine-owned conclusion
        run: >-
          python scripts/post_index_regression.py validate
          --input /tmp/post-index-regression/post-index-result.json
          --phase final

network:
  allowed:
    - defaults

tools:
  bash:
    - "cat /tmp/gh-aw/agent/post-index-result.json"

steps:
  - name: Download bounded validated regression artifact
    uses: actions/download-artifact@v8
    with:
      name: post-index-regression-${{ github.run_id }}
      path: /tmp/post-index-agent-input
  - name: Validate and isolate the agent input
    run: |
      set -euo pipefail
      python scripts/post_index_regression.py validate \
        --input /tmp/post-index-agent-input/post-index-result.json \
        --phase schema
      mkdir -p /tmp/gh-aw/agent
      cp /tmp/post-index-agent-input/post-index-result.json /tmp/gh-aw/agent/post-index-result.json
      find /tmp/post-index-agent-input -type f ! -name post-index-result.json -delete

safe-outputs:
  report-failure-as-issue: false
  missing-tool: false
  missing-data: false
  report-incomplete: false
  noop: false
  jobs:
    record-validated-summary:
      description: Record a bounded human-readable summary of the validated post-index result
      runs-on: ubuntu-latest
      output: Validated post-index summary recorded in the workflow run.
      inputs:
        summary:
          description: Concise summary copied only from the validated result
          required: true
          type: string
      permissions:
        contents: read
      steps:
        - name: Append bounded agent summary
          run: |
            {
              echo "### Bounded Agent Summary"
              echo
              jq -r '.items[] | select(.type == "record_validated_summary") | .summary' \
                "$GH_AW_AGENT_OUTPUT"
            } >> "$GITHUB_STEP_SUMMARY"

timeout-minutes: 10
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
---

# Post-Index Search Quality Check

Deterministic custom jobs execute and validate the regression suite, upsert one durable incident for a failed quality result,
record a concrete no-action summary for every other validated result, and enforce the final conclusion. Copilot is activated
only after an executed result passes schema validation. It receives one isolated copy of that bounded result and can publish
only a workflow job summary; it cannot create or update incidents or alter the machine-owned conclusion.

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

## Step 2: Summarize the Machine Decision

Call `record_validated_summary` exactly once with a concise human-readable `summary` containing:

- status and decision
- threshold and actual pass rate
- passed and total test counts
- failed-query count
- diagnostics, if present
- up to five failed query names when the status is `failed`

## Guidelines

- Never create, edit, close, or comment on an issue
- Never run Python, install dependencies, query Azure, or calculate a pass rate
- Never change `status`, `decision`, `threshold`, totals, failed queries, scores, or diagnostics
- A pass rate below 85% is a machine-owned failure; 85% and above is a machine-owned pass
- The deterministic conclusion job publishes every failed query and owns incident deduplication
- This is a quick sanity check, not a comprehensive evaluation
