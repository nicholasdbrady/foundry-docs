# Implementation Plan: Foundry Classic → New Documentation Suite

## Problem Statement

Microsoft Foundry's transition from Classic to New creates confusion across eight simultaneous axes (branding, portals, agent API, API versioning, resource model, SDKs, terminology, billing). With NextGen GA launching March 17, 2026, there is no single authoritative documentation resource that helps developers understand what changed, why, and what to do about it. The existing docs cover individual topics but lack the connective tissue — a "Developer Guide to Foundry" narrative, an updated glossary with migration mappings, SDK comparison tables, and a revised overview page that frames the platform through the Discovery → Build → Operate lifecycle.

## Approach

Create a suite of 6 documentation deliverables (5 MDX pages + 1 glossary update) in `docs-vnext/` that work together as a coherent "understand the evolution" layer. Each page is standalone but cross-linked. All follow Mintlify MDX format and Diátaxis conventions.

## Deliverables

### 1. Rewrite `overview/what-is-foundry.mdx` — The Landing Page
- **File:** `docs-vnext/overview/what-is-foundry.mdx` (edit existing)
- **Diátaxis type:** Explanation
- **What changes:**
  - Add "Who is Foundry for?" section with developer personas (app developers, ML engineers, IT admins)
  - Add "How Foundry evolved" section with the 3-line naming timeline (Azure AI Studio → Azure AI Foundry → Microsoft Foundry) and a brief explanation of the model-centric → agent-centric industry shift
  - Restructure body around Discovery → Build → Operate lifecycle instead of feature bullet list
  - Update the portals table to reflect NextGen as default (post-March 17 GA)
  - Remove "How to get access" toggle language (NextGen is now default)
  - Add "Coming from Azure OpenAI?" callout with link to upgrade guide
  - Add "Coming from Hubs?" callout with link to classic docs
  - Fix broken related-content link (line 88 has missing line break)

### 2. New page: `overview/developer-guide.mdx` — The Developer Guide to Foundry
- **File:** `docs-vnext/overview/developer-guide.mdx` (create new)
- **Diátaxis type:** Explanation
- **Purpose:** Single narrative explaining why the platform changed. This is the "customer-facing article on what is happening from classic → new" from the original requirements.
- **Outline:**
  1. **The industry shifted** — model-centric (2023) → agent-centric (2025), pace of model releases, reasoning/tool-calling/multimodal convergence
  2. **What changed and why** — eight axes summarized in a single table (the "Classic vs. New" alignment table from research, simplified for customers)
  3. **The Responses API** — why the wire protocol moved from Assistants to Responses (simpler model, better performance, lower costs, native tools, encrypted reasoning, future-proofing — rewritten in Microsoft voice without naming upstream provider)
  4. **The v1 API** — why monthly api-versions were replaced with stable `/openai/v1/` routes
  5. **One resource, one portal** — Foundry resource replaces Hub + AOAI + AI Services; NextGen replaces Mainline
  6. **Which migration do I need?** — decision tree linking to specific migration guides
  7. **Foundry vs. Copilot Studio vs. M365 Copilot** — persona-based decision framework
- **Nav location:** Add to "What is Microsoft Foundry (new)?" group in `docs.json`

### 3. New page: `overview/classic-vs-new.mdx` — Terminology & Feature Comparison
- **File:** `docs-vnext/overview/classic-vs-new.mdx` (create new)
- **Diátaxis type:** Reference
- **Purpose:** The terminology mapping table + feature comparison matrix. Two tables in one page.
- **Content:**
  - **Terminology mapping table** — Classic Term → New Term → Notes (the full 17-row table from research)
  - **Feature comparison matrix** — Classic portal vs. New portal capabilities (what's available where)
  - **Naming lineage callout** — Cognitive Services → Azure AI Services → Foundry Tools; Azure AI Studio → Azure AI Foundry → Microsoft Foundry
- **Nav location:** Add to "What is Microsoft Foundry (new)?" group in `docs.json`

### 4. New page: `api-sdk/sdk-classic-vs-new.mdx` — SDK Migration Comparison
- **File:** `docs-vnext/api-sdk/sdk-classic-vs-new.mdx` (create new)
- **Diátaxis type:** Reference
- **Purpose:** Side-by-side comparison of classic vs. new SDK patterns with code examples.
- **Content:**
  - **SDK mapping table** — Classic SDK → New SDK → Status → Migration effort
  - **Client library comparison** — `AzureOpenAI()` vs `OpenAI()` with side-by-side code (Python, C#, JS)
  - **API versioning comparison** — monthly `api-version` vs v1 routes with before/after curl examples
  - **Agent SDK comparison** — `create_agent()` vs `create_version()` with before/after Python code
  - **Conversation SDK comparison** — threads vs conversations with before/after Python code
  - **Deprecation notices** — `azure-ai-inference` (retiring May 30, 2026), Assistants API (sunset Aug 26, 2026)
  - Link to existing `api-version-lifecycle.mdx` for full v1 API details
  - Link to existing `migrate.mdx` for full agent migration guide
- **Nav location:** Add to "API & SDK" group in `docs.json`

### 5. Update `glossary.mdx` — Add Migration Mappings & Missing Terms
- **File:** `docs-vnext/glossary.mdx` (edit existing)
- **What changes:**
  - Add missing terms: Conversation, Foundry Tools, Foundry Resource, Foundry Project, Items, Responses API, v1 API, Classic (portal), New (portal), Agents v2, Workflow Agent, Hosted Agent, Foundry Control Plane, Foundry Direct Models, Agent Framework
  - Add "See also" cross-references for deprecated terms: Thread → see Conversation, Run → see Response, Assistant → see Agent, Azure AI Services → see Foundry Tools, Azure AI Studio → see Microsoft Foundry, Hub → see Foundry Resource
  - Remove foundry-docs MCP server-specific terms that don't belong in customer-facing glossary (Devvit, Redis, repository_dispatch, Content Chunking, Hit@K, HNSW, MRR, TF-IDF, SearchIndex, Semantic Reranking, MCP Gateway, FastMCP, MDX, Mintlify, Telemetry, docs-vnext, Diátaxis, Embeddings as implementation detail, Hybrid Search as implementation detail)

### 6. Update `docs.json` navigation — Wire New Pages Into Nav
- **File:** `docs-vnext/docs.json` (edit existing)
- **What changes:**
  - Add `overview/developer-guide` and `overview/classic-vs-new` to the "What is Microsoft Foundry (new)?" group
  - Add `api-sdk/sdk-classic-vs-new` to the "API & SDK" group
  - Consider renaming top nav group from "What is Microsoft Foundry (new)?" to "What is Microsoft Foundry?" (drop the "(new)" since NextGen is now GA default)

## Notes

- All new pages follow Mintlify MDX format per `.github/instructions/documentation.instructions.md`
- All new pages use Diátaxis framework (explanation for narrative, reference for tables)
- Code samples are minimal, focused, copy-paste ready with ALL_CAPS placeholders
- No promotional language; neutral technical tone
- Content is drawn from the research report at `~/.copilot/session-state/.../research/i-m-having-a-problem-with-explaining-the-technical.md`
- The developer guide blog post mentioned in research is separate from these docs pages and not part of this implementation
