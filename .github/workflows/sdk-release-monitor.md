---
name: SDK Release Monitor
description: Monitors Azure SDK repos for new azure-ai-projects releases across Python, JS, .NET, and Java
on:
  schedule: every 12h
  slash_command:
    name: sdk-check
    events: [issue_comment]
  workflow_dispatch:
  reaction: "eyes"

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
features:
  copilot-requests: true
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
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
    expires: 3d
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

You monitor the Azure SDK repositories and REST API for new releases of the `azure-ai-projects` package **v2.x** (the Microsoft Foundry SDK). Your job is to detect new v2 beta or stable releases and create an issue summarizing what changed.

**IMPORTANT**: Only track and report on **v2.x releases**. Ignore all v1.x versions entirely — they are legacy. The v2 SDK is launching this week across all languages. Even if only pre-release/beta versions of v2 exist, those are the versions to track and report on.

## Context

- **Repository**: ${{ github.repository }}

## SDK Repositories to Monitor

| Language | Repository | Package | Changelog Path |
|----------|-----------|---------|---------------|
| Python | `Azure/azure-sdk-for-python` | `azure-ai-projects` | `sdk/ai/azure-ai-projects/CHANGELOG.md` |
| JavaScript/TypeScript | `Azure/azure-sdk-for-js` | `@azure/ai-projects` | `sdk/ai/ai-projects/CHANGELOG.md` |
| .NET | `Azure/azure-sdk-for-net` | `Azure.AI.Projects` | `sdk/ai/Azure.AI.Projects/CHANGELOG.md` |
| Java | `Azure/azure-sdk-for-java` | `azure-ai-projects` | `sdk/ai/azure-ai-projects/CHANGELOG.md` |
| REST API | `Azure/azure-rest-api-specs` | `Microsoft.AIFoundry` | `specification/ai/Microsoft.AIFoundry/` |

## Step 1: Load Cached State

Check cache memory for previously detected versions:

```bash
cat /tmp/gh-aw/cache-memory/sdk-versions.txt 2>/dev/null || echo "No cached state — first run"
```

## Step 2: Fetch Changelogs

For each SDK repo, use `get_file_contents` to fetch the CHANGELOG.md file. Scan for the latest **v2.x entry** that has a date (not `(Unreleased)`). Skip any v1.x entries.

The format is always:
```
## 2.0.0bN (YYYY-MM-DD)      ← Python beta
## 2.0.0-beta.N (YYYY-MM-DD) ← JS/.NET/Java beta
## 2.0.0 (YYYY-MM-DD)        ← Stable release
```

For the REST API, check the `specification/ai/Microsoft.AIFoundry/` directory for the latest `api-version` in TypeSpec or OpenAPI files.

Extract:
- Version string (must be 2.x)
- Release date
- Whether it's beta or stable
- Breaking changes section (if present)
- Features added section (if present)

## Step 3: Compare with Cache

For each language, compare the detected latest v2 version against the cached version.

If any language has a **new version** (different from cache):
- Record which languages have new releases
- Note if it's a coordinated release (multiple languages on same day)

## Step 4: Assess Documentation Impact

For each new release, analyze the changelog for:

1. **Breaking Changes**: Class renames, method signature changes, removed APIs (especially v1→v2 migration)
2. **New Features**: New tools, new subclients, new operations
3. **API Changes**: New parameters, changed return types, new API versions

Determine which documentation sections in `docs-vnext/` might need updates:
- Tool class renames → `docs-vnext/agents/tools/`
- New subclients → `docs-vnext/api-sdk/`
- Tracing changes → `docs-vnext/observability/`
- New features → `docs-vnext/agents/development/`
- REST API changes → `docs-vnext/api-sdk/reference.mdx`, `docs-vnext/api-sdk/latest.mdx`

## Step 5: Update Cache

```bash
echo "python=VERSION_HERE" > /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "javascript=VERSION_HERE" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "dotnet=VERSION_HERE" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "java=VERSION_HERE" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "rest_api=API_VERSION_HERE" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
echo "last_check=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /tmp/gh-aw/cache-memory/sdk-versions.txt
```

## Step 6: Create Issue or Noop

### If New Releases Detected

Create an issue with:

```markdown
### 📦 Azure AI Projects SDK v2 Release Detected

### Release Summary

| Language | Version | Date | Type |
|----------|---------|------|------|
| Python | 2.0.0b5 | 2026-03-XX | Beta |
| JS/TS | 2.0.0-beta.6 | 2026-03-XX | Beta |
| .NET | 2.0.0-beta.3 | 2026-03-XX | Beta |
| Java | 2.0.0-beta.2 | 2026-03-XX | Beta |
| REST API | 2025-05-15-preview | 2026-03-XX | Preview |

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
| REST API version | Medium | `docs-vnext/api-sdk/reference.mdx` |

### Recommended Actions

- [ ] Update code examples with renamed classes
- [ ] Document new features
- [ ] Verify existing samples still compile
- [ ] Update REST API version references
```

### If No New Releases

```json
{"noop": {"message": "No new v2.x SDK releases detected. Checked all 4 repos + REST API. Last known: Python=X, JS=Y, .NET=Z, Java=W, REST=V"}}
```

## Guidelines

- **Only track v2.x releases** — ignore all v1.x versions
- Always check all four SDK repos and the REST API spec in every run
- Compare dates to detect coordinated releases
- Focus documentation impact on `docs-vnext/` content
- Be specific about which files need updating
- If a language only has a v2 pre-release/beta, that is still the version to track
