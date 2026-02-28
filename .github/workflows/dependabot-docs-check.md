---
name: Dependabot Documentation Checker
description: Checks if Dependabot dependency updates affect documented APIs or code examples
on:
  pull_request:
    types: [opened, synchronize]
  reaction: "eyes"
  bots: ["dependabot[bot]"]

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: dependabot-docs-check

network:
  allowed:
    - defaults
    - github

tools:
  github:
    toolsets: [default]
  bash:
    - "cat *"
    - "grep *"
    - "find docs-vnext -name '*.mdx'"
    - "pip show *"

safe-outputs:
  add-comment:
    max: 1
  add-labels:
    allowed: [docs-impact, no-docs-impact]
    max: 1
  noop:

timeout-minutes: 10
---

# Dependabot Documentation Checker

You run when Dependabot opens a pull request for dependency updates. Your job is to check if the updated dependency affects any documented APIs, code examples, or instructions in `docs-vnext/`.

## Context

- **Repository**: ${{ github.repository }}
- **PR**: "${{ needs.activation.outputs.text }}"

## Step 1: Identify Updated Dependencies

Read the PR title and body to extract:
- Which package(s) are being updated
- Old version → new version
- Whether it's a major, minor, or patch update

Key dependencies to watch:
- `azure-ai-projects` — core SDK documented throughout
- `fastmcp` — MCP server framework
- `azure-ai-inference` — inference SDK
- `azure-identity` — authentication
- `openai` — OpenAI SDK integration
- `mintlify` — documentation framework

## Step 2: Search Documentation for References

For each updated package, search `docs-vnext/` for references:

```bash
grep -rl "PACKAGE_NAME" docs-vnext/ 2>/dev/null
grep -rl "from PACKAGE import" docs-vnext/ 2>/dev/null
grep -rl "pip install PACKAGE" docs-vnext/ 2>/dev/null
```

## Step 3: Assess Impact

| Update Type | Docs Impact |
|-------------|-------------|
| Patch (x.y.Z) | Usually none |
| Minor (x.Y.z) | Check for new features to document |
| Major (X.y.z) | Likely breaking changes in code examples |
| Pre-release (beta/alpha) | Check for API changes |

## Step 4: Report

### If Documentation Impact Detected

Add a comment on the PR:

```markdown
### 📦 Documentation Impact Assessment

**Updated**: `package-name` (old → new)

### Affected Documentation

| File | Reference | Impact |
|------|-----------|--------|
| `docs-vnext/path/file.mdx` | `import from package` | May need update |

### Recommended Actions

- [ ] Check if code examples still work with new version
- [ ] Update version references if documented
- [ ] Verify API changes against documented behavior
```

Add label `docs-impact`.

### If No Documentation Impact

Add a brief comment: "✅ No documentation impact detected for this dependency update."

Add label `no-docs-impact`.

## Guidelines

- Be fast — Dependabot PRs should be merged quickly
- Focus on breaking changes and major updates
- Patch updates rarely affect documentation
- Only check `docs-vnext/` content
