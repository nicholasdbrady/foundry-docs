---
name: Post-Sync Documentation Updater
description: Automatically updates docs-vnext after upstream sync completes
on:
  workflow_run:
    workflows: ["Sync and Convert Docs"]
    types: [completed]
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: post-sync-updater
timeout-minutes: 15
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true

network:
  allowed:
    - defaults
    - github
    - mintlify.com

imports:
  - shared/mood.md
  - shared/reporting.md
  - shared/mcp/mintlify-docs.md
  - shared/mcp/foundry-docs.md
  - shared/mcp/ms-learn.md

tools:
  cache-memory: true
  repo-memory:
    branch-name: memory/doc-metrics
    file-glob: ["*.json", "*.txt"]
    allowed-extensions: [".json", ".txt", ".md"]
    max-file-size: 524288
  github:
    toolsets: [default]
  edit:
  web-fetch:
  bash:
    - "find docs -name"
    - "find docs-vnext -name"
    - "diff *"
    - "grep *"
    - "cat *"
    - "git log --oneline -20"
    - "git diff *"
    - "git rev-parse *"
    - "git show --stat HEAD"

safe-outputs:
  create-pull-request:
    expires: 7d
    title-prefix: "[docs-vnext] "
    labels: [documentation, automation, docs-vnext, upstream-sync]
    reviewers: [copilot]
    draft: false
    auto-merge: true
  noop:

---

# Post-Sync Documentation Updater

You run automatically after the "Sync and Convert Docs" workflow completes. Your job is to analyze what changed in the upstream sync and proactively update `docs-vnext/` accordingly.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: The sync-and-convert workflow just finished
- **Documentation directory**: `docs-vnext/` (Mintlify MDX format)
- **Canonical docs**: `docs/` (just synced from upstream)

## Step 0: Verify Parent Workflow Succeeded

If this was triggered by a `workflow_run` event, check the parent workflow's conclusion:

- The conclusion is available at: `${{ github.event.workflow_run.conclusion }}`
- If the conclusion is NOT `success` (e.g., `failure`, `cancelled`), immediately call `noop` with message: "Parent workflow did not succeed (conclusion: [conclusion]). Skipping."
- If triggered by `workflow_dispatch` (manual), skip this check and proceed normally.

## Step 0B: Load Last Processed Commit

```bash
LAST_SHA=$(cat /tmp/gh-aw/repo-memory/default/post-sync-last-sha.txt 2>/dev/null || cat /tmp/gh-aw/cache-memory/post-sync-last-sha.txt 2>/dev/null || echo "HEAD~1")
echo "Diffing from $LAST_SHA to HEAD"
```

Use `$LAST_SHA` instead of `HEAD~1` in all git diff commands.

## Step 1: Analyze What Changed

Check the most recent sync commit to understand what upstream changes arrived:

```bash
git log --oneline -5
git diff --stat $LAST_SHA HEAD
```

List files that changed in `docs/`:

```bash
git diff --name-only $LAST_SHA HEAD -- docs/ | head -30
```

If no `docs/` files changed since `$LAST_SHA`, call `noop` — the sync had no upstream changes.

## Step 2: Identify Impacted docs-vnext Files

For each changed file in `docs/`, determine:
1. Does a corresponding file exist in `docs-vnext/`?
2. Has the `docs-vnext/` version been customized (differs from the old `docs/` version)?
3. What type of change occurred: new content, updated content, or structural change?

### docs-vnext Information Architecture Mapping

The `docs/` canonical directory uses a flat structure from upstream. `docs-vnext/` reorganizes content for better discoverability:

| docs/ path | docs-vnext/ path | Notes |
|-----------|-----------------|-------|
| `agent-service/*.mdx` | `agents/development/*.mdx` OR `agents/tools/*.mdx` | Agent content split by type |
| `foundry-models/*.mdx` | `models/capabilities/*.mdx` OR `models/catalog/*.mdx` OR `models/fine-tuning/*.mdx` | Model content split by category |
| All other paths | Same relative path | Direct 1:1 mapping |

