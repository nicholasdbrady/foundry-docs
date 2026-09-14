# Reddit Pro Discovery Baseline

## Overview

This document tracks the Reddit Pro discovery process used to configure the Devvit app's keyword monitoring. Update this document as you refine keywords and subreddits based on Reddit Pro analytics.

## Setup Date

_Fill in when you complete the Reddit Pro setup._

## Keywords Tracked in Reddit Pro

Configure these in Reddit Pro's keyword tracking dashboard:

### Primary Keywords (High Signal)

| Keyword | Expected Volume | Notes |
|---------|----------------|-------|
| `microsoft foundry` | Medium | Core product name |
| `azure ai foundry` | Medium | Previous product name, still commonly used |
| `ai foundry` | High (noisy) | May match non-Azure results; monitor signal quality |
| `azure openai` | High | Major Azure AI service |
| `azure ai` | Very High (noisy) | Broad — use Reddit Pro smart keywords to refine |

### Secondary Keywords (Medium Signal)

| Keyword | Expected Volume | Notes |
|---------|----------------|-------|
| `ai projects sdk` | Low | SDK-specific discussions |
| `hosted agent` | Low-Medium | Foundry hosted agents feature |
| `azure ai search` | Medium | RAG and search integration |
| `model context protocol` | Low-Medium | MCP discussions |

### Discovery Keywords (Use Reddit Pro Smart Keywords)

Use Reddit Pro's smart keywords feature to discover related terms. Add any high-signal discoveries here:

| Discovered Keyword | Source | Added to Devvit? |
|-------------------|--------|-----------------|
| _pending discovery_ | — | — |

## Target Subreddits

Use Reddit Pro's Trends tool and community discovery to identify subreddits. The Devvit app must be installed per-subreddit by moderators.

| Subreddit | Members | Foundry Mentions/Month | Priority | Installed? |
|-----------|---------|----------------------|----------|-----------|
| r/azure | ~300K | _check via Reddit Pro_ | High | ☐ |
| r/MachineLearning | ~3M | _check via Reddit Pro_ | Medium | ☐ |
| r/OpenAI | ~1M+ | _check via Reddit Pro_ | Medium | ☐ |
| r/LocalLLaMA | ~500K | _check via Reddit Pro_ | Low-Medium | ☐ |
| r/artificial | ~400K | _check via Reddit Pro_ | Low | ☐ |
| r/azuredevops | ~50K | _check via Reddit Pro_ | Low | ☐ |

## Analytics Baseline

Export these from Reddit Pro before launching the Devvit app, then compare monthly:

| Metric | Baseline (Pre-Devvit) | Month 1 | Month 2 |
|--------|----------------------|---------|---------|
| Total keyword mentions/week | — | — | — |
| Average post engagement | — | — | — |
| Top subreddit by mentions | — | — | — |
| Sentiment (if available) | — | — | — |

## Feedback Loop Notes

After the Devvit app is running, use Reddit Pro to:

1. **Measure keyword effectiveness**: Which keywords produce documentation-impactful posts vs. noise?
2. **Refine subreddit list**: Which subreddits generate the highest-quality signals?
3. **Outbound scheduling**: Use Reddit Pro's post scheduling to share doc updates to relevant subreddits
4. **Trend detection**: Monitor for new keywords/topics emerging in the community
