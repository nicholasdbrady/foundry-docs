# RFC: Navigation Reflow for docs-vnext

**Status:** Implemented  
**Date:** March 4, 2026  
**Author:** Nicholas Brady  

---

## 1. Summary

This RFC documents the rationale, evidence, and decisions behind restructuring the Microsoft Foundry `docs-vnext` navigation from 18 top-level groups to 10 product-pillar-aligned groups. The reflow reduces cognitive load for developers, aligns the documentation with Foundry's strategic positioning as an agent development platform, and improves discoverability for IDE coding agents — all while preserving 100% of existing content (273 unique pages, zero deletions).

---

## 2. Motivation

### 2.1 Strategic context

Microsoft Foundry is positioned as an **agent development platform** comprising five product pillars:

| Product Pillar | Description |
|---------------|-------------|
| **Foundry Agent Service** | Central runtime for building, deploying, and operating AI agents. Manages conversations, orchestrates tool calls, enforces content safety. |
| **Foundry Models** | Model catalog, deployment, inference, fine-tuning, and performance management across Azure OpenAI, Foundry Direct, and partner models. |
| **Foundry Tools** | Tool catalog (1,400+ MCP servers, OpenAPI, custom tools) and pre-built AI services (Speech, Vision, Language, Content Safety). |
| **Foundry IQ** | Managed knowledge layer that turns enterprise data into reusable, permission-aware knowledge bases for agents. |
| **Foundry Control Plane** | Unified fleet-wide governance, observability, evaluation, and compliance management for agents, models, and tools. |

These product names appear throughout the documentation *content* (page titles, descriptions, body text) but were absent from the navigation *structure*. The documentation sidebar used organizational categories ("Agent development," "Agent tools & integration," "Model catalog," "Model capabilities") that don't match how the product is marketed, sold, or explained to developers.

### 2.2 Competitive evidence

A comparative analysis of Anthropic, OpenAI, and Google Gemini API documentation (conducted March 2026 from live production sites) revealed strong convergence on documentation architecture patterns:

| Metric | Anthropic | OpenAI | Gemini | Foundry (before) |
|--------|-----------|--------|--------|-------------------|
| Top-level sections | 7 | 6 | 8 | **18** |
| Max nesting depth | 3 | 2 | 2 | **4** |
| Total pages (est.) | ~50 | ~60 | ~45 | **273** |
| Code above the fold | Every page | Every page | Every page | **20% of pages** |
| SDK languages per example | 3-4 | 4 | 6 | **1-2** |
| Time to first API call | < 2 min | < 2 min | < 2 min | **10+ min** |