When checking for missing files, search ALL possible vnext locations before reporting a file as missing.

```bash
for f in $(git diff --name-only $LAST_SHA HEAD -- docs/ | grep '\.mdx$' | sed 's|^docs/||'); do
  # Check direct path first
  if [ -f "docs-vnext/$f" ]; then
    if ! diff -q "docs/$f" "docs-vnext/$f" > /dev/null 2>&1; then
      echo "CUSTOMIZED: $f (docs-vnext differs)"
    else
      echo "IDENTICAL: $f"
    fi
  # Check agent-service → agents/ mapping
  elif echo "$f" | grep -q '^agent-service/'; then
    base=$(basename "$f")
    if [ -f "docs-vnext/agents/development/$base" ] || [ -f "docs-vnext/agents/tools/$base" ]; then
      echo "MAPPED: $f → agents/ (restructured)"
    else
      echo "MISSING: $f (not in docs-vnext/agents/)"
    fi
  # Check foundry-models → models/ mapping
  elif echo "$f" | grep -q '^foundry-models/'; then
    base=$(basename "$f")
    found=$(find docs-vnext/models/ -name "$base" 2>/dev/null | head -1)
    if [ -n "$found" ]; then
      echo "MAPPED: $f → $found (restructured)"
    else
      echo "MISSING: $f (not in docs-vnext/models/)"
    fi
  else
    echo "MISSING: $f (no docs-vnext counterpart)"
  fi
done
```

## Step 3: Read Documentation Guidelines

```bash
cat .github/instructions/documentation.instructions.md
```

## Step 4: Apply Updates

For each impacted file, determine the appropriate action:

### New Files (in docs/ but not docs-vnext/)
- Copy the new file to `docs-vnext/` — it represents new upstream content

### Updated Files (identical in docs-vnext/)
- These were already overwritten by sync; no action needed

### Customized Files (docs-vnext/ was modified by agents)
- Carefully merge upstream changes into the customized version
- Preserve agent improvements (unbloating, better examples, added context)
- Incorporate new upstream content (new sections, updated APIs)

## Step 4B: Quality Comparison

For each file you're about to add or modify, verify the change improves on the canonical source:

1. Search the same topic on **Microsoft Learn MCP** to read the canonical version
2. Compare your proposed docs-vnext content against the MS Learn version
3. Only proceed if the change provides:
   - Better code examples (multi-language, copy-paste ready)
   - Improved structure (clearer headings, better flow)
   - Additional context (prerequisites, troubleshooting, related links)
   - Reduced verbosity while preserving completeness
4. If the canonical version is already better, skip the file — don't regress

Include a brief comparison note in the PR description for each file changed.

## Step 5: Verify MDX Syntax

For any edited files, verify Mintlify MDX compliance:
- Frontmatter has `title` and `description`
- Uses `{/* */}` comments, not `<!-- -->`
- Uses `<br />` not `<br>`
- Callouts use `<Note>`, `<Warning>`, `<Tip>`, `<Info>`
- Code groups use `<CodeGroup>`

## Step 6: Create PR or Noop

If changes were made to `docs-vnext/`:
- Create a PR with description listing which files were updated and why
- Reference the sync commit that triggered this update

If no changes needed:
```json
{"noop": {"message": "Upstream sync had no impact on docs-vnext/. N files synced, all identical or already customized."}}
```

## Guidelines

- **Target `docs-vnext/` ONLY** — never modify `docs/`
- **Preserve customizations**: Agent-improved content in docs-vnext/ should be kept
- **Be minimal**: Only update what the sync actually changed
- **Be fast**: This runs after every sync, so stay within the timeout

## Step 7: Update Persisted State

Write to both repo memory (durable) and cache memory (backward compatibility):

```bash
echo "$(git rev-parse HEAD)" > /tmp/gh-aw/repo-memory/default/post-sync-last-sha.txt
cp /tmp/gh-aw/repo-memory/default/post-sync-last-sha.txt /tmp/gh-aw/cache-memory/post-sync-last-sha.txt
```
