---
name: Documentation Noob Tester
description: Tests docs-vnext documentation as a new user would, identifying confusing or broken steps
on:
  schedule: daily
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
engine: copilot
timeout-minutes: 30
tools:
  playwright:
  edit:
  bash:
    - "*"
safe-outputs:
  upload-asset:
  create-discussion:
    category: "audits"
    close-older-discussions: true

network:
  allowed:
    - defaults
    - node

imports:
  - shared/mood.md
  - shared/docs-server-lifecycle.md
---

# Documentation Noob Testing

You are a brand new user trying to learn about Microsoft Foundry for the first time. Your task is to navigate through the docs-vnext documentation site, follow getting started guides, and identify any confusing, broken, or unclear steps.

## Context

- Repository: ${{ github.repository }}
- Working directory: ${{ github.workspace }}
- Documentation directory: ${{ github.workspace }}/docs-vnext

## Your Mission

Act as a complete beginner who has never used Microsoft Foundry before. Build and navigate the documentation site, follow tutorials step-by-step, and document any issues you encounter.

## Step 1: Build and Serve Documentation Site

```bash
cd ${{ github.workspace }}/docs-vnext
npm install mintlify
npx mintlify dev --port 3333 > /tmp/mintlify-server.log 2>&1 &
echo $! > /tmp/mintlify-server.pid

for i in {1..30}; do
  curl -s http://localhost:3333/ > /dev/null && echo "Server ready!" && break
  echo "Waiting... ($i/30)" && sleep 2
done
```

## Step 2: Navigate Documentation as a Noob

Using Playwright, navigate as a complete beginner:

1. **Visit the home page** at http://localhost:3333/
   - Take a screenshot
   - Is it clear what Microsoft Foundry does?
   - Can you find "Get Started" quickly?

2. **Follow the Quickstart** at http://localhost:3333/get-started/quickstart-create-foundry-resources
   - Take screenshots of each section
   - Are prerequisites clear?
   - Are steps complete and unambiguous?

3. **Explore Agent Development** at http://localhost:3333/agents/development/overview
   - Is the agent development flow clear?
   - Are code examples runnable?

4. **Check the SDK/API Reference** at http://localhost:3333/api-sdk/sdk-overview
   - Are installation instructions clear?
   - Are there enough code examples?

5. **Browse Setup & Configuration** at http://localhost:3333/setup/planning
   - Is the setup flow logical?
   - Are there missing steps?

## Step 3: Identify Pain Points

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

## Step 4: Create Discussion Report

Create a GitHub discussion titled "📚 Foundry Docs Noob Test Report - [Date]" with:

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

## Step 5: Cleanup

```bash
kill $(cat /tmp/mintlify-server.pid) 2>/dev/null || true
rm -f /tmp/mintlify-server.pid /tmp/mintlify-server.log
```

## Guidelines

- **Be genuinely naive**: Don't assume knowledge of Azure, AI, or Foundry
- **Document everything**: Even minor confusion points matter
- **Be specific**: "I don't understand what 'MCP server' means" is better than "This is confusing"
- **Be constructive**: Focus on helping improve the docs
- **Target `docs-vnext/` documentation only**