**Sources:** Anthropic sidebar reconstructed from [docs.anthropic.com](https://docs.anthropic.com) and [platform.claude.com/docs](https://platform.claude.com/docs). OpenAI sidebar reconstructed from [developers.openai.com](https://developers.openai.com) search index and page content. Gemini sidebar captured from [ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs) live navigation.

Three universal patterns emerged from competitors:

1. **Flat, task-oriented navigation.** Section titles describe what developers *do* ("Text generation," "Function calling," "Deploy models") rather than what organizational group owns the content ("Model capabilities," "Agent tools & integration").

2. **Code-first pages.** Every guide page leads with a minimal, runnable code snippet before any conceptual explanation. Multi-language code tabs (Python, JavaScript, C#, REST at minimum) are standard.

3. **Agents and tools as first-class sections.** All three platforms treat agents/tools as top-level navigation peers to models — not subordinate to them.

### 2.3 Problems with the previous structure

Five structural problems were identified through the comparative analysis and page inventory:

**Problem 1: Product pillars didn't drive the navigation.** A developer reading Foundry marketing about "Foundry Agent Service" found no matching section in the docs sidebar. The navigation used abstract categories instead.

**Problem 2: Agent content was artificially split.** Agent Service content spanned two top-level groups: "Agent development" (24 pages for concepts, hosting, publishing) and "Agent tools & integration" (33 pages for tools, protocols, knowledge). No competitor splits agent development from agent tooling.

**Problem 3: Model content was fragmented into three groups.** "Model catalog" (24 pages), "Model capabilities" (40 pages), and "Fine-tuning" (10 pages) covered related content under three separate top-level headings. Every competitor uses a single "Models" section.

**Problem 4: Observability was scattered across three groups.** Agent tracing appeared under "Agent development." Model monitoring appeared under "Observability, evaluation, & tracing." Fleet-level monitoring appeared under "Manage agents, models, & tools." This reflected the reality that evaluation and tracing apply at both the model and agent level — but the navigation didn't acknowledge this dual nature. Instead, it scattered the content without clear scoping.

**Problem 5: Platform/governance sections overwhelmed the sidebar.** Setup (21 pages) + Security (21 pages) + Guardrails (15 pages) + Responsible AI (9 pages) + Operate (7 pages) + Manage (9 pages) = 82 pages across 6 top-level groups. This is more pages than the *entire* Anthropic documentation, devoted to running the platform rather than building with it.

---

## 3. Design Decisions

### Decision 1: Use product pillar names as navigation groups

**Rationale:** Product names in navigation eliminate the translation gap between marketing materials, portal UI, and documentation. When a developer sees "Foundry Agent Service" in a blog post or portal, they find the same words in the docs sidebar.

**Trade-off considered:** Generic names like "Agents" or "Models" (matching competitors) vs. branded names like "Foundry Agent Service" or "Foundry Models." We chose branded names because Foundry's product pillars are meaningful nouns that developers already encounter — and because the branded names reinforce platform identity without adding length.

### Decision 2: Merge Control Plane + Observability into one section

**Rationale:** The Control Plane's stated purpose is fleet-wide visibility, governance, and control. Observability (evaluation, tracing, monitoring) *is* the visibility layer. Separating them would reproduce the same fragmentation that plagued the previous structure.

The merged section acknowledges the dual-scoped nature of evaluation and tracing by introducing explicit "Agent observability" and "Model observability" subgroups within the Control Plane:

```
Foundry Control Plane
├── Agent observability (metrics, dashboards, tracing)
├── Model observability (monitor models, optimization dashboard)
├── Evaluators (built-in, RAG, safety, agent, custom)
├── Run evaluations (batch, cloud, results, cluster analysis)
├── Red teaming
├── CI/CD evaluations
├── Govern agents (fleet management, registration)
├── Govern models (limits, guardrail policies, cost optimization)
├── Compliance & AI gateway
```

**Trade-off considered:** Keeping "Evaluation & observability" separate (as originally proposed in the first research iteration) vs. merging into Control Plane. The merge was chosen because: (1) the Control Plane overview page literally defines itself as providing "observability"; (2) separating them creates an ambiguity about where agent metrics live; and (3) the combined section (38 pages) is comparable in size to "Foundry Models" (72 pages) and "Platform" (40 pages), so it doesn't dominate the sidebar.

### Decision 3: Merge three model groups into one

**Rationale:** The distinction between "what models exist" (catalog), "what they can do" (capabilities), and "how to customize them" (fine-tuning) is an internal organizational distinction. A developer asking "how do I use GPT-5 with function calling" doesn't care which team owns the catalog vs. capabilities doc.

Competitors validate this: OpenAI has a single "Models" page plus capability-specific guides. Gemini has "Models" + "Core capabilities." Neither has three separate top-level groups.

The merged "Foundry Models" section uses subgroups to preserve the logical structure:

```
Foundry Models (72 pages)
├── Model catalog (Azure OpenAI + partner models)
├── Choose a model (selection guides)
├── Model router
├── Deploy models
├── Generate text (chat completions, responses, reasoning, ...)
├── Vision and image
├── Audio and speech
├── Scale inference (throughput, priority, benchmarks)
├── Fine-tuning
└── Integrate (webhooks, playgrounds)
```

### Decision 4: Merge six governance/platform groups into two

**Rationale:** 82 pages of platform/governance content across 6 groups overwhelmed the sidebar. Merging into "Safety & guardrails" (23 pages) and "Platform" (40 pages) cuts the navigation noise in half while preserving every page.

- **Safety & guardrails** merges "Guardrails and controls" + "Responsible AI" — these share the same concern (safe AI outputs) and audience (developers configuring safety).
- **Platform** merges "Setup & configure" + "Security & governance" — these share the same concern (infrastructure) and audience (platform engineers/IT admins).

### Decision 5: Use jobs-to-be-done subgroup titles

**Rationale:** Section titles should describe what a developer *does*, not what a team *owns*. This matches all three competitor patterns and improves LLM agent routing (a coding agent searching for "how to generate text" should match a section called "Generate text," not "Chat completions & Responses APIs").

| Previous title | New title | Rationale |
|---------------|-----------|-----------|
| "Core concepts" | "How agents work" | Task-oriented; answers "what will I learn?" |
| "Chat completions & Responses APIs" | "Generate text" | Describes the job, not the API name |
| "Performance and throughput" | "Scale inference" | Imperative verb; what you're trying to do |
| "Model selection and management" | "Choose a model" | Direct action |
| "Overview of agent tools" | "Manage tools" | Active verb |
| "Publishing and sharing" | "Publish agents" | Simpler, active |
| "Configuration and policies" | "Configure policies" | Shorter, active |
| "Connect services and tools" | "Connect data sources" | More specific |
| "High availability and disaster recovery" | "Disaster recovery" | Concise |

### Decision 6: Add code-above-the-fold to high-impact pages

**Rationale:** All three competitors lead every guide page with runnable code. Of 173 Foundry pages containing code blocks, only 55 had code in the first 50 lines after frontmatter. 118 pages buried code below conceptual prose.

The initial implementation added `<CodeGroup>` snippets (Python + TypeScript) to the 18 highest-impact pages:
- 8 model capability pages (responses, reasoning, function-calling, structured-outputs, embeddings, batch, prompt-caching, web-search)
- 7 agent tool pages (code-interpreter, file-search, web-search, function-calling, MCP, ai-search, memory)
- 3 agent service pages (overview, workflow, quickstart-hosted-agent)

### Decision 7: Navigation-only changes; no file moves

**Rationale:** Mintlify decouples file paths from navigation structure — any `.mdx` file can appear in any navigation group regardless of its directory location. By changing only `docs.json`, we avoid:
- Breaking external links and bookmarks
- Disrupting MCP server path mappings
- Losing git blame history on moved files
- Creating merge conflicts with in-flight content work

File path restructuring (moving files to match the new navigation) can be a separate, lower-risk follow-up.

---

## 4. Result

### Before vs. After

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Top-level groups | 18 | 10 | **-44%** |
| Max nesting depth | 4 levels | 3 levels | **-1 level** |
| Total unique pages | 273 | 273 | **0 pages lost** |
| Product pillar names in nav | 0 | 4 | **+4** |
| Duplicate page references | 5 | 0 | **Fixed** |
| Pages with code above fold | 55 | 65 | **+18%** |

### New navigation structure

```
Documentation
├── Overview (3 pages)
├── Get started (4 pages)
├── Foundry Agent Service (19 pages)
│   ├── How agents work
│   ├── Hosted agents
│   ├── System messages
│   └── Publish agents
├── Foundry Models (72 pages)
│   ├── Model catalog
│   ├── Choose a model
│   ├── Model router
│   ├── Deploy models
│   ├── Generate text
│   ├── Embeddings
│   ├── Vision and image
│   ├── Audio and speech
│   ├── Scale inference
│   ├── Benchmark models
│   ├── Integrate
│   └── Fine-tuning
├── Foundry Tools (33 pages)
│   ├── Manage tools
│   ├── Built-in tools
│   ├── Memory
│   ├── Knowledge and retrieval
│   ├── Foundry IQ
│   ├── Voice and speech
│   └── Protocols
├── Foundry Control Plane (38 pages)
│   ├── Agent observability
│   ├── Model observability
│   ├── Evaluators
│   ├── Run evaluations
│   ├── Red teaming
│   ├── CI/CD evaluations
│   ├── Govern agents
│   ├── Govern models
│   └── Compliance & AI gateway
├── Safety & guardrails (23 pages)
│   ├── Content filters
│   ├── Custom controls
│   ├── Configure policies
│   └── Responsible AI
├── Platform (40 pages)
│   ├── Manage Foundry resources
│   ├── Agent configuration
│   ├── Connect data sources
│   ├── Quotas and limits
│   ├── Identity and access
│   ├── Network security
│   ├── Data protection
│   ├── Policy management
│   └── Disaster recovery
├── Developer experience (16 pages)
│   ├── Agent development tools
│   ├── Foundry MCP Server
│   └── Best practices
└── Reference (25 pages)
    ├── API & SDK
    └── Operate & support
```

### GA functionality audit

Every generally available feature verified as represented in the new navigation:

| Feature Area | Pages | Status |
|-------------|-------|--------|
| Chat completions | 1 | ✅ Foundry Models > Generate text |
| Responses API | 1 | ✅ Foundry Models > Generate text |
| Function calling | 2 | ✅ Foundry Models + Foundry Tools > Protocols |
| Structured outputs | 1 | ✅ Foundry Models > Generate text |
| Reasoning | 1 | ✅ Foundry Models > Generate text |
| Batch processing | 1 | ✅ Foundry Models > Generate text |
| Embeddings | 1 | ✅ Foundry Models > Embeddings |
| Fine-tuning (all variants) | 10 | ✅ Foundry Models > Fine-tuning |
| Image generation (DALL-E) | 2 | ✅ Foundry Models > Vision and image |
| Video generation | 3 | ✅ Foundry Models > Vision and image |
| Realtime audio | 6 | ✅ Foundry Models > Audio and speech |
| Speech-to-text / Text-to-speech | 3 | ✅ Foundry Models > Audio and speech |
| Model deployment | 4 | ✅ Foundry Models > Deploy models |
| Provisioned throughput | 3 | ✅ Foundry Models > Scale inference |
| Model router | 2 | ✅ Foundry Models > Model router |
| Code interpreter | 2 | ✅ Foundry Tools > Built-in tools |
| File search | 1 | ✅ Foundry Tools > Built-in tools |
| Web search | 1 | ✅ Foundry Tools > Built-in tools |
| Azure AI Search | 1 | ✅ Foundry Tools > Knowledge and retrieval |
| SharePoint / Bing / Fabric | 3 | ✅ Foundry Tools > Knowledge and retrieval |
| Vector stores | 1 | ✅ Foundry Tools > Knowledge and retrieval |
| MCP support | 3 | ✅ Foundry Tools > Protocols |
| OpenAPI tools | 1 | ✅ Foundry Tools > Protocols |
| Agent publishing (M365, Teams) | 4 | ✅ Foundry Agent Service > Publish agents |
| Tracing | 3 | ✅ Foundry Control Plane > Agent observability |
| Evaluations | 14 | ✅ Foundry Control Plane > Evaluators + Run evaluations |
| Content filters | 6 | ✅ Safety & guardrails > Content filters |
| Blocklists | 1 | ✅ Safety & guardrails > Custom controls |
| RBAC / Identity | 5 | ✅ Platform > Identity and access |
| Network security | 3 | ✅ Platform > Network security |
| Azure Policy | 3 | ✅ Platform > Policy management |
| Disaster recovery | 4 | ✅ Platform > Disaster recovery |

All preview features (hosted agents, memory, Foundry IQ, tool catalog, browser automation, computer use, voice integration, A2A protocol, Foundry Control Plane, Foundry MCP Server, AI Red Teaming Agent, custom code interpreter) are also preserved at their respective locations.

---

## 5. Competitive alignment summary

The new structure maps cleanly to competitor documentation surfaces while preserving Foundry's unique differentiators:

| Foundry Section | Anthropic Equivalent | OpenAI Equivalent | Gemini Equivalent |
|----------------|---------------------|-------------------|-------------------|
| Foundry Agent Service | Build with Claude + Agents & Tools | Guides (Agents, Conversation state) | Tools and agents |
| Foundry Models | About Claude (models) | Models + Guides (Text, Vision, Audio) | Models + Core capabilities |
| Foundry Tools | Agents & Tools (server/client tools) | Built-in tools | Tools and agents |
| Foundry Control Plane | Administration (1 page) | RBAC guide | *(no equivalent)* |
| Safety & guardrails | *(woven into features)* | Data handling guide | Policies |
| Platform | *(API key only, no setup)* | *(API key only)* | Get started (API key) |

**Foundry-unique sections with no competitor equivalent:**
- **Foundry IQ** (managed knowledge retrieval) — nested under Foundry Tools
- **Foundry Control Plane** (fleet governance + evaluation) — no competitor has fleet-wide agent management
- **Evaluation suite** (24 pages of evaluators, red teaming, CI/CD integration) — OpenAI has 1 page; Anthropic and Gemini have none
- **Platform** (42 pages of Azure infrastructure configuration) — competitors are API-key-only SaaS; Foundry's Azure integration requires this content

These sections represent necessary, defensible documentation obligations that competitors don't face. They should not be cut — they should be organized to not overwhelm the developer-facing sections.

---

## 6. Follow-up work

This RFC covers the navigation restructuring and initial code-above-the-fold additions. Remaining work:

1. **Code-above-the-fold for remaining pages.** 108 pages still have code buried below conceptual prose. These should be addressed incrementally, prioritizing by traffic.

2. **Feature availability matrix page.** Anthropic's `Build with Claude > Overview` page shows a single table of ALL capabilities with platform availability columns. Foundry should create an equivalent.

3. **File path restructuring.** File paths currently don't match navigation groups (e.g., agent tools are at `agents/tools/` but appear under "Foundry Tools" top-level). This is cosmetic — Mintlify handles it — but aligning paths would improve developer experience when browsing the repository directly.

4. **OpenAI compatibility guide.** Gemini has an explicit migration guide for developers coming from OpenAI. Foundry supports the OpenAI API surface and should document the mapping explicitly.

---

## Appendix A: Methodology

### Data collection

- **Anthropic:** Navigation reconstructed from multiple page fetches against [docs.anthropic.com](https://docs.anthropic.com) and [platform.claude.com/docs](https://platform.claude.com/docs) (March 4, 2026). Client-rendered SPA required content extraction rather than DOM scraping.
- **OpenAI:** Navigation reconstructed from [developers.openai.com](https://developers.openai.com) Algolia search index (6,415 indexed pages) combined with direct page fetches. Hierarchy levels extracted from search result metadata.
- **Gemini:** Full sidebar captured from [ai.google.dev/gemini-api/docs/text-generation?hl=en](https://ai.google.dev/gemini-api/docs/text-generation?hl=en) which renders the complete navigation tree.
- **Foundry:** Parsed directly from `docs-vnext/docs.json` Mintlify configuration file.

### Page inventory

All page counts derived from the `docs.json` navigation configuration. A Python script collected all page references, identified duplicates, and cross-referenced against `.mdx` files on disk. The validation confirmed 273 unique pages before and after the reflow.

### Code analysis

A shell script analyzed all 274 `.mdx` files for code block presence using `awk` pattern matching on fenced code block markers (`` ``` ``). "Code above the fold" was defined as a code block appearing within the first 50 non-frontmatter lines of a file.

Results: 173 files contained code blocks. 55 had code above the fold. 118 had code buried below conceptual prose. 101 files had no code blocks at all (concept pages, reference pages, portal-only guides).
