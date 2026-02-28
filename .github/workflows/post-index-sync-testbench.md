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

network:
  allowed:
    - defaults
    - github
    - python

tools:
  github:
    toolsets: [default]
  bash:
    - "python *"
    - "pip install *"
    - "cat *"
    - "grep *"

safe-outputs:
  create-issue:
    title-prefix: "[search-quality] "
    labels: [search, automation]
    expires: 7d
    close-older-issues: true
  noop:

imports:
  - shared/mood.md
  - shared/reporting.md

timeout-minutes: 15
---

# Post-Index Search Quality Check

You run automatically after the "Incremental Index Sync" workflow completes. Your job is to verify that search quality hasn't regressed after the index update.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: Index sync just completed

## Step 1: Install Dependencies

```bash
pip install -e ".[scripts]"
```

## Step 2: Run Search Testbench

Run the existing testbench regression suite:

```bash
python scripts/run_testbench.py --test-file tests/search_testbench.json --top-k 10 --min-pass-rate 0.85 --min-tests 1 2>&1
```

Capture the output and exit code.

## Step 3: Analyze Results

Parse the testbench output:
- Total tests run
- Pass rate (target: ≥85%)
- Failed queries (if any)
- Average relevance score

## Step 4: Report

### If Tests Pass (≥85% pass rate)

```json
{"noop": {"message": "Search quality check passed. N/M tests passed (X%). Index update is clean."}}
```

### If Tests Fail (<85% pass rate)

Create an issue:

```markdown
### ⚠️ Search Quality Regression Detected

**Trigger**: Post-index-sync check
**Pass rate**: X% (target: ≥85%)

### Failed Queries

| Query | Expected Result | Got | Score |
|-------|----------------|-----|-------|
| "query text" | expected/path | actual/path | 0.XX |

### Recommended Actions

- Review the index sync for data issues
- Check if new/modified documents have correct metadata
- Consider running a full index rebuild
```

## Guidelines

- Use the existing testbench infrastructure — don't reinvent it
- A pass rate below 85% is a regression
- Report specific failed queries so they can be investigated
- This is a quick sanity check, not a comprehensive evaluation
