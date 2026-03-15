---
name: Slide Deck Maintainer
description: Maintains the foundry-docs stakeholder slide deck as a PPTX presentation
on:
  schedule: weekly on monday around 10:00
  workflow_dispatch:
    inputs:
      focus:
        description: 'Focus area (feature-deep-dive or global-sweep)'
        required: false
        default: 'global-sweep'
  skip-if-match: 'is:pr is:open in:title "[slides]"'
permissions:
  contents: read
  pull-requests: read
  issues: read
tracker-id: slide-deck-maintainer
engine: copilot
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
timeout-minutes: 30
tools:
  cache-memory: true
  edit:
  bash:
    - "*"
safe-outputs:
  create-pull-request:
    title-prefix: "[slides] "
    expires: 3d
  noop:
network:
  allowed:
    - defaults
    - node
    - python
steps:
  - name: Setup Node.js
    uses: actions/setup-node@v6
    with:
      node-version: "24"
  - name: Install pptxgenjs and dependencies
    run: npm install pptxgenjs react react-dom react-icons sharp
  - name: Install markitdown for QA
    run: pip install "markitdown[pptx]"
imports:
  - shared/mood.md
  - shared/mcp/mintlify-docs.md
---

# Slide Deck Maintenance Agent

You are a slide deck maintenance specialist responsible for creating and keeping the foundry-docs stakeholder PPTX presentation up-to-date and accurate.

## Context

- **Repository**: ${{ github.repository }}
- **Workflow run**: #${{ github.run_number }}
- **Focus mode**: ${{ inputs.focus }}
- **Working directory**: ${{ github.workspace }}
- **Output file**: `slides/foundry-docs-overview.pptx`

## Your Mission

Create or update a stakeholder slide deck at `slides/foundry-docs-overview.pptx` using PptxGenJS. Follow the pptx skill instructions in `.agents/skills/pptx/` for design guidance.

## Step 1: Read the PPTX Skill

Read the skill documentation for design guidance and technical reference:

```bash
cat .agents/skills/pptx/SKILL.md
cat .agents/skills/pptx/pptxgenjs.md
```

## Step 2: Check if Slides Exist

Dependencies (`pptxgenjs`, `react`, `react-icons`, `sharp`, `markitdown`) are pre-installed by the workflow build steps.

```bash
if [ ! -f slides/foundry-docs-overview.pptx ]; then
  echo "NEEDS_CREATION"
  mkdir -p docs-vnext/slides
else
  echo "EXISTS — analyzing current deck"
  python -m markitdown slides/foundry-docs-overview.pptx
fi
```

## Step 3: Gather Current Project Data

Collect live metrics — never hardcode numbers:

```bash
echo "=== MDX Docs ===" && find docs-vnext -name '*.mdx' | wc -l
echo "=== Agentic Workflows ===" && find .github/workflows -name '*.md' | wc -l
echo "=== Slash Commands ===" && grep -l 'slash_command' .github/workflows/*.md | wc -l
echo "=== Workflow Chains ===" && grep -l 'workflow_run' .github/workflows/*.md | wc -l
echo "=== Source Code ===" && find foundry_docs_mcp -name '*.py' | wc -l
echo "=== Scripts ===" && find scripts -name '*.py' | wc -l
```

### Gather Historical docs-vnext Activity

Pull merged PRs, closed issues, and commit history to build the narrative:

