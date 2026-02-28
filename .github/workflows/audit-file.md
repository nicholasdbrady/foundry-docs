---
name: Audit Documentation File
description: On-demand documentation audit for specific files via /audit command
on:
  slash_command:
    name: audit
    events: [issue_comment, pull_request_comment]
  workflow_dispatch:
  reaction: "eyes"

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: claude
strict: true
tracker-id: audit-file

network:
  allowed:
    - defaults
    - github
    - learn.microsoft.com
    - mintlify.com

imports:
  - shared/mood.md
  - shared/mcp/mintlify-docs.md
  - shared/mcp/foundry-docs.md

steps:
  - name: Install foundry-docs MCP server
    run: pip install -e .

tools:
  cache-memory: true
  github:
    toolsets: [default]
  web-fetch:
  playwright:
  bash:
    - "cat *"
    - "grep *"
    - "find docs-vnext -name '*.mdx'"
    - "python -c *"

safe-outputs:
  add-comment:
    max: 1
  noop:

timeout-minutes: 15
---

# On-Demand Documentation Audit

You perform a targeted audit of specific documentation files when triggered by the `/audit` slash command. The user may specify file paths or topics in their comment.

## Context

- **Repository**: ${{ github.repository }}
- **Command context**: "${{ needs.activation.outputs.text }}"

## Step 1: Parse the Command

The user invoked `/audit` with optional arguments. Parse the context to determine:

1. **Specific files**: e.g., `/audit docs-vnext/agents/development/overview.mdx`
2. **Topic area**: e.g., `/audit agents` or `/audit search`
3. **No arguments**: `/audit` alone — audit a random selection of 5 files

## Step 2: Identify Target Files

Based on the command:

### Specific file path
```bash
cat "docs-vnext/PATH_FROM_COMMAND"
```

### Topic area
```bash
find docs-vnext -path "*TOPIC*" -name '*.mdx' | head -10
```

### No arguments (random selection)
```bash
find docs-vnext -name '*.mdx' | sort -R | head -5
```

## Step 3: Read Documentation Guidelines

```bash
cat .github/instructions/documentation.instructions.md
```

## Step 4: Audit Each File

For each target file, check:

### MDX Syntax
- Valid frontmatter with `title` and `description`
- Correct comment syntax (`{/* */}`)
- Self-closing tags (`<br />`)
- Proper Mintlify callout components
- Valid `<CodeGroup>` usage

### Code Examples
- Python syntax validity (check with `python -c "import ast; ast.parse(...)"`)
- Correct import statements
- Placeholder format (ALL_CAPS)
- No deprecated API patterns

### External Links
- Check 3-5 external links per file using Playwright
- Verify `learn.microsoft.com` links return 200
- Flag any redirects or 404s

### Content Quality
- Follows Diátaxis framework
- No marketing language
- Consistent terminology
- Appropriate heading levels

## Step 5: Post Results

Add a comment with the audit results:

```markdown
### 🔍 Documentation Audit Results

**Files audited**: N
**Triggered by**: /audit [arguments]

### Results

| File | MDX | Code | Links | Quality | Status |
|------|-----|------|-------|---------|--------|
| `path/file.mdx` | ✅ | ✅ | ⚠️ 1 redirect | ✅ | Pass |
| `path/file2.mdx` | ❌ HTML comment | ✅ | ✅ | ✅ | Fail |

<details>
<summary><b>Detailed Findings</b></summary>

#### path/file.mdx
- Link `https://learn.microsoft.com/...` redirects to new URL

#### path/file2.mdx
- Line 15: Uses `<!-- -->` instead of `{/* */}`

</details>
```

## Guidelines

- Be thorough but fast — respect the 15-minute timeout
- For broad audits, prioritize high-impact checks (broken links, invalid MDX)
- Always report results even if everything passes
- Include actionable fix suggestions for each issue
