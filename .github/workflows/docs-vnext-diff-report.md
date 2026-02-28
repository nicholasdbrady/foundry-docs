---
name: Docs-vnext Diff Report
description: Weekly report comparing canonical docs with agent-improved docs-vnext
on:
  schedule: weekly on monday around 09:00
  workflow_dispatch:

permissions:
  contents: read
  issues: read

tracker-id: docs-vnext-diff-report
engine: copilot
strict: true

network:
  allowed:
    - defaults
    - github

tools:
  cache-memory: true
  github:
    toolsets: [default]
  bash:
    - "diff *"
    - "find *"
    - "wc *"
    - "grep *"
    - "cat *"
    - "git *"
    - "sort *"
    - "head *"

safe-outputs:
  create-issue:
    title-prefix: "[docs-vnext-report] "
    labels: [documentation, metrics, docs-vnext]
    close-older-issues: true
    expires: 14
  noop:

timeout-minutes: 15

imports:
  - shared/reporting.md
---

# Docs-vnext Diff Report

You are a documentation metrics agent that generates a weekly "before vs. after" report comparing the canonical `docs/` with the agent-improved `docs-vnext/`.

## Your Mission

Generate a comprehensive report showing what agentic workflows have changed, improved, or added to `docs-vnext/` compared to the canonical `docs/`.

## Context

- **Repository**: ${{ github.repository }}
- **Canonical docs**: `docs/` (upstream source of truth)
- **Agent-improved docs**: `docs-vnext/` (where agentic workflows operate)

## Step 1: Generate Diff Statistics

```bash
# Count files in each directory
echo "=== File Counts ==="
echo "Canonical docs: $(find docs -name '*.mdx' | wc -l) MDX files"
echo "docs-vnext: $(find docs-vnext -name '*.mdx' | wc -l) MDX files"

# Find files unique to docs-vnext (agent-created content)
echo ""
echo "=== Files unique to docs-vnext ==="
diff <(cd docs && find . -name '*.mdx' | sort) <(cd docs-vnext && find . -name '*.mdx' | sort) | grep '^>' | sed 's/^> //'

# Find modified files
echo ""
echo "=== Modified files ==="
for f in $(find docs -name '*.mdx' | sed 's|^docs/||'); do
  if [ -f "docs-vnext/$f" ]; then
    if ! diff -q "docs/$f" "docs-vnext/$f" > /dev/null 2>&1; then
      echo "MODIFIED: $f"
    fi
  fi
done
```

## Step 2: Analyze Changes

For each modified file, compute:
- Lines added/removed
- Word count difference
- Type of change (unbloating, content addition, formatting fix, etc.)

```bash
for f in $(find docs -name '*.mdx' | sed 's|^docs/||'); do
  if [ -f "docs-vnext/$f" ]; then
    if ! diff -q "docs/$f" "docs-vnext/$f" > /dev/null 2>&1; then
      echo "--- $f ---"
      diff --stat "docs/$f" "docs-vnext/$f" 2>/dev/null || true
    fi
  fi
done
```

## Step 3: Review Agent Activity

Search for recent agent-created PRs:
- PRs with `[docs-vnext]` prefix
- PRs with labels: `documentation`, `automation`, `docs-vnext`
- Merge rates and review status

## Step 4: Generate Report

Create an issue with the following structure:

```markdown
### 📊 Docs-vnext Weekly Report - [Date]

### Overview
- **Canonical docs**: X MDX files
- **docs-vnext**: Y MDX files (Z unique to vnext)
- **Modified files**: N files changed by agents
- **Total lines changed**: +A / -B

### Agent Activity This Week
- PRs created: X
- PRs merged: Y (Z% merge rate)
- Files improved: N

### Changes by Category

<details>
<summary><b>📝 Content Improvements (N files)</b></summary>

| File | Lines +/- | Change Type |
|------|-----------|-------------|
| path/to/file.mdx | +10/-5 | Unbloated |

</details>

<details>
<summary><b>📚 New Content (N files)</b></summary>

- `reference/glossary.mdx` — Agent-maintained glossary
- `slides/index.md` — Stakeholder presentation

</details>

### Quality Metrics
- Average line reduction from unbloating: X%
- Glossary terms added: N
- Documentation gaps filled: N

### Recommendations
- Improvements ready to upstream to azure-ai-docs-pr
- Areas needing more agent attention
```

## Step 5: Handle No Changes

If docs/ and docs-vnext/ are identical, call `noop`:

```json
{"noop": {"message": "No differences between docs/ and docs-vnext/. Agents have not yet made changes."}}
```

## Guidelines

- Be data-driven: use actual diff statistics
- Highlight the most impactful changes
- Track trends over time using cache-memory
- Make recommendations for upstreaming improvements
