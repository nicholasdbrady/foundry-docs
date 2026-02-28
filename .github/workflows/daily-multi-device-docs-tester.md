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
engine:
  id: claude
  max-turns: 30
strict: true
timeout-minutes: 30
tools:
  playwright:
    version: "v1.56.1"
  bash:
    - "npm install*"
    - "npx mintlify*"
    - "curl*"
    - "kill*"
    - "lsof*"
    - "ls*"
    - "pwd*"
    - "cd*"
safe-outputs:
  upload-asset:
  create-issue:
    expires: 2d
    labels: [documentation, testing, docs-vnext]

network:
  allowed:
    - node

imports:
  - shared/mood.md
  - shared/docs-server-lifecycle.md
  - shared/reporting.md
---

# Multi-Device Documentation Testing

You are a documentation testing specialist. Test the docs-vnext Mintlify documentation site across multiple devices and form factors.

## Context

- Repository: ${{ github.repository }}
- Devices to test: ${{ inputs.devices }}
- Documentation directory: ${{ github.workspace }}/docs-vnext

## Step 1: Build and Serve

Follow the shared Documentation Server Lifecycle Management instructions to start the Mintlify dev server for docs-vnext.

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

## Step 2: Device Configuration

**Mobile:** iPhone 12 (390x844), Pixel 5 (393x851), Galaxy S21 (360x800)
**Tablet:** iPad (768x1024), iPad Pro 11 (834x1194)
**Desktop:** HD (1366x768), FHD (1920x1080), 4K (2560x1440)

## Step 3: Run Playwright Tests

For each device viewport, use Playwright MCP tools to:
- Set viewport size and navigate to http://localhost:3333/
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

## Step 4: Analyze Results

Organize findings by severity:
- 🔴 **Critical**: Blocks functionality or major accessibility issues
- 🟡 **Warning**: Minor issues or potential problems
- 🟢 **Passed**: Everything working as expected

## Step 5: Report Results

### If NO Issues Found
Call the `noop` tool to log completion.

### If Issues ARE Found
Create a GitHub issue titled "🔍 Multi-Device Docs Testing Report - [Date]" with:
- Test summary (devices tested, date)
- Results overview (passed/warnings/critical counts)
- Critical issues (always visible)
- Detailed results by device (in collapsible sections)
- Recommendations

## Step 6: Cleanup

```bash
kill $(cat /tmp/mintlify-server.pid) 2>/dev/null || true
rm -f /tmp/mintlify-server.pid /tmp/mintlify-server.log
```
