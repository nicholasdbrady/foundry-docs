---
name: SDK Release Monitor
description: Monitors Azure SDK repos for new azure-ai-projects releases across Python, JS, .NET, and Java
on:
  schedule: every 2h
  slash_command:
    name: sdk-check
    events: [issue_comment]
  workflow_dispatch:
  skip-if-match: 'is:issue is:open in:title "[sdk-release]"'
  reaction: "eyes"

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: sdk-release-monitor

tools:
  cache-memory: true
  github:
    toolsets: [default]
  web-fetch:
  bash:
    - "cat *"
    - "grep *"
    - "date *"
    - "echo *"

safe-outputs:
  create-issue:
    title-prefix: "[sdk-release] "
    labels: [sdk-update, automation]
    expires: 7d
    close-older-issues: true
  noop:

network:
  allowed:
    - defaults
    - github

imports:
  - shared/mood.md
  - shared/reporting.md

timeout-minutes: 10
---

# SDK Release Monitor

You monitor the four Azure SDK repositories for new releases of the `azure-ai-projects` package (the Foundry SDK). Your job is to detect new beta or stable releases and create an issue summarizing what changed.

## Context

- **Repository**: ${{ github.repository }}

## SDK Repositories to Monitor

| Language | Repository | Changelog Path |
|----------|-----------|---------------|
| Python | `Azure/azure-sdk-for-python` | `sdk/ai/azure-ai-projects/CHANGELOG.md` |
| JavaScript | `Azure/azure-sdk-for-js` | `sdk/ai/ai-projects/CHANGELOG.md` |
| .NET | `Azure/azure-sdk-for-net` | `sdk/ai/Azure.AI.Projects/CHANGELOG.md` |
| Java | `Azure/azure-sdk-for-java` | `sdk/ai/azure-ai-projects/CHANGELOG.md` |

## Step 1: Load Cached State

Check cache memory for previously detected versions:

```bash
cat /tmp/gh-aw/cache-memory/sdk-versions.txt 2>/dev/null || echo "No cached state — first run"
```

## Step 2: Fetch Changelogs

For each SDK repo, use `get_file_contents` to fetch the CHANGELOG.md file. Parse the **first entry** that has a date (not `(Unreleased)`).

The format is always:
```
## X.Y.ZbN (YYYY-MM-DD)     ← Python beta
## X.Y.Z-beta.N (YYYY-MM-DD) ← JS/.NET/Java beta
## X.Y.Z (YYYY-MM-DD)        ← Stable release
```

Extract:
- Version string
- Release date
- Whether it's beta or stable
- Breaking changes section (if present)
- Features added section (if present)

## Step 3: Compare with Cache

For each language, compare the detected latest version against the cached version.

If any language has a **new version** (different from cache):
- Record which languages have new releases
- Note if it's a coordinated release (multiple languages on same day)

## Step 4: Assess Documentation Impact

For each new release, analyze the changelog for:

1. **Breaking Changes**: Class renames, method signature changes, removed APIs
2. **New Features**: New tools, new subclients, new operations
3. **API Changes**: New parameters, changed return types

Determine which documentation sections in `docs-vnext/` might need updates:
- Tool class renames → `docs-vnext/agents/tools/`
- New subclients → `docs-vnext/api-sdk/`
- Tracing changes → `docs-vnext/observability/`
- New features → `docs-vnext/agents/development/`

## Step 5: Update Cache

```bash
echo "python=VERSION_HERE" > /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "javascript=VERSION_HERE" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "dotnet=VERSION_HERE" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "java=VERSION_HERE" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "last_check=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
```

## Step 6: Create Issue or Noop

### If New Releases Detected

Create an issue with:

```markdown
### 📦 Azure AI Projects SDK Release Detected

### Release Summary

| Language | Version | Date | Type |
|----------|---------|------|------|
| Python | 2.0.0b5 | 2026-03-XX | Beta |
| JS/TS | 2.0.0-beta.6 | 2026-03-XX | Beta |

### Breaking Changes

<details>
<summary><b>Python (if applicable)</b></summary>

- List of breaking changes from changelog

</details>

### New Features

<details>
<summary><b>Python (if applicable)</b></summary>

- List of new features from changelog

</details>

### Documentation Impact Assessment

| Area | Impact | Affected Docs |
|------|--------|--------------|
| Tool renames | High | `docs-vnext/agents/tools/` |
| New APIs | Medium | `docs-vnext/api-sdk/` |

### Recommended Actions

- [ ] Update code examples with renamed classes
- [ ] Document new features
- [ ] Verify existing samples still compile
```

### If No New Releases

```json
{"noop": {"message": "No new SDK releases detected. Checked all 4 repos. Last known: Python=X, JS=Y, .NET=Z, Java=W"}}
```

## Guidelines

- Always check all four SDK repos in every run
- Compare dates to detect coordinated releases
- Focus documentation impact on `docs-vnext/` content
- Be specific about which files need updating
