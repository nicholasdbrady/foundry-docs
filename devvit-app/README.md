# Foundry Community Monitor — Devvit App

A Reddit Devvit app that monitors subreddits for Microsoft Foundry / Azure AI discussions and dispatches events to the foundry-docs GitHub repository for documentation impact analysis via agentic workflows.

## Architecture

This integration uses **two complementary Reddit tools**:

```
Reddit Pro (Dashboard)          Devvit App (Automation)
┌──────────────────────┐       ┌──────────────────────┐
│ • Keyword discovery  │──────▶│ • Keyword filter     │
│ • Trend analysis     │       │ • Event triggers     │
│ • Community finder   │       │ • GitHub dispatch    │
│ • Engagement metrics │◀──────│ • Redis dedup        │
│ • Post scheduling    │       │ • Weekly digest      │
└──────────────────────┘       └──────────┬───────────┘
                                          │ repository_dispatch
                                          ▼
                               ┌──────────────────────┐
                               │ GitHub Agentic        │
                               │ Workflow              │
                               │ • MCP doc search      │
                               │ • Gap classification  │
                               │ • Issue creation      │
                               └──────────────────────┘
```

- **Reddit Pro** (free dashboard) handles discovery, analytics, and outbound scheduling
- **Devvit** (this app) handles real-time automation and GitHub integration
- **Agentic workflow** handles documentation analysis using the MCP server

## Prerequisites

1. A Reddit account with [Reddit Pro](https://www.reddit.com/settings/pro) enabled
2. The [Devvit CLI](https://developers.reddit.com/docs/guides/tools/devvit_cli) installed
3. A GitHub Personal Access Token (PAT) with `repo` scope for `repository_dispatch`
4. Moderator access to target subreddits (for app installation)

## Setup

### Step 1: Reddit Pro Discovery

Before deploying the Devvit app, use Reddit Pro to discover your baseline:

1. Go to [Reddit Pro dashboard](https://www.reddit.com/settings/pro)
2. Set up keyword tracking for your target terms (see `REDDIT_PRO_BASELINE.md`)
3. Use the Trends tool to identify which subreddits discuss these topics
4. Use smart keywords to discover related terms
5. Document your findings in `REDDIT_PRO_BASELINE.md`

### Step 2: Configure Secrets

```bash
cd devvit-app

# Set the GitHub PAT (required for repository_dispatch)
npx devvit settings set githubToken

# Optionally configure the target repo (defaults to nicholasdbrady/foundry-docs)
npx devvit settings set githubRepo
```

### Step 3: Install on Subreddits

```bash
# Playtest on your own subreddit first
npx devvit playtest r/YOUR_TEST_SUBREDDIT

# Once verified, upload for production
npx devvit upload
```

Then install the app on each target subreddit. Moderators can customize keywords per-subreddit via the Install Settings page.

### Step 4: Verify

1. Create a test post in a monitored subreddit mentioning a keyword
2. Check the Devvit logs: `npx devvit logs r/YOUR_SUBREDDIT`
3. Verify a `repository_dispatch` event appears in the foundry-docs Actions tab
4. Verify the `reddit-community-monitor` workflow runs and creates an issue (or noop)

## Configuration

### Global Settings (Developer-only)

| Setting | Type | Description |
|---------|------|-------------|
| `githubToken` | Secret | GitHub PAT with `repo` scope |
| `githubRepo` | String | Target repo for dispatch (default: `nicholasdbrady/foundry-docs`) |

### Subreddit Settings (Moderator-configurable)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `keywords` | String | See below | Comma-separated keywords to monitor |
| `enabled` | Boolean | `true` | Enable/disable monitoring in this subreddit |

**Default keywords**: `microsoft foundry, azure openai, azure ai, ai foundry, ai projects sdk, hosted agent, azure ai search, model context protocol`

## Reddit Pro Feedback Loop

After deployment, use Reddit Pro to continuously refine:

1. **Measure keyword effectiveness**: Which keywords produce high-quality documentation signals vs. noise?
2. **Refine subreddit list**: Which subreddits generate the most actionable posts?
3. **Outbound scheduling**: Use Reddit Pro's post scheduler to share doc updates to relevant subreddits when major `docs-vnext/` changes land
4. **Trend detection**: Monitor for new keywords/topics emerging in the community and add them to the Devvit app's settings

See `REDDIT_PRO_BASELINE.md` for the tracking template.

## How It Works

1. **Trigger**: User creates a post/comment in a monitored subreddit
2. **Filter**: Devvit app checks post title + body against configured keywords
3. **Dedup**: Redis prevents duplicate dispatches (7-day TTL per post ID)
4. **Dispatch**: HTTP POST to GitHub `repository_dispatch` with post metadata
5. **Analyze**: Agentic workflow searches foundry-docs MCP for related documentation
6. **Classify**: Agent classifies as doc gap / doc error / FAQ / off-topic
7. **Act**: Creates a `[reddit-community]` issue if documentation-relevant
8. **Heal**: `daily-doc-healer` picks up the issue and proposes documentation fixes

## File Structure

```
devvit-app/
├── README.md                  # This file
├── REDDIT_PRO_BASELINE.md     # Reddit Pro discovery tracking
├── devvit.json                # App config (triggers, scheduler, settings)
├── package.json               # Dependencies
├── server/
│   └── index.ts               # Hono server (triggers, dispatch, dedup, digest)
└── .gitignore
```

## Related Workflows

| Workflow | Role |
|----------|------|
| `reddit-community-monitor.md` | Receives dispatches, analyzes posts via MCP |
| `daily-doc-healer.md` | Scans `[reddit-community]` issues as signal source |
| `community-discussions-monitor.md` | Similar pattern for GitHub Discussions |
