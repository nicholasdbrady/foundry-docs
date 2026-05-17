---
name: Label-Ops Documentation Fixer
description: Automatically fixes documentation issues when an issue is labeled docs-fix-needed, sdk-update, or noob-test
on:
  issues:
    types: [labeled]
    names: [docs-fix-needed, sdk-update, noob-test]
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
    - "find docs-vnext -name"
    - "cat *"
    - "grep *"
    - "sed *"
    - "head *"
    - "tail *"
    - "wc *"
    - "diff *"
    - "python3 *"

safe-outputs:
  create-pull-request:
    expires: 7d
    title-prefix: "[docs-vnext] "
    labels: [documentation, automation, docs-vnext]
    reviewers: [copilot]
    auto-merge: true
    draft: false
  add-comment:
    max: 1
  report-incomplete:
  noop:
    report-as-issue: false

timeout-minutes: 15
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
---

# Label-Ops Documentation Fixer

You are triggered when an issue is labeled `docs-fix-needed`, `sdk-update`, or `noob-test`. Your job is to read the issue, understand the documentation problem described, find the affected files in `docs-vnext/`, and create a fix PR.

When the triggering label is `sdk-update`, the issue was created by the SDK Release Monitor and contains structured sections: **Breaking Changes**, **New Features**, **Documentation Impact Assessment**, and **Recommended Actions**. Treat the recommended actions as your task list and apply each change systematically across all affected files in `docs-vnext/`.

When the triggering label is `noob-test`, the issue was created by the Documentation Noob Tester — an automated workflow that navigates the live docs site as a complete beginner. The issue contains structured sections: **Summary**, **Critical Issues Found**, **Confusing Areas**, **What Worked Well**, and **Recommendations**. Prioritize fixes in this order:
1. **Critical Issues** (🔴) — blocking problems like broken links, 404 pages, missing prerequisites, incorrect code examples
2. **Confusing Areas** (🟡) — unclear explanations, jargon without definitions, missing examples, inconsistent terminology
3. **Recommendations** — treat each recommendation as a task to address

Focus on actionable content fixes: clarify confusing prose, add missing context, fix broken examples, improve getting-started flow. Skip cosmetic or layout-only observations that are Mintlify theme concerns rather than content issues.

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

### Noob Test Issues (label: `noob-test`)

If the issue title starts with `[noob-test]`, this is an automated noob test report. Parse these sections from the issue body:
- **Summary** — understand which pages were visited and the overall impression
- **Critical Issues Found** (🔴) — extract each blocking issue with its page URL and description
- **Confusing Areas** (🟡) — extract each confusing section with its page URL and what was unclear
- **Recommendations** — treat each suggestion as a prioritized task

For each issue or recommendation:
1. Map the documentation site URL back to the source file in `docs-vnext/` (e.g., `/agents/development/overview` → `docs-vnext/agents/development/overview.mdx`)
2. Read the current file content
3. Apply the fix: clarify prose, add missing prerequisites, fix code examples, add definitions for jargon, improve step-by-step flow
4. Verify MDX syntax after editing

Skip items that are purely about site layout, theme styling, or viewport rendering — those are Mintlify platform concerns, not content fixes.

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
