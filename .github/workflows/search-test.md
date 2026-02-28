---
name: Search Testbench Runner
description: On-demand search quality testing via /search-test slash command
on:
  slash_command:
    name: search-test
    events: [issue_comment]
  workflow_dispatch:
    inputs:
      query:
        description: 'Search query to test'
        required: false
        type: string
  reaction: "eyes"

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: search-test

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
    - "echo *"

safe-outputs:
  add-comment:
    max: 1
  noop:

imports:
  - shared/mood.md

timeout-minutes: 10
---

# Search Testbench Runner

You run when someone uses the `/search-test` slash command. Your job is to test search quality for a specific query or run the full testbench.

## Context

- **Repository**: ${{ github.repository }}
- **Command context**: "${{ needs.activation.outputs.text }}"

## Step 1: Parse the Command

The user invoked `/search-test` with optional arguments:
- `/search-test how to create an agent` — test a specific query
- `/search-test` (no args) — run the full testbench

## Step 2: Install Dependencies

```bash
pip install -e ".[scripts]"
```

## Step 3: Run the Test

### Specific Query

If a query was provided, run it against the search index and report results:

```bash
python -c "
from foundry_docs_mcp.foundry_client import FoundryClient
client = FoundryClient()
results = client.search('USER_QUERY', top_k=10)
for r in results:
    print(f'{r.score:.3f} | {r.path} | {r.title}')
"
```

### Full Testbench

If no query was provided, run the full testbench:

```bash
python scripts/run_testbench.py --test-file tests/search_testbench.json --top-k 10 --min-pass-rate 0.85 --min-tests 1 2>&1
```

## Step 4: Report Results

Add a comment with the results:

### For Specific Query

```markdown
### 🔍 Search Test Results

**Query**: "user query here"

| Rank | Score | Path | Title |
|------|-------|------|-------|
| 1 | 0.95 | path/to/doc | Doc Title |
| 2 | 0.87 | path/to/doc2 | Doc Title 2 |
| ... | ... | ... | ... |

**Top result relevance**: High/Medium/Low
```

### For Full Testbench

```markdown
### 🧪 Search Testbench Results

**Tests run**: N
**Pass rate**: X%
**Status**: ✅ Passed / ❌ Failed

<details>
<summary>Detailed results</summary>

[Full testbench output]

</details>
```

## Guidelines

- Report results clearly with relevance scores
- For specific queries, assess whether the top results are relevant
- For full testbench, report the pass/fail summary
- If the search infrastructure isn't available (missing env vars), explain what's needed
