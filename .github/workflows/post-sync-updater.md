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

steps:
  - name: Install foundry-docs MCP server
    run: pip install -e .

tools:
  cache-memory: true
  github:
    toolsets: [default]
  edit:
  web-fetch:
  bash:
    - "find docs -name '*.mdx'"
    - "find docs-vnext -name '*.mdx'"
    - "diff *"
    - "grep *"
    - "cat *"
    - "git log --oneline -20"
    - "git diff --stat HEAD~1"
    - "git show --stat HEAD"

safe-outputs:
  create-pull-request:
    expires: 1d
    title-prefix: "[docs-vnext] "
    labels: [documentation, automation, docs-vnext, upstream-sync]
    reviewers: [copilot]
    draft: false
    auto-merge: true
  noop:

timeout-minutes: 30
---

# Post-Sync Documentation Updater

You run automatically after the "Sync and Convert Docs" workflow completes. Your job is to analyze what changed in the upstream sync and proactively update `docs-vnext/` accordingly.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: The sync-and-convert workflow just finished
- **Documentation directory**: `docs-vnext/` (Mintlify MDX format)
- **Canonical docs**: `docs/` (just synced from upstream)

## Step 1: Analyze What Changed

Check the most recent sync commit to understand what upstream changes arrived:

```bash
git log --oneline -5
git diff --stat HEAD~1
```

List files that changed in `docs/`:

```bash
git show --stat HEAD | grep 'docs/' | head -30
```

If no `docs/` files changed in the last commit, call `noop` — the sync had no upstream changes.

## Step 2: Identify Impacted docs-vnext Files

For each changed file in `docs/`, determine:
1. Does a corresponding file exist in `docs-vnext/`?
2. Has the `docs-vnext/` version been customized (differs from the old `docs/` version)?
3. What type of change occurred: new content, updated content, or structural change?

```bash
for f in $(git show --stat HEAD -- docs/ | grep '\.mdx' | awk '{print $1}' | sed 's|docs/||'); do
  if [ -f "docs-vnext/$f" ]; then
    if ! diff -q "docs/$f" "docs-vnext/$f" > /dev/null 2>&1; then
      echo "CUSTOMIZED: $f (docs-vnext differs from synced docs)"
    else
      echo "IDENTICAL: $f (no customizations)"
    fi
  else
    echo "MISSING: $f (exists in docs/ but not docs-vnext/)"
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
