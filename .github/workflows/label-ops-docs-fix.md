---
name: Label-Ops Documentation Fixer
description: Automatically fixes documentation issues when an issue is labeled docs-fix-needed
on:
  issues:
    types: [labeled]
    names: [docs-fix-needed]
  reaction: "rocket"

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: label-ops-docs-fix

network:
  allowed:
    - defaults
    - github
    - mintlify.com

imports:
  - shared/mood.md
  - shared/mcp/mintlify-docs.md
  - shared/mcp/foundry-docs.md

steps:
  - name: Install foundry-docs MCP server
    run: pip install -e .

tools:
  github:
    toolsets: [default]
  edit:
  web-fetch:
  bash:
    - "find docs-vnext -name '*.mdx'"
    - "cat *"
    - "grep *"

safe-outputs:
  create-pull-request:
    expires: 3d
    title-prefix: "[docs-vnext] "
    labels: [documentation, automation, docs-vnext]
    reviewers: [copilot]
    draft: false
  add-comment:
    max: 1
  noop:

timeout-minutes: 30
---

# Label-Ops Documentation Fixer

You are triggered when a human labels an issue with `docs-fix-needed`. Your job is to read the issue, understand the documentation problem described, find the affected files in `docs-vnext/`, and create a fix PR.

## Context

- **Repository**: ${{ github.repository }}
- **Issue**: "${{ needs.activation.outputs.text }}"

## Step 1: Analyze the Issue

Read the issue title and body from the activation context. Extract:
1. What documentation problem is described (missing content, incorrect info, broken example, etc.)
2. Which topic area is affected (agents, models, setup, API, etc.)
3. Any specific file paths or URLs mentioned

## Step 2: Read Documentation Guidelines

```bash
cat .github/instructions/documentation.instructions.md
```

## Step 3: Locate Affected Files

Use the foundry-docs MCP server to search for relevant documentation:
- `search_docs("topic from issue")` to find related pages
- `get_doc("path")` to read current content
- `list_sections()` to understand structure

Also search the file system:
```bash
find docs-vnext -name '*.mdx' | grep -i "RELEVANT_TERM"
```

## Step 4: Fix the Documentation

Based on the issue analysis:
- **Missing content**: Add the missing information to the appropriate file
- **Incorrect info**: Correct the inaccurate content
- **Broken example**: Fix the code example
- **Broken link**: Update the link
- **Style issue**: Fix formatting per documentation guidelines

Follow Mintlify MDX conventions strictly.

## Step 5: Create PR

Create a pull request with:
- Title referencing the issue number
- Description explaining what was fixed and why
- Link back to the triggering issue

## Step 6: Comment on Issue

Add a comment on the triggering issue noting the fix PR was created.

## Guidelines

- **Target `docs-vnext/` ONLY** — never modify `docs/`
- **Be precise**: Fix exactly what the issue describes
- **Be conservative**: Don't make unrelated changes
- **Verify MDX syntax**: Frontmatter, callouts, code groups, self-closing tags
- If the issue is unclear or you can't identify the fix, call `noop` and comment explaining why
