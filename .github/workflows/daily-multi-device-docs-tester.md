---
name: Multi-Device Docs Tester
description: Tests docs-vnext documentation site across multiple device form factors for responsive design
on:
  schedule: daily
  workflow_dispatch:
    inputs:
      devices:
        description: 'Device types to test (comma-separated: mobile,tablet,desktop)'
        required: false
        default: 'mobile,tablet,desktop'
  skip-if-match: 'is:issue is:open in:title "Multi-Device Docs Testing"'
  stop-after: "+30d"
permissions:
  contents: read
  issues: read
  pull-requests: read
tracker-id: daily-multi-device-docs-tester
engine: copilot
strict: true
timeout-minutes: 20
tools:
  playwright:
    version: "v1.56.1"
  bash:
    - "cat *"
    - "ls*"
safe-outputs:
  upload-asset:
  create-issue:
    expires: 2d
    labels: [documentation, testing, docs-vnext]
  noop:

network:
  allowed:
    - defaults
    - hobbyist-e43fa225.mintlify.app
    - learn.microsoft.com
    - github.com

imports:
  - shared/mood.md
  - shared/reporting.md
---

# Multi-Device Documentation Testing

You are a documentation testing specialist. Test the deployed docs-vnext Mintlify documentation site across multiple devices and form factors.

## Context

- Repository: ${{ github.repository }}
- Devices to test: ${{ inputs.devices }}
- Documentation site: https://hobbyist-e43fa225.mintlify.app/

## Step 1: Device Configuration

**Mobile:** iPhone 12 (390x844), Pixel 5 (393x851), Galaxy S21 (360x800)
**Tablet:** iPad (768x1024), iPad Pro 11 (834x1194)
**Desktop:** HD (1366x768), FHD (1920x1080), 4K (2560x1440)

## Step 2: Run Playwright Tests

For each device viewport, use Playwright MCP tools to:
- Set viewport size and navigate to https://hobbyist-e43fa225.mintlify.app/
- Take screenshots
- Test navigation, search, and interactive elements
- Check for layout issues (overflow, truncation, broken layouts)
- Verify Mintlify sidebar navigation works correctly on all sizes

Key pages to test:
- Home page
- Get Started quickstart
- Agent development overview
- API/SDK reference
- Setup & configuration

## Step 3: Analyze Results

Organize findings by severity:
- 🔴 **Critical**: Blocks functionality or major accessibility issues
- 🟡 **Warning**: Minor issues or potential problems
- 🟢 **Passed**: Everything working as expected

## Step 4: Report Results

### If NO Issues Found
Call the `noop` tool to log completion.

### If Issues ARE Found
Create a GitHub issue titled "🔍 Multi-Device Docs Testing Report - [Date]" with:
- Test summary (devices tested, date)
- Results overview (passed/warnings/critical counts)
- Critical issues (always visible)
- Detailed results by device (in collapsible sections)
- Recommendations