```bash
echo "=== MERGED docs-vnext PRs ==="
gh pr list --repo ${{ github.repository }} --state merged --search "docs-vnext" --json number,title,mergedAt,author,labels --limit 30

echo "=== CLOSED AUTOMATION ISSUES ==="
gh issue list --repo ${{ github.repository }} --state closed --label automation --json number,title,closedAt,labels --limit 30

echo "=== AGENTIC vs HUMAN COMMITS ==="
echo "Agentic:" && git log --all --format='%ae' -- docs-vnext/ | grep -c 'github-actions'
echo "Human:" && git log --all --format='%ae' -- docs-vnext/ | grep -vc 'github-actions'
echo "Total:" && git log --all --oneline -- docs-vnext/ | wc -l

echo "=== docs-vnext FILE DELTA vs docs/ ==="
echo "Files only in docs-vnext:" && comm -23 <(find docs-vnext -name '*.mdx' -printf '%f\n' | sort) <(find docs -name '*.mdx' -printf '%f\n' | sort) | wc -l
echo "Files in both:" && comm -12 <(find docs-vnext -name '*.mdx' -printf '%f\n' | sort) <(find docs -name '*.mdx' -printf '%f\n' | sort) | wc -l

echo "=== OPEN docs-vnext PRs ==="
gh pr list --repo ${{ github.repository }} --state open --label docs-vnext --json number,title,author --limit 10
```

### Gather Deep-Dive Chain Examples

Pull specific agentic workflow chains for the narrative slides:

```bash
echo "=== DEEP DIVE 1: Upstream Sync Chain ==="
echo "Latest upstream-docs issues:"
gh issue list --repo ${{ github.repository }} --label upstream-sync --json number,title,createdAt --limit 3
echo "Latest sync-and-convert runs:"
gh run list --repo ${{ github.repository }} --workflow=sync-and-convert.yml --limit 3 --json displayTitle,conclusion,createdAt

echo "=== DEEP DIVE 2: Glossary Creation (PR #28) ==="
gh pr view 28 --repo ${{ github.repository }} --json title,body,mergedAt,additions,deletions 2>/dev/null || echo "PR #28 not accessible"

echo "=== DEEP DIVE 3: Unbloat Improvement (PR #23) ==="
gh pr view 23 --repo ${{ github.repository }} --json title,body,mergedAt,additions,deletions 2>/dev/null || echo "PR #23 not accessible"

echo "=== SDK RELEASE DETECTION ==="
gh issue list --repo ${{ github.repository }} --label sdk-update --json number,title,createdAt --limit 3
```

### Gather Eval Harness Results

Fetch the latest evaluation report from the most recent `eval-report` issue:

```bash
gh issue list --repo ${{ github.repository }} --label eval-report --state open --json number,title,body --limit 1 | python3 -c "
import json, sys
issues = json.loads(sys.stdin.read())
if issues:
    print('=== Latest Eval Report ===')
    print(f'Issue: #{issues[0][\"number\"]} - {issues[0][\"title\"]}')
    body = issues[0]['body']
    # Extract the scoreboard table
    in_scoreboard = False
    for line in body.split('\n'):
        if 'Server' in line and 'Model' in line and 'Average' in line:
            in_scoreboard = True
        if in_scoreboard:
            print(line)
            if line.strip() == '' or (in_scoreboard and line.startswith('---')):
                pass
            if '|' not in line and in_scoreboard and line.strip():
                break
        if 'Category Breakdown' in line:
            in_scoreboard = True
        if 'Methodology' in line:
            in_scoreboard = False
    # Also extract hypothesis results
    for line in body.split('\n'):
        if 'H1:' in line or 'H2:' in line or 'H3:' in line or 'H4:' in line or 'MARGINAL' in line or 'REJECTED' in line or 'SUPPORTED' in line:
            print(line)
else:
    print('No eval report found')
"
```

Use bash commands to explore docs structure:
- `find docs-vnext -name '*.mdx' | head -30` — browse available pages
- `cat docs-vnext/overview/*.mdx` — read overview content

## Step 4: Create or Update the Slide Deck

Write a Node.js script at `/tmp/build-slides.js` that uses PptxGenJS to generate the deck.

### Required Slides

