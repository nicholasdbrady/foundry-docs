---
name: Push Documentation Check
description: Checks if docs-vnext needs updating when core code changes are pushed to main
on:
  push:
    branches: [main]
    paths:
      - "foundry_docs_mcp/**"
      - "scripts/**"
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: on-push-docs-check

network:
  allowed:
    - defaults
    - github

imports:
  - shared/mood.md
  - shared/mcp/foundry-docs.md

steps:
  - name: Install foundry-docs MCP server
    run: pip install -e .

tools:
  github:
    toolsets: [default]
  bash:
    - "git log --oneline -5"
    - "git diff --stat HEAD~1"
    - "git show --stat HEAD"
    - "cat *"
    - "grep *"
    - "find docs-vnext -name '*.mdx'"

safe-outputs:
  create-issue:
    title-prefix: "[docs-sync] "
    labels: [documentation, automation, docs-vnext]
    expires: 7d
    close-older-issues: true
  noop:

timeout-minutes: 10
---

# Push Documentation Check

You run when code changes are pushed to `main` in `foundry_docs_mcp/` or `scripts/`. Your job is to quickly check if the code changes require documentation updates in `docs-vnext/`.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: Push to main

## Step 1: Analyze the Push

```bash
git log --oneline -5
git diff --stat HEAD~1
```

Identify what changed:
- **MCP server changes** (`foundry_docs_mcp/`): New tools, changed tool signatures, new parameters
- **Script changes** (`scripts/`): New pipeline steps, changed build process, new commands

## Step 2: Check Documentation Impact

For each changed file, determine if it affects documented behavior:

| Code Change | Documentation Impact | Location |
|------------|---------------------|----------|
| New MCP tool | Must document | `docs-vnext/api-sdk/` |
| Changed tool signature | Must update examples | Relevant docs referencing the tool |
| New script | May need docs | `docs-vnext/developer-experience/` |
| Bug fix | Usually no impact | — |
| Refactoring | Usually no impact | — |

Use the foundry-docs MCP server to search for docs referencing the changed components:
```
search_docs("tool_name_or_concept")
```

## Step 3: Report or Noop

### If Documentation Updates Needed

Create an issue listing what needs updating:

```markdown
### 📝 Code Change Requires Documentation Update

**Commit**: `COMMIT_SHA`
**Changed files**: list of changed files

### Documentation Impact

| Changed Code | Impact | Docs to Update |
|-------------|--------|---------------|
| `foundry_docs_mcp/server.py` | New tool added | `docs-vnext/api-sdk/...` |

### Suggested Actions

- Update `docs-vnext/path/file.mdx` to document the new `tool_name` tool
- Add code example showing new usage pattern
```

### If No Documentation Impact

```json
{"noop": {"message": "Push to main analyzed. N files changed in foundry_docs_mcp/ and scripts/. No documentation impact detected."}}
```

## Guidelines

- Be fast — this runs on every push, stay lightweight
- Only flag genuine documentation gaps, not every code change
- Bug fixes and refactoring rarely need docs updates
- New features and API changes almost always need docs updates
