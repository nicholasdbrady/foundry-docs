---
name: Post-Merge Documentation Verification
description: Verifies documentation quality after a PR is merged
on:
  pull_request:
    types: [closed]
  reaction: "rocket"
  skip-bots: [github-actions, copilot, dependabot]

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: post-merge-docs-verify

network:
  allowed:
    - defaults
    - github
    - learn.microsoft.com

tools:
  github:
    toolsets: [default]
  web-fetch:
  bash:
    - "cat *"
    - "grep *"
    - "find docs-vnext -name '*.mdx'"
    - "python -c *"

safe-outputs:
  add-comment:
    max: 1
  create-issue:
    title-prefix: "[post-merge] "
    labels: [documentation, post-merge-check]
    expires: 7d
  noop:

timeout-minutes: 15
---

# Post-Merge Documentation Verification

You run after a pull request is merged. Your job is to verify that the merged changes haven't introduced documentation issues — broken links, invalid code examples, or MDX syntax errors.

## Context

- **Repository**: ${{ github.repository }}
- **Merged PR**: "${{ needs.activation.outputs.text }}"

## Step 1: Identify Changed Files

Use GitHub tools to get the list of files changed in the merged PR. Focus only on files under `docs-vnext/`.

If no `docs-vnext/` files were changed, call `noop` — nothing to verify.

## Step 2: Verify Each Changed File

For each changed `.mdx` file:

### MDX Syntax
- Valid frontmatter with `title` and `description`
- Uses `{/* */}` for comments
- Uses `<br />` (self-closing)
- Proper Mintlify callout components

### Code Examples
- Python syntax validity: `python -c "import ast; ast.parse('''CODE''')"` 
- No obviously broken imports

### External Links
- Spot-check 2-3 external links per file using `web-fetch`
- Verify `learn.microsoft.com` links return 200

## Step 3: Report Results

### If Issues Found

Create an issue listing the problems:

```markdown
### ⚠️ Post-Merge Documentation Issues

**Merged PR**: #NUMBER
**Files checked**: N

### Issues Found

| File | Issue | Severity |
|------|-------|----------|
| `docs-vnext/path/file.mdx` | Broken link to learn.microsoft.com | 🔴 |

### Details

<details>
<summary>Detailed findings</summary>

...

</details>
```

### If No Issues

Add a comment on the merged PR:
```markdown
✅ **Post-merge docs check passed** — N files verified, no issues found.
```

## Guidelines

- Be fast — this runs on every merge
- Only check docs-vnext/ files
- Focus on high-impact issues (broken links, invalid syntax)
- Don't re-review style or content quality — that's the PR reviewer's job
