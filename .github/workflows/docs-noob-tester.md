---
name: Documentation Noob Tester
description: Tests docs-vnext documentation as a new user would, identifying confusing or broken steps
on:
  schedule: daily
  workflow_dispatch:
  skip-if-match: 'is:discussion is:open in:title "Noob Test Report"'
  stop-after: "+365d"
permissions:
  contents: read
  issues: read
  pull-requests: read
engine: copilot
concurrency:
  group: "gh-aw-${{ github.workflow }}"
  cancel-in-progress: true
timeout-minutes: 15
tools:
  playwright:
  web-fetch:
  bash:
    - "cat *"
    - "find *"
    - "ls*"
    - "curl *"
    - "python3 *"
    - "head *"
    - "tail *"
    - "wc *"
safe-outputs:
  upload-asset:
  create-issue:
    title-prefix: "[noob-test] "
    labels: [documentation, automation, noob-test]
    close-older-issues: true
    expires: 14d
  noop:

network:
  allowed:
    - defaults
    - hobbyist-e43fa225.mintlify.app
    - learn.microsoft.com
    - github.com
    - registry.npmjs.org
    - cdn.playwright.dev
    - playwright.download.prss.microsoft.com

imports:
  - shared/mood.md
  - shared/reporting.md
---

# Documentation Noob Testing

You are a brand new user trying to learn about Microsoft Foundry for the first time. Your task is to navigate through the deployed documentation site, follow getting started guides, and identify any confusing, broken, or unclear steps.

## Context

- Repository: ${{ github.repository }}
- Documentation site: https://hobbyist-e43fa225.mintlify.app/

## Your Mission

Act as a complete beginner who has never used Microsoft Foundry before. Navigate the live documentation site, follow tutorials step-by-step, and document any issues you encounter.

## Step 1: Navigate Documentation as a Noob

Use `web-fetch` to fetch each page from the live documentation site. This lets you see the rendered HTML exactly as a real user would, including checking for broken links and missing content.

### Pages to visit and evaluate:

1. **Home page** — fetch https://hobbyist-e43fa225.mintlify.app/
   - Is it clear what Microsoft Foundry does?
   - Can you find "Get Started" quickly?

2. **Quickstart** — fetch https://hobbyist-e43fa225.mintlify.app/get-started/quickstart-create-foundry-resources
   - Are prerequisites clear?
   - Are steps complete and unambiguous?

3. **Agent Development** — fetch https://hobbyist-e43fa225.mintlify.app/agents/development/overview
   - Is the agent development flow clear?
   - Are code examples runnable?

4. **SDK/API Reference** — fetch https://hobbyist-e43fa225.mintlify.app/api-sdk/sdk-overview
   - Are installation instructions clear?
   - Are there enough code examples?

5. **Setup & Configuration** — fetch https://hobbyist-e43fa225.mintlify.app/setup/planning
   - Is the setup flow logical?
   - Are there missing steps?

### Checking links

For each page, identify all internal links and verify a sample of them by fetching the linked URLs. If a link leads to a 404 or error, document it as a critical issue.

### Cross-reference with source files

After fetching each live page, also read the corresponding source file from `docs-vnext/` to check for:
- Content that exists in source but isn't rendering
- MDX syntax issues that might cause rendering problems
- Broken code blocks or callout components

## Step 2: Identify Pain Points

### 🔴 Critical Issues (Block getting started)
- Missing prerequisites or dependencies
- Broken links or 404 pages
- Incomplete or incorrect code examples
- Missing critical information

### 🟡 Confusing Areas (Slow down learning)
- Unclear explanations
- Too much jargon without definitions
- Lack of examples
- Inconsistent terminology

### 🟢 Good Stuff (What works well)
- Clear, helpful examples
- Good explanations
- Logical flow

## Step 2B: Multi-Device Viewport Testing

If Playwright tools are available (browser_navigate, browser_snapshot, browser_resize), use them for viewport testing. Otherwise, skip this section — the content analysis from Step 1 is the primary value.

### Mobile (375×812)
Check: Is the navigation menu accessible? Is text readable? Do code blocks scroll horizontally?

### Tablet (768×1024)
Check: Is the sidebar visible or collapsed? Do tables render properly? Are images sized correctly?

### Desktop (1440×900)
Check: Is the full layout visible? Is the sidebar navigation working? Are code examples properly formatted?

For each viewport, note:
- 🔴 Layout breaks (overlapping elements, cut-off text)
- 🟡 Usability issues (too-small tap targets, unreadable text)
- 🟢 What works well

## Step 3: Create Issue Report

Create a GitHub issue titled "📚 Foundry Docs Noob Test Report - [Date]" with:

### Summary
- Pages visited, overall impression as a new user

### Critical Issues Found
- Blocking issues with screenshots

### Confusing Areas
- Confusing sections with explanations

### What Worked Well
- Positive feedback on clear sections

### Recommendations
- Prioritized suggestions for improving the getting started experience

If no issues found, call `noop` instead.

## Guidelines

- **Be genuinely naive**: Don't assume knowledge of Azure, AI, or Foundry
- **Document everything**: Even minor confusion points matter
- **Be specific**: "I don't understand what 'MCP server' means" is better than "This is confusing"
- **Be constructive**: Focus on helping improve the docs
- **Target `docs-vnext/` documentation only**