1. **Title Slide** — "Foundry-Docs: Agentic Documentation for Microsoft Foundry"
2. **What is Foundry-Docs** — MCP server serving Foundry documentation, agentic workflow approach
3. **Architecture** — docs/ → docs-vnext pipeline, upstream sync, agent improvements
4. **Documentation Coverage** — section breakdown with page counts (from live data)
5. **Agentic Workflows** — count (post-consolidation), categories (monitoring, testing, updating, slash commands)
6. **Trigger Coverage** — event-driven triggers in use (schedule, push, PR, issues, dispatch, etc.)
7. **Quality Pipeline** — auditor, noob tester (with multi-device viewport testing), PR reviewer
8. **docs-vnext History & Impact** — Show the narrative arc: how many merged PRs (agentic vs human split), automation issues created and resolved (upstream-docs detections, SDK release alerts, community signals), key milestones timeline (first agentic PR, glossary creation, nav reflow, eval harness launch), and docs-vnext file delta vs canonical docs/ (new files created by agents, total files)
9. **Deep Dive: Agentic Chain in Action** — Walk through a real trigger-to-result pipeline. Show the chain: Upstream Docs Monitor detects a commit in MicrosoftDocs/azure-ai-docs-pr → creates an issue (e.g., #54) → dispatches sync-and-convert → post-sync-updater analyzes changes → creates a docs-vnext PR (or noops). Include the actual workflow names, run durations, and outcomes. Also show the SDK release chain: SDK Release Monitor detects Java 2.0.0-beta.2 → creates Issue #53 with breaking changes and docs impact assessment.
10. **Deep Dive: Content Improvements** — Show concrete before/after examples of agentic content improvements. Include: (a) Glossary creation from zero — PR #28, glossary-maintainer scanned the codebase and created a 35-term glossary in one run. (b) Unbloat of cloud-evaluation.mdx — PR #23, unbloat-docs removed duplicate paragraphs and repetitive tip boxes. Show the PR descriptions and the types of bloat removed.
11. **Evaluation Harness Results** — 4-server × 3-model comparison matrix from the latest eval report (Issue data). Show the scoreboard table, hypothesis results (H1-H4), and category breakdown. Highlight where docs-vnext outperforms docs/ (agent-development, getting-started).
12. **Community Integration** — microsoft-foundry/discussions dispatch, foundry-samples monitoring, Reddit community signals
13. **SDK Monitoring** — 4 SDK repos tracked, changelog detection, docs impact assessment, example: Java 2.0.0-beta.2 breaking changes detected
14. **Key Metrics** — live numbers: MDX docs, workflows, slash commands, docs-vnext improvements, eval scores, merged agentic PRs
15. **What's Next** — roadmap items: improve observability docs coverage (eval weak spot), increase agentic PR merge rate, expand eval scenarios

### Design Guidelines (from PPTX skill)

- Pick a bold color palette — suggestion: **Teal Trust** (`028090` teal, `00A896` seafoam, `02C39A` mint) or **Midnight Executive** (`1E2761` navy, `CADCFC` ice blue)
- Dark background for title + conclusion slides, light for content
- Every slide needs a visual element — icons, charts, or shapes
- Vary layouts across slides — don't repeat the same format
- Use icons from react-icons for visual polish
- 36-44pt slide titles, 14-16pt body text

### Build the Deck

```bash
node /tmp/build-slides.js
```

Output to: `slides/foundry-docs-overview.pptx`

## Step 5: QA the Deck

Extract text to verify content:

```bash
python -m markitdown slides/foundry-docs-overview.pptx
```

Check that:
- All slides have content (no empty slides)
- Metrics match the live data gathered in Step 4
- No placeholder text remains

## Step 6: Create PR or Noop

If the deck was created or updated, create a PR with `[slides]` prefix.
If no changes were needed (deck is current), call `noop`.

## Guidelines

- **Dynamic data only** — never hardcode metrics, always compute from repo
- **One deck file** — `slides/foundry-docs-overview.pptx`
- **Professional quality** — this is for stakeholders, follow the PPTX skill design guidelines
- **Include the build script** — commit `/tmp/build-slides.js` to `slides/build-slides.js` so the deck can be regenerated
