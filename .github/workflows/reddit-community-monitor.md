---
name: Reddit Community Monitor
description: Analyzes Reddit posts about Microsoft Foundry/Azure AI dispatched by the Devvit app, identifies documentation gaps
on:
  repository_dispatch:
    types: [reddit-foundry-mention]
  slash_command:
    name: check-reddit
    events: [issue_comment]
  workflow_dispatch:
  skip-if-match: 'is:issue is:open in:title "[reddit-community]"'
  reaction: "eyes"

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: copilot
strict: true
tracker-id: reddit-community-monitor

tools:
  cache-memory: true
  github:
    toolsets: [default]
  bash:
    - "cat *"
    - "grep *"
    - "find docs-vnext -name '*.mdx'"
    - "echo *"
    - "date *"

safe-outputs:
  create-issue:
    title-prefix: "[reddit-community] "
    labels: [reddit-community, documentation]
    expires: 14d
    close-older-issues: true
  add-comment:
    max: 1
  noop:

network:
  allowed:
    - defaults
    - github

imports:
  - shared/mood.md
  - shared/reporting.md
  - shared/mcp/foundry-docs.md

timeout-minutes: 10
---

# Reddit Community Monitor

You analyze Reddit posts about Microsoft Foundry, Azure OpenAI, and Azure AI that are dispatched by the Devvit community monitoring app. Your job is to determine whether these posts indicate documentation gaps, errors, or frequently asked questions that should be addressed in `docs-vnext/`.

## Context

- **Repository**: ${{ github.repository }}
- **Signal source**: Reddit communities (via Devvit app → `repository_dispatch`)
- **Documentation directory**: `docs-vnext/` (Mintlify MDX format)
- **Complementary tool**: Reddit Pro provides the analytics/discovery layer; this workflow handles the automation

## When Triggered via repository_dispatch

The dispatch payload from the Devvit app contains:
- `github.event.client_payload.subreddit` — Source subreddit (e.g., "azure", "MachineLearning")
- `github.event.client_payload.title` — Post/comment title
- `github.event.client_payload.url` — Direct Reddit link
- `github.event.client_payload.bodySnippet` — First 500 chars of body text
- `github.event.client_payload.keywords` — Matched keywords (e.g., ["azure openai", "hosted agent"])
- `github.event.client_payload.source` — "post" or "comment"

## When Triggered via /check-reddit

Load cached state and check for any manually-noted Reddit posts that need analysis. This is a fallback for when the Devvit app dispatches are unavailable.

## Step 1: Load Cached State

```bash
cat /tmp/gh-aw/cache-memory/reddit-community.txt 2>/dev/null || echo "No cached state — first run"
```

## Step 2: Extract Post Details

### If repository_dispatch
Read the payload from the activation context. Extract the subreddit, title, URL, body snippet, and matched keywords.

### If /check-reddit or workflow_dispatch
Check the cache for any pending posts. If none, call noop.

## Step 3: Search Existing Documentation

Use the `foundry-docs` MCP server to check if the topic is already documented:

1. `search_docs("matched_keyword")` — Find related pages
2. `get_doc("path")` — Read the current content of a page
3. For each result, assess coverage depth

Keywords from the payload indicate which topics to search. For example:
- `azure openai` → `search_docs("azure openai deployment")`
- `hosted agent` → `search_docs("hosted agent deploy")`
- `model context protocol` → `search_docs("MCP server setup")`

## Step 4: Classify the Post

Analyze the post content and documentation search results to classify:

| Classification | Criteria | Action |
|---------------|----------|--------|
| **Doc gap** | Post asks about a topic not covered in docs-vnext | Create issue |
| **Doc error** | Post reports incorrect information that matches our docs | Create issue |
| **FAQ signal** | Post asks a common question our docs should preempt | Create issue |
| **SDK confusion** | Post shows confusion about SDK usage patterns | Create issue (lower priority) |
| **Already documented** | Docs already cover this topic well | Noop |
| **Off-topic** | Not actually about Foundry/Azure AI despite keyword match | Noop |

## Step 5: Create Issue or Noop

### If Documentation-Relevant

Create an issue:

```markdown
### 📡 Reddit Community Signal — Documentation Impact

**Source**: r/SUBREDDIT
**Post**: [TITLE](URL)
**Matched Keywords**: keyword1, keyword2
**Classification**: [Doc gap / Doc error / FAQ signal / SDK confusion]

### Problem

[Summary of the documentation issue identified from the Reddit post]

### What the User Was Asking/Reporting

[Brief summary of the post content]

### Documentation Search Results

[What was found (or not found) via search_docs]

### Affected Documentation

- `docs-vnext/path/to/relevant/file.mdx`

### Suggested Action

[What should be updated or added in docs-vnext/]

### Reddit Pro Follow-up

- [ ] Check Reddit Pro analytics for similar posts (trending?)
- [ ] Consider scheduling a doc update announcement to r/SUBREDDIT via Reddit Pro
```

### If Not Documentation-Relevant

```json
{"noop": {"message": "Reddit post from r/SUBREDDIT analyzed — no documentation impact. Keywords: [keywords]. Classification: [already documented/off-topic]"}}
```

## Step 6: Update Cache

```bash
cat > /tmp/gh-aw/cache-memory/reddit-community.txt << EOF
last_run=$(date -u +%Y-%m-%dT%H:%M:%SZ)
last_subreddit=SUBREDDIT
last_post_url=URL
posts_analyzed=N
issues_created=N
EOF
```

## Guidelines

- Only create issues for genuine documentation gaps — not every Reddit post needs action
- Use the MCP server search results to verify gaps before creating issues
- Include the Reddit URL in every issue for easy follow-up
- Be selective: 1 high-quality issue is better than 5 noise issues
- Include Reddit Pro follow-up checklist items in issues for the human operator
- Never modify `docs/` — only suggest changes to `docs-vnext/`
