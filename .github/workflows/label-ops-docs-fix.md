---
name: Label-Ops Documentation Fixer
description: Automatically fixes documentation issues when an issue is labeled docs-fix-needed
on:
  issues:
    types: [labeled]
    names: [docs-fix-needed, sdk-update]
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

timeout-minutes: 15
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
---

# Label-Ops Documentation Fixer

You are triggered when an issue is labeled `docs-fix-needed` or `sdk-update`. Your job is to read the issue, understand the documentation problem described, find the affected files in `docs-vnext/`, and create a fix PR.

When the triggering label is `sdk-update`, the issue was created by the SDK Release Monitor and contains structured sections: **Breaking Changes**, **New Features**, **Documentation Impact Assessment**, and **Recommended Actions**. Treat the recommended actions as your task list and apply each change systematically across all affected files in `docs-vnext/`.

## Context

- **Repository**: ${{ github.repository }}
- **Issue**: "${{ steps.sanitized.outputs.text }}"

## Step 1: Analyze the Issue

Read the issue title and body from the activation context. Extract:
1. What documentation problem is described (missing content, incorrect info, broken example, etc.)
2. Which topic area is affected (agents, models, setup, API, etc.)
3. Any specific file paths or URLs mentioned

### SDK Release Issues (label: `sdk-update`)

If the issue title starts with `[sdk-release]`, this is an automated SDK release notification. Parse these sections from the issue body:
- **Release Summary** table — identify which languages have new versions
- **Breaking Changes** — extract class renames, method signature changes, removed APIs
- **New Features** — identify what needs new documentation
- **Documentation Impact Assessment** — use the impact table to prioritize
- **Recommended Actions** — treat each checkbox item as a task

For breaking changes, build a mapping of old name → new name, then search `docs-vnext/` for every occurrence and apply the rename. Common patterns:
- Tool class renames (e.g., `AzureAISearchAgentTool` → `AzureAISearchTool`)
- Method renames (e.g., `.agents.create()` → `.agents.create_version()`)
- Subclient path changes (e.g., `project_client.memory_stores` → `project_client.beta.memory_stores`)
- Tracing attribute renames
- API version string updates
- Import path changes
- Package version bumps in install commands (e.g., `pip install azure-ai-projects==2.0.0b4` → `2.0.0`)

Search broadly — breaking changes can appear in code blocks, prose descriptions, and frontmatter across many files.

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
- **SDK breaking changes**: Apply renames/updates systematically across ALL affected files — use `grep` to find every occurrence before editing, and verify no instances are missed after editing

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
