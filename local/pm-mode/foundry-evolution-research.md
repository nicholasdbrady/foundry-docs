# Untangling Microsoft Foundry: A Framework for Communicating the Classic → New Evolution

## Executive Summary

Microsoft Foundry's messaging challenge stems from **eight simultaneous transitions** happening across branding, APIs, API versioning, portals, SDKs, resource models, terminology, and billing — all driven by a fundamental industry shift from a model-centric to an agent-centric world. These transitions are governed by a **four-phase migration plan** (NextGen GA March 17 → AOAI migration through March 2027 → Hub deprecation → Legacy retirement) that sequences the customer impact across distinct cohorts: FDP users first, AOAI users second, Hub/Foundry Tools users third, and full legacy retirement last[^18]. This report maps each transition dimension, identifies the specific conflation points, proposes a structured communication framework anchored in Dennis Drews' Build 2025 recap, and provides actionable recommendations aligned to each migration phase. Key stakeholder domains: Bala (Foundry API), Dan (Foundry SDKs), Jeff (Agent Service), Marco (horizontal platform). The core recommendation: **treat each transition axis independently in documentation, but present them through a unified "Classic → New" lens** with a single entry point that lets customers self-select into the migration path(s) relevant to them.

---

## Why Everything Changed: The Model-Centric to Agent-Centric Shift

Before diving into the eight axes of transition, it is critical to frame **why** these changes happened. The technical debt and messaging complexity are not accidents — they are the natural consequence of an industry that moved faster than any platform could organically evolve.

### The pace of change

The AI industry underwent a phase transition between 2023 and 2025:

| Era | Cadence | Paradigm | Platform Response |
|-----|---------|----------|-------------------|
| **2023** | Major model release every ~6 months (GPT-4, GPT-4 Turbo) | **Model-centric**: Models are the product. Developers consume inference APIs. | Azure AI Studio launched as a model playground and experimentation environment. Monthly `api-version` parameters (e.g., `2024-03-01-preview`) to track each incremental API feature. |
| **2024 (early)** | Model releases every ~2–3 months (GPT-4o, o1-preview) | **Model-centric → transitional**: Models gain multimodal capabilities. Reasoning emerges with o1-preview (Sept 2024). Tool-calling and instruction-following improve dramatically. | Azure AI Studio rebranded to Azure AI Foundry — reflecting the shift from "studio" (experimentation) to "foundry" (production factory). Monthly API versions proliferate — 12+ preview versions per year, each requiring code and environment variable updates. |
| **2025** | Multiple model releases every ~6 days (GPT-4.1, o3, o4-mini, GPT-image-1, Codex) | **Agent-centric**: Models become infrastructure. Agents — compositions of models, tools, memory, and orchestration — are the product. | Microsoft Foundry launched: unified resource model, Responses API (replacing Assistants), v1 API routes (replacing monthly versions), Foundry-as-a-service. The platform had to evolve from "serve a model" to "operate an agent factory." |

### What drove the shift

Starting October 2024 and accelerating through 2025, several capabilities converged to make models **infrastructure** rather than **products**:

- **Advanced reasoning** (o1-preview Sept 2024 → o1 Dec 2024 → o3/o4-mini 2025): Models that can plan, decompose tasks, and self-correct made autonomous agent behavior viable.
- **Improved tool-calling**: Models became reliable enough at structured function calling to be trusted with real-world tool execution — APIs, databases, code interpreters — without constant human oversight.
- **Enhanced instruction following**: System prompt fidelity improved to the point where agents could maintain persona, follow constraints, and operate within guardrails across long conversations.
- **Multimodal capabilities**: Vision, audio, and image generation collapsed into single model families, enabling agents that perceive and act across modalities.

This is the context that makes every transition axis below understandable: Microsoft wasn't changing things for the sake of change. The industry moved from a world where "deploy a model, call an API" was the entire workflow, to one where models are one component in a multi-agent system requiring orchestration, state management, governance, and observability. The platform had to evolve to match.

### The API versioning crisis

The monthly API version pattern (`2024-03-01-preview`, `2024-04-01-preview`, ..., `2025-04-01-preview`) was sustainable when models shipped every 6 months. When model releases accelerated to days rather than months, and each release brought new API features, the monthly cadence became a treadmill for developers. The v1 API is the direct answer to this crisis.

---

## The Eight Axes of Transition

The confusion is not a single problem — it is eight overlapping transitions that customers experience simultaneously. Each axis is independent but interacts with the others, creating a combinatorial explosion of possible customer states.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    MICROSOFT FOUNDRY EVOLUTION                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. BRANDING         Azure AI Studio → Azure AI Foundry →            │
│                      Microsoft Foundry                                │
│                                                                      │
│  2. PORTAL UX        Mainline (Classic) ←→ NextGen (New)             │
│                                                                      │
│  3. AGENT API        Assistants API → Agents v0.5/v1 → Agents v2    │
│                      (wire protocol: Assistants → Responses)          │
│                                                                      │
│  4. API VERSIONING   Monthly api-version params → v1 stable routes   │
│                      (AzureOpenAI client → OpenAI client)             │
│                                                                      │
│  5. RESOURCE MODEL   Hub + Azure OpenAI + AI Services →              │
│                      Foundry Resource (unified)                       │
│                                                                      │
│  6. SDK STACK        AI Inference + AI Generative + AOAI SDK →       │
│                      AI Projects SDK + OpenAI SDK + Foundry Tools     │
│                                                                      │
│  7. TERMINOLOGY      Threads/Messages/Runs →                         │
│                      Conversations/Items/Responses                    │
│                                                                      │
│  8. BILLING          Model-as-a-Service (MaaS) →                     │
│                      Foundry Direct Models                            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Axis 1: Branding Evolution

### Timeline

| Date | Brand | Key Event |
|------|-------|-----------|
| November 2023 | **Azure AI Studio** | Public preview launch |
| November 2024 | **Azure AI Foundry** | Rebranding at Ignite 2024; "agent factory" positioning |
| May 2025 | **Azure AI Foundry** | Build 2025 — new Foundry resource type, Foundry API, Foundry projects announced[^1] |
| November 2025 | **Microsoft Foundry** | Ignite 2025 — elevated from Azure sub-brand to core Microsoft pillar alongside M365 and Azure[^2] |

### Why This Causes Confusion

- Customers searching for "Azure AI Foundry" find content from three different eras
- Documentation still uses "Azure AI Foundry" in many places (the `what-is-foundry.mdx` page opens with a tip: "Azure AI Foundry is now Microsoft Foundry. Screenshots appearing throughout this documentation are in the process of being updated.")[^3]
- The Azure resource type is still `Microsoft.CognitiveServices/accounts` with `kind: 'AIServices'` — there is no "Microsoft.Foundry" resource provider yet[^4]
- The portal URL remains `ai.azure.com`, not a Microsoft Foundry-branded URL

### Recommendation

Create a "Name History" callout that appears once, early, in the "What is Foundry" page:

> **A note on naming:** Azure AI Studio (2023) → Azure AI Foundry (2024) → Microsoft Foundry (2025). All three names refer to the same evolving platform. The Azure resource type is `Microsoft.CognitiveServices/accounts`. This documentation uses "Microsoft Foundry" or simply "Foundry."

---

## Axis 2: Portal UX — Classic vs. New (NextGen)

### Current State

The docs-vnext `what-is-foundry.mdx` already defines the two portals clearly[^3]:

| Portal | Internal Name | Who Should Use It |
|--------|--------------|-------------------|
| **Microsoft Foundry (classic)** | "Mainline" | Working with multiple resource types: Azure OpenAI, Foundry resources, hub-based projects, or Foundry projects |
| **Microsoft Foundry (new)** | "NextGen" | Seamless experience for multi-agent applications. Only Foundry projects visible. |

A toggle in the portal banner switches between the two.

### Key Differences

| Dimension | Classic (Mainline) | New (NextGen) |
|-----------|-------------------|---------------|
| Resource visibility | All resource types (AOAI, Hubs, Foundry) | Foundry projects only |
| Navigation | Customizable left pane, Management Center | Streamlined, project selector in upper-left |
| Agent experience | Agents v0.5/v1 (Assistants-based) | Agents v2 (Responses-based) |
| Multi-agent workflows | Not available | SDK-based orchestration (C#, Python) |
| Tool catalog | Limited | 1,400+ tools, public/private catalogs |
| Memory | Not available | GA |
| Foundry IQ | Not available | Preview |
| Performance | Standard | Faster load times, dynamic prefetching |

### Conflation Point

The term "Mainline" is an internal code name that has leaked into some customer-facing contexts. Customers don't know what "Mainline" means. The `what-is-foundry.mdx` correctly uses "(classic)" and "(new)" labels[^3], but the internal naming ("Mainline OAI sub-studio" and "NextGen") from the alignment table needs to be systematically replaced.

### Recommendation

- **Label Mainline as "Classic" in all customer-facing content** — NextGen GA is March 13 (announced March 17)[^18]. This is now.
- The docs-vnext already does this well — ensure Foundry (classic) docs match
- Create a feature support matrix table comparing Classic vs New portal capabilities (partially exists in the `what-is-foundry.mdx` page but not as a dedicated comparison)
- **Phase 1 nuance:** Hub projects + AOAI-only resources remain Mainline-only. NextGen shows only Foundry projects. Document the toggle-back flow clearly.
- **Phase 2 risk to document:** NextGen provides same *functionality* as OAI sub-studio but not same *API surface in UX* (Agents instead of Assistants, Foundry evals instead of OAI evals, AI Search index instead of OAI vector store). The underlying API still supports all legacy patterns — this distinction must be made clear to avoid DSAT.

---

## Axis 3: Agent API Evolution

This is the deepest source of technical confusion. There are effectively **four generations** of agent API in the Foundry ecosystem:

### Lineage

```
OpenAI Assistants API (beta)
    │
    ├── Azure OpenAI Assistants API (Agents v0.5)
    │       Wire protocol: Assistants API
    │       Objects: Assistants, Threads, Messages, Runs
    │       SDK: client.beta.assistants.create()
    │
    ├── Azure AI Agent Service (Agents v1)
    │       Wire protocol: Assistants API (with extensions)
    │       Objects: Agents, Threads, Messages, Runs
    │       SDK: project_client.agents.create_agent()
    │
    └── Foundry Agent Service (Agents v2)
            Wire protocol: Responses API
            Objects: Agent Versions, Conversations, Items, Responses
            SDK: project_client.agents.create_version()
                 openai_client.conversations.create()
                 openai_client.responses.create()
```

### Critical Context: Why the Wire Protocol Changed

The Assistants API — the wire protocol underpinning Agents v0.5 and v1 — has been **formally deprecated with a sunset date of August 26, 2026**[^5]. This is not a Microsoft decision — the upstream API provider is sunsetting the protocol that Foundry's classic agents were built on. Microsoft's move to the Responses API for Agents v2 is therefore both a feature upgrade and a forced migration.

The upstream provider's own documentation, SDKs, cookbooks, and blog posts articulate seven clear reasons for the migration. These reasons apply directly to Foundry customers and should be incorporated (in Microsoft's voice) into customer-facing messaging:

#### 1. Simpler Mental Model

The Assistants API required managing four tightly-coupled objects: Assistants, Threads, Messages, and Runs. Runs were asynchronous processes requiring polling loops. The Responses API replaces this with a single pattern: **send input items, get output items back**[^15]. No polling, no run status checks, no async orchestration complexity. In the upstream migration guide, this is described as moving to "a simpler and more flexible mental model"[^16].

#### 2. Better Performance with Reasoning Models

The Responses API delivers measurably better model intelligence when using reasoning models (o3, o4-mini, GPT-5). Upstream internal evaluations show a **3% improvement on SWE-bench** with the same prompt and setup, compared to the older Chat Completions API[^15]. This improvement comes from the Responses API's ability to preserve and reuse reasoning items across tool-calling turns — something the Assistants API could not do.

The upstream cookbook on reasoning items explains the mechanism: when a reasoning model makes a tool call, the reasoning tokens from before the tool call are critical context for interpreting the tool's output. The Responses API preserves these automatically via `previous_response_id` or explicit inclusion in subsequent input items[^17].

#### 3. Lower Costs via Cache Utilization

The Responses API achieves **40% to 80% improvement in cache utilization** compared to Chat Completions in internal tests[^15]. Higher cache hit rates mean lower input token costs — for example, cached input tokens for o4-mini are 75% cheaper than uncached ones[^17]. The Assistants API's architecture made efficient caching difficult because state management was opaque and server-side.

#### 4. Native Agentic Tools

The Responses API is **agentic by default** — it supports a built-in tool loop where the model can call multiple tools (web search, file search, code interpreter, image generation, remote MCP servers, and custom functions) **within a single API request**[^15]. The Assistants API required manual orchestration for multi-tool scenarios. The Responses API also supports capabilities that never existed in the Assistants API:

| Capability | Assistants API | Responses API |
|-----------|---------------|---------------|
| Web search | ❌ (custom implementation) | ✅ Built-in |
| File search | ✅ | ✅ |
| Code interpreter | ✅ | ✅ |
| Computer use | ❌ | ✅ |
| Image generation | ❌ | ✅ |
| MCP (remote servers) | ❌ | ✅ |
| Deep research | ❌ | ✅ |
| Reasoning summaries | ❌ | ✅ |
| Connectors (Google, Dropbox, etc.) | ❌ | ✅ |

#### 5. Conversations Replace Threads

Threads could only store messages. **Conversations** store **items** — messages, tool calls, tool outputs, reasoning items, and other data[^16]. This is a superset: anything you could do with Threads, you can do with Conversations, plus you get richer context that enables better debugging, training data extraction, and multi-agent coordination.

The upstream migration guide provides a direct mapping[^16]:

| Before | Now | Why |
|--------|-----|-----|
| Assistants | Prompts | Easier to version, snapshot, diff, and roll back |
| Threads | Conversations | Streams of items instead of just messages |
| Runs | Responses | Input items in, output items out; tool call loops explicitly managed |
| Run steps | Items | Generalized objects — can be messages, tool calls, outputs, and more |

#### 6. Encrypted Reasoning for Compliance

Organizations with Zero Data Retention (ZDR) requirements cannot use stateful APIs. The Responses API supports **encrypted reasoning items**: the client receives an encrypted blob of reasoning tokens that it can pass back in future requests without the provider ever persisting intermediate state[^17]. This capability had no equivalent in the Assistants API and is critical for regulated enterprise scenarios — exactly the scenarios Foundry serves.

#### 7. Future-Proofing

The upstream provider has been explicit: **"The Responses API represents the future direction for building agents"**[^15]. All new model support, tool integrations, and API features land exclusively on the Responses API. The Assistants API received no new features after its deprecation notice in August 2025. For Foundry, this means Agents v2 (built on Responses) is the only path to new capabilities.

### What This Means for Foundry's "Classic → New" Story

The upstream migration is not a Microsoft-specific change — it is an **industry-wide protocol evolution**. Foundry's Agents v2 inherits all seven benefits listed above, plus Foundry-specific additions:

- **Versioned agent definitions** with `PromptAgentDefinition` and `WorkflowAgentDefinition`
- **Hosted agents** with their own identity and managed lifecycle
- **Foundry-specific tools** (Foundry IQ, Azure AI Search, SharePoint, Fabric)
- **Enterprise governance** (RBAC, Azure Policy, content filters, network isolation)
- **Multi-agent workflows** via the Agent Framework

The key messaging opportunity: **don't frame the migration as "Microsoft changed the API." Frame it as "the industry evolved the protocol, and Foundry adopted it to give you better performance, lower costs, and more capabilities."**

### Key API Changes (from `migrate.mdx`)[^6]

| Before (Classic) | After (New) | Details |
|---|---|---|
| Threads | Conversations | Supports streams of items, not just messages |
| Runs | Responses | Responses send input items, receive output items. Tool call loops explicitly managed |
| Assistants / Agents | Agents (versioned) | Support for prompt, workflow, and hosted agents with stateful context |
| `client.agents.create_agent()` | `client.agents.create_version()` | Versioned definitions with explicit `kind`, `model`, `instructions` |
| `client.agents.threads.create()` | `openai_client.conversations.create()` | Uses OpenAI client, not project client |
| `client.agents.runs.create()` | `openai_client.responses.create()` | Synchronous by default, no polling loop needed |

### Dual-Client Pattern

A particularly confusing aspect of Agents v2: agent creation uses `AIProjectClient` (Foundry SDK), but conversation/response operations use the **OpenAI client** obtained via `project_client.get_openai_client()`[^6]. This split exists because conversations and responses are built on the OpenAI Responses API wire format, while agent definitions are Foundry-specific resources.

### Recommendation

- **Publish a clear "Agent API Versions" reference page** with the lineage diagram above
- **Explain the upstream protocol sunset deadline** — customers need to know this is a forced industry migration, not a preference. Frame it as: "the industry evolved the protocol" rather than "Microsoft changed the API"
- **Incorporate the seven upstream benefits** (simpler model, better performance, lower costs, native tools, conversations, encrypted reasoning, future-proofing) into Foundry's own migration messaging — rewritten in Microsoft's voice without explicitly referencing the upstream provider
- **Document the dual-client pattern explicitly** — the migration doc does this well already[^6]; elevate it to a concept page
- **Highlight the capability matrix** showing what's available only in the Responses API (MCP, deep research, image generation, connectors, reasoning summaries) — these are exclusive to "New" and provide concrete value for the migration

---

## Axis 4: API Versioning — Monthly Versions to v1 Stable Routes

This is one of the most impactful developer-facing transitions and one of the clearest wins for the "New" story. It deserves its own axis because it affects **every developer** who calls any Azure OpenAI API, regardless of whether they use agents.

### The Problem: Monthly API Version Treadmill

Azure OpenAI historically required a dated `api-version` query parameter on every request:

```
POST https://{resource}.openai.azure.com/openai/deployments/{model}/chat/completions?api-version=2024-10-21
```

Each month brought a new preview version, each adding features that developers needed. The changelog in `api-version-lifecycle.mdx` tells the story[^14]:

| API Version | Key Feature Added |
|------------|-------------------|
| `2024-04-01-preview` | Assistants v2, file search, vector stores |
| `2024-05-01-preview` | Batch API, vector store chunking |
| `2024-07-01-preview` | Structured outputs |
| `2024-08-01-preview` | `max_completion_tokens` for o1 models, parallel tool calls |
| `2024-09-01-preview` | `reasoning_tokens` in usage |
| `2024-10-01-preview` | Stored completions, `reasoning_effort`, Defender integration |
| `2024-12-01-preview` | Predicted outputs, audio completions |
| `2025-01-01-preview` | (continued incremental) |
| `2025-02-01-preview` | Responses API, computer use |
| `2025-03-01-preview` | GPT-image-1, reasoning summaries, Evaluation API |
| `2025-04-01-preview` | Video generation, MCP tool integration, background tasks |

That is **12 API versions in 12 months**, each requiring developers to update a query parameter and test for breaking changes. Moreover, Azure OpenAI required a separate `AzureOpenAI()` client (Python, C#, JS, etc.) distinct from the standard `OpenAI()` client, creating overhead when porting code between OpenAI and Azure OpenAI[^14].

### The Solution: v1 API Routes

Starting August 2025, Azure OpenAI introduced the **v1 API**, which eliminates the monthly version treadmill[^14]:

```
POST https://{resource}.openai.azure.com/openai/v1/chat/completions
```

Key changes:

| Dimension | Classic (Monthly Versions) | New (v1 Routes) |
|-----------|---------------------------|-----------------|
| **URL pattern** | `/openai/deployments/{model}/chat/completions?api-version=2024-10-21` | `/openai/v1/chat/completions` |
| **Version management** | Must update `api-version` param monthly to access new features | No version parameter; ongoing access to latest features |
| **Client library** | `AzureOpenAI()` — Azure-specific client | `OpenAI()` — standard OpenAI client with `base_url` set to Azure[^14] |
| **Token auth** | Required `AzureOpenAI()` for automatic token refresh | `OpenAI()` client handles token refresh natively |
| **Cross-provider models** | Azure OpenAI models only | DeepSeek, Grok, and other providers via same `v1` chat completions route[^14] |
| **Preview features** | Entire API version is "preview" | Feature-specific preview headers (e.g., `"aoai-evals":"preview"`) or path indicators (e.g., `/alpha/`)[^14] |

### Code Comparison

**Classic (monthly version, Azure-specific client):**

```python
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="https://YOUR-RESOURCE.openai.azure.com",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-10-21",  # Must update monthly
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**New (v1, standard OpenAI client):**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://YOUR-RESOURCE.openai.azure.com/openai/v1/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

response = client.responses.create(
    model="gpt-4.1-nano",
    input="Hello",
)
```

Or, with environment variables `OPENAI_BASE_URL` and `OPENAI_API_KEY` set:

```python
client = OpenAI()  # Zero Azure-specific configuration
```

### v1 GA API Surface

The v1 API launched with a subset of capabilities, expanding rapidly[^14]:

| API Path | Status |
|----------|--------|
| `/openai/v1/chat/completions` | Generally Available |
| `/openai/v1/responses` | Generally Available |
| `/openai/v1/embeddings` | Generally Available |
| `/openai/v1/files` | Generally Available |
| `/openai/v1/fine_tuning/` | Generally Available |
| `/openai/v1/models` | Generally Available |
| `/openai/v1/vector_stores` | Generally Available |
| `/openai/v1/evals` | Preview (requires header) |

### Why This Matters for the "Classic → New" Story

The v1 API transition is perhaps the **easiest win** for customer messaging because:

1. **It solves a universal pain point**: Every Azure OpenAI developer has been burned by `api-version` management.
2. **It eliminates Azure-specific client code**: Developers can use the same `OpenAI()` client for both OpenAI and Azure, with only a `base_url` change.
3. **It enables cross-provider model access**: The same `/openai/v1/chat/completions` route works with DeepSeek, Grok, and other Foundry Direct models.
4. **It decouples feature access from version management**: Preview features use headers, not version strings.

### Connection to the Agent-Centric Shift

The v1 API is not just a developer convenience — it is architecturally necessary for the agent-centric world. When models shipped every 6 months, monthly API versions were manageable. When the Responses API, MCP tool integration, background tasks, image generation, and encrypted reasoning all land within a 3-month window (Feb–Apr 2025)[^14], forcing developers to hop from `2025-02-01-preview` to `2025-03-01-preview` to `2025-04-01-preview` to access each feature is untenable. The v1 API acknowledges that the pace of innovation has outgrown the monthly versioning model.

### Recommendation

- **Lead with the v1 API as the flagship "Classic → New" developer improvement** — it has the broadest impact and the simplest migration path
- **Create a prominent "Upgrade to v1" guide** that shows the 3-line code change (already well-documented in `api-version-lifecycle.mdx`[^14])
- **Document both endpoints**: `https://{resource}.openai.azure.com/openai/v1/` and `https://{resource}.services.ai.azure.com/openai/v1/` (both are valid[^14])
- **Clarify that monthly API versions still work** — v1 is opt-in, not a forced migration. Classic `api-version` parameters remain supported for existing code.

---

## Axis 5: Resource Model Evolution

### Classic: Multi-Resource Hub Model

```
┌─────────────────────────────────────────┐
│              Hub (workspace)            │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │Azure     │  │Azure AI Services     │ │
│  │OpenAI    │  │  ├─ Speech           │ │
│  │          │  │  ├─ Language          │ │
│  │          │  │  ├─ Vision            │ │
│  │          │  │  └─ Content Safety    │ │
│  └──────────┘  └──────────────────────┘ │
│  ┌──────────────────────────────────────┐│
│  │ Azure Machine Learning Workspace     ││
│  │   └─ Hub-based Projects              ││
│  └──────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

- Multiple Azure resource types to manage
- Multiple RBAC scopes
- Multiple SDKs
- Complex networking (multiple private endpoints)

### New: Foundry-as-a-Service

```
┌───────────────────────────────────────────┐
│      Foundry Resource                      │
│      (Microsoft.CognitiveServices/accounts │
│       kind: AIServices)                    │
│                                            │
│  ┌────────────────────────────────────────┐│
│  │ Foundry Project (default)              ││
│  │   ├─ Agents                            ││
│  │   ├─ Models (AOAI + Direct + Partner)  ││
│  │   ├─ Foundry Tools (Speech, Vision...) ││
│  │   ├─ Evaluations                       ││
│  │   └─ Connections                       ││
│  └────────────────────────────────────────┘│
│  ┌────────────────────────────────────────┐│
│  │ Foundry Project (team-2)               ││
│  │   └─ (isolated workspace)              ││
│  └────────────────────────────────────────┘│
│                                            │
│  Endpoints:                                │
│   .openai.azure.com                        │
│   .services.ai.azure.com                   │
│   .cognitiveservices.azure.com              │
└───────────────────────────────────────────┘
```

### The Upgrade Path

The `upgrade-azure-openai.mdx` document describes the AOAI → Foundry upgrade as changing `kind` from `'OpenAI'` to `'AIServices'` while preserving endpoint, keys, and state[^4]. This is a **non-breaking upgrade** that adds capabilities.

### Three FQDNs

A Foundry resource exposes three FQDNs[^4]:
- `{name}.openai.azure.com` — Azure OpenAI API compatibility
- `{name}.services.ai.azure.com` — Foundry API (projects, agents, evaluations)
- `{name}.cognitiveservices.azure.com` — Cognitive Services / Foundry Tools

This triple-endpoint model is itself a source of confusion. Customers need to know which endpoint to use for which SDK.

### Recommendation

- **Create a "Resource Types Explained" page** that shows the before/after diagram
- **Explicitly document the three endpoints** and which SDK/scenario uses each (the `sdk-overview.mdx` does this with a table[^7] — ensure it's prominent and cross-linked)
- **Hub deprecation is Phase 3** — target is April 30, 2026, contingent on Foundry Hosting (MaaP) GA[^18]. Hub users will be routed to ML Studio from NextGen for MaaP deployments and Prompt Flow. The hub-to-Foundry migration guide does not yet exist and is a critical Phase 3 deliverable.
- **Agents v0.5 on Hub** needs a deprecation owner — this is called out as an unresolved blocker in the migration plan[^18]
- **Foundry Tools naming:** Confirmed lineage is Cognitive Services → Azure AI Services → Foundry Tools. "Foundry Tools" refers to the domain-specific AI services (Speech, Vision, Language, Content Understanding, Content Safety), **not** the Foundry resource type. The `multi-service-resource.mdx` phrasing is misleading.

---

## Axis 6: SDK Evolution

### Classic SDK Stack

| SDK | Purpose | Status |
|-----|---------|--------|
| `azure-ai-inference` | Chat completions, embeddings (model inference) | **Deprecated**, retiring May 30, 2026[^8] |
| `azure-ai-generative` | RAG, prompt flow, evaluations | Superseded |
| `azure-ai-evaluation` | Model/agent evaluations | Continues in `azure-ai-projects` |
| `openai` (Azure OpenAI SDK) | OpenAI API compatibility | Continues |

### New SDK Stack

| SDK | Purpose | Endpoint | Status |
|-----|---------|----------|--------|
| `azure-ai-projects` (2.x preview) | Agents, evaluations, Foundry-specific features | `.services.ai.azure.com/api/projects/{project}` | Preview[^7] |
| `azure-ai-projects` (1.x GA) | Classic experience | Same | Stable[^7] |
| `openai` | Chat completions, responses, conversations | `.openai.azure.com/openai/v1` | Stable[^7] |
| Foundry Tools SDKs | Speech, Vision, Language, Content Safety | Tool-specific | Stable |
| Agent Framework | Multi-agent orchestration (cloud-agnostic) | Via project endpoint | Preview |

### The Azure AI Inference Question

From your open questions: **"Is Azure AI Inference deprecated now that GitHub Models is no longer using it?"**

**Yes.** The `azure-ai-inference` beta SDK is deprecated with a retirement date of **May 30, 2026**[^8]. Microsoft recommends migrating to the OpenAI SDK (`openai` package), which provides the same chat completions and embeddings capabilities through the `/openai/v1` endpoint. GitHub Models now uses the OpenAI SDK directly. The migration is minimal — mostly changing import statements and endpoint URLs.

### SDK Version ↔ Portal Version Mapping

This is a critical detail from `sdk-overview.mdx`[^7]:

| SDK Version | Portal Version | Status |
|---|---|---|
| `azure-ai-projects` 2.x (preview) | Foundry (new) | Preview |
| `azure-ai-projects` 1.x (GA) | Foundry (classic) | Stable |

Customers using the wrong SDK version for their portal experience will encounter confusing errors. This mapping must be prominent.

### Recommendation

- **Create a "SDK Migration Matrix"** showing old SDK → new SDK for each use case
- **Answer the Azure AI Inference question explicitly** in a deprecation notice or FAQ
- **Emphasize the SDK ↔ Portal version mapping** in quickstart and getting-started content

---

## Axis 7: Terminology Changes

### Comprehensive Terminology Table

This is the table you started — here it is completed and verified against the codebase:

| Concept | Classic Term | New Term | Notes |
|---------|-------------|----------|-------|
| **Conversation state** | Threads | Conversations | Conversations store items (messages, tool calls, outputs), not just messages[^6] |
| **Chat messages** | Messages | Items | Items are a superset of messages[^6] |
| **Execution** | Runs (async, polled) | Responses (sync by default) | No polling loop needed[^6] |
| **Agent definition** | Assistants / Agents | Agent Versions | Versioned, with explicit `kind` (prompt, workflow, hosted)[^6] |
| **Portal settings** | Management Center | Admin Console | Portal navigation rename |
| **AI services** | Azure AI Services | Foundry Tools | Speech, Vision, Language, Content Safety, Content Understanding |
| **Agent creation** | `create_agent()` | `create_version()` | Uses `PromptAgentDefinition`[^6] |
| **API wire protocol** | Assistants API | Responses API | OpenAI-driven change; Assistants sunset Aug 2026[^5] |
| **API versioning** | Monthly `api-version` params (e.g., `2024-10-21`) | v1 stable routes (`/openai/v1/...`), no version param | Platform pace-of-innovation change[^14] |
| **Client library** | `AzureOpenAI()` — Azure-specific | `OpenAI()` — standard, with `base_url` for Azure | Eliminates Azure-specific code[^14] |
| **Resource type** | Azure OpenAI + Hub | Foundry Resource | Single `AIServices` kind[^4] |
| **RBAC roles** | Cognitive Services OpenAI User | Azure AI User, Azure AI Project Manager, Azure AI Owner | New Foundry-specific roles with control/data plane separation[^9] |
| **Policies** | Azure AI Services policies | Foundry policies | Same `Microsoft.CognitiveServices` provider; policies being renamed[^10] |
| **Model billing** | Model-as-a-Service (MaaS) | Foundry Direct Models | First-party models billed directly via Azure meters[^11] |
| **Portal (main)** | Mainline / OAI sub-studio | Classic | Internal "Mainline" name not customer-facing |
| **Portal (new)** | — | NextGen → Foundry (new) | Internal "NextGen" name not customer-facing |

### Recommendation

- **Publish this table as a standalone reference page** (e.g., "Terminology: Classic vs. New")
- **Link it from migration guides, FAQs, and the glossary**
- **Include both old and new terms in the glossary** (`glossary.mdx` currently defines "Conversation" implicitly but not the mapping from "Thread")[^12]

---

## Axis 8: Model Billing Evolution

| Aspect | Classic (MaaS) | New (Foundry Direct) |
|--------|---------------|---------------------|
| **Who hosts** | Microsoft-managed GPU pools | Dedicated VMs or Microsoft-managed |
| **Billing unit** | Tokens (input/output) | VM core hours or tokens depending on deployment type |
| **Billing path** | Azure Marketplace for partners | Azure meters (first-party) |
| **Model scope** | Azure OpenAI models only | Azure OpenAI + DeepSeek + Meta + xAI + Mistral + Microsoft + Black Forest Labs[^4] |
| **Provisioned throughput** | PTUs per model | Fungible PTUs across Foundry Direct Models |

### Recommendation

- This is the least well-documented transition axis. Create a "Model Billing Explained" page
- Clarify that pay-per-token still exists for standard deployments; "Foundry Direct" is about billing path, not pricing model

---

## Differentiating from Copilot Studio and M365 Copilot

This is a critical messaging need. Here is a decision framework:

| Dimension | Microsoft Foundry | Copilot Studio | M365 Copilot |
|-----------|------------------|----------------|--------------|
| **Target user** | Developers, ML engineers | Business users, IT pros, pro-makers | End users |
| **Development model** | Code-first (SDKs, CLI, VS Code) | Low-code (visual designer, connectors) | No development |
| **Agent complexity** | Multi-agent systems, custom models, fine-tuning | Departmental chatbots, workflows | Built-in AI assistant |
| **Infrastructure** | Full Azure control (VNETs, compute, BYO resources) | Fully managed SaaS | Embedded in M365 |
| **Integrations** | Deep Azure + multi-cloud + custom code | M365 + Power Platform connectors | M365 Graph only |
| **Deployment targets** | Azure, containers, any cloud | Teams, Outlook, web | M365 apps |
| **Pricing model** | Consumption (tokens, compute hours) | Capacity-based (messages/month) | Per-user license |

### The Hybrid Pattern

The most powerful messaging for enterprises: **build backend logic in Foundry, compose user-facing experiences in Copilot Studio**. This is the bridge between the two platforms and should be documented as a first-class pattern[^13].

### Recommendation

- **Create a "Foundry vs. Copilot Studio vs. M365 Copilot" comparison page** (this is in your open items)
- **Lead with the persona** ("Who are you?") rather than the technology
- **Document the hybrid pattern** as a recommended architecture

---

## Proposed Documentation Structure for the Evolution

Based on the analysis, here is a recommended documentation structure for addressing the Classic → New transition:

### 1. Landing Page: "What is Foundry" (exists, needs refinement)

- Who is it for (developer personas)
- Discovery → Build → Operate lifecycle
- Link to Classic docs for customers not yet migrated

### 2. Understanding the Evolution (new section)

```
setup/
├── evolution/
│   ├── classic-vs-new-overview.mdx          # Single entry point
│   ├── terminology-mapping.mdx              # The big terminology table
│   ├── feature-comparison.mdx               # Feature support matrix
│   ├── agent-api-versions.mdx               # Assistants → Agents v2 lineage
│   └── sdk-migration-matrix.mdx             # Which SDK replaces what
```

### 3. Migration Guides (consolidate once NextGen GA)

```
setup/
├── migrate/
│   ├── overview.mdx                         # "Which migration path do I need?"
│   ├── aoai-to-foundry.mdx                  # Azure OpenAI → Foundry resource (exists as upgrade-azure-openai.mdx)
│   ├── hub-to-foundry.mdx                   # Hub-based projects → Foundry projects
│   ├── agents-v1-to-v2.mdx                  # Agents v1 → v2 (exists as migrate.mdx)
│   ├── api-version-to-v1.mdx               # Monthly api-versions → v1 routes (exists as api-version-lifecycle.mdx)
│   └── sdk-migration.mdx                    # azure-ai-inference → openai SDK
```

### 4. Blog Posts Needed

| Blog | Purpose | Owner |
|------|---------|-------|
| "V1/V2 Terminology Table" | Customer-facing terminology mapping with examples | (Dennis) |
| "Why Foundry, not Copilot Studio?" | Persona-based decision guide | (Nick) |
| "The OpenAI Responses API: What It Means for Foundry Developers" | Explain the Assistants → Responses migration in context | (Dennis/Dan) |
| "From Hub to Foundry: A Migration Story" | Customer-facing narrative of what changed and why | (Nick) |

---

## Complete "Classic vs. New" Alignment Table (Refined)

This is the refined version of the table from your initial draft, with corrections and additions based on research:

| Dimension | Classic | New | Migration Effort |
|-----------|---------|-----|-----------------|
| **Agent service** | Agents v0.5 (Assistants API on AOAI), Agents v1 (Assistants API on Agent Service) | Agents v2 (Responses API on Agent Service) | Medium — code changes required[^6] |
| **Inference shape** | Chat Completions API | Responses API (Chat Completions still available) | Low — additive, not breaking |
| **API versioning** | Monthly `api-version` params (`2024-03-01-preview` through `2025-04-01-preview`) | v1 stable routes (`/openai/v1/`); preview features via headers | Low — 3-line code change; opt-in[^14] |
| **Client library** | `AzureOpenAI()` client (Azure-specific) | `OpenAI()` client with `base_url` (standard) | Low — drop-in replacement[^14] |
| **UX experience** | Mainline portal → label as "(classic)" | NextGen portal → label as "(new)" | N/A — toggle switch |
| **Threads** | Threads (message-only) | Conversations (items: messages, tool calls, outputs) | Medium — structural change[^6] |
| **Messages** | Messages (in threads) | Items (in conversations) | Low — superset |
| **Execution** | Runs (async polling) | Responses (sync by default) | Medium — pattern change[^6] |
| **Portal settings** | Management Center | Admin Console | N/A — UI rename |
| **AI services branding** | Azure AI Services | Foundry Tools | N/A — name change |
| **Resource model** | Hub + AOAI + AI Services (multiple resources) | Foundry Resource (single, with child projects) | Low — upgrade path exists[^4] |
| **Agent API** | Assistants API (OpenAI wire protocol) | Agents API (Responses wire protocol) | High — wire protocol change |
| **RBAC roles** | Cognitive Services OpenAI User, Cognitive Services User | Azure AI User, Azure AI Project Manager, Azure AI Owner | Medium — review assignments[^9] |
| **Model billing** | MaaS (Marketplace for partners, per-token for AOAI) | Foundry Direct Models (Azure meters, fungible PTUs) | Low — billing path change |
| **Documentation** | Domain-specific (Speech, Language, Vision separate) | Foundry-centric with branches to domain-specific | N/A — docs restructure |
| **SDK (Python)** | `azure-ai-inference`, `azure-ai-generative`, `azure-openai` | `azure-ai-projects` (2.x), `openai`, Foundry Tools SDKs | Medium — package swap |
| **Azure Policies** | `Azure AI Services` namespace | `Foundry` namespace (rename in progress) | Low — policy rename[^10] |

---

## Open Questions — Answers

### "Is Azure AI Inference deprecated now that GitHub Models is no longer using it?"

**Yes.** The `azure-ai-inference` SDK (Python, .NET, JS) is deprecated with a retirement date of **May 30, 2026**[^8]. The recommended migration target is the `openai` SDK package, which provides the same inference capabilities (chat completions, embeddings) through the `/openai/v1` endpoint on Foundry resources. The migration is straightforward — mostly changing import statements and endpoint configuration. GitHub Models now uses the OpenAI SDK directly.

---

## Recommended Action Items (Aligned to Migration Phases)

### Phase 1 — Before March 17 (NextGen GA Announcement)

1. **Ensure docs-vnext is production-ready** — all pages in the NextGen TOC are live and reviewed
2. **Publish the terminology mapping table** as a standalone reference page
3. **Rename all "Mainline" references to "Classic"** in customer-facing content
4. **Answer the Azure AI Inference deprecation question** in a deprecation notice
5. **Create the feature comparison matrix** (Classic vs. New portal capabilities)
6. **Document the toggle-back flow** — users need to know they can return to Classic

### Phase 1 → Phase 2 Transition (March–April 2026)

7. **Label the Classic portal as "Classic"** consistently in UI, docs, and blog posts
8. **Publish the V1/V2 terminology blog post** (owner: Dennis)
9. **Publish the "Why Foundry, not Copilot Studio?" comparison** (owner: Nick)
10. **Document the default-project API key behavior** — critical for AOAI upgrade users
11. **Document the assistants playground redirect** — users upgrading from AOAI need to know where to find assistants in Mainline

### Phase 2 (AOAI → FDP Migration, March 2026 – March 2027)

12. **Consolidate migration guides** under a single section with a "Which migration do I need?" entry point
13. **Create the "What is changing and why" customer-facing narrative article** (owner: Nick)
14. **Align Azure Portal display names** with Classic/New terminology
15. **Update landing page** to lead with the Discovery → Build → Operate lifecycle
16. **Publish the "From AOAI to Foundry" blog post** — explaining the auto-upgrade process, rollback options, and what changes

### Phase 3 (Hub Deprecation, TBD ~April 2026+)

17. **Create hub-to-Foundry migration guide** (does not yet exist)
18. **Publish Agents v0.5 deprecation notice** — needs an owner
19. **Document the ML Studio routing** for MaaP and Prompt Flow customers
20. **Publish Foundry Tools studio retirement comms** (Language Studio, Speech Studio, etc.)

### Phase 4 (Legacy Retirement, TBD)

21. **Archive/remove classic docs** (owner: Amir/Sheri per migration plan)
22. **Redirect ai.azure.com to NextGen** (owner: Shané/Sean per migration plan)
23. **Remove Azure Portal AOAI view** (owner: Varsha per migration plan)

---

## The Four-Phase Migration Plan

The all-up migration plan — authored by Amir Zur, Dennis Eikelenboom, and Shané Winner — provides the authoritative roadmap for how everything in this report comes together operationally[^18]. The plan resolves the core ambiguity: this is not one migration but **four sequential phases**, each with distinct customer cohorts, entry/exit criteria, and KPIs.

### Phase Overview

```
Phase 1                Phase 2                Phase 3               Phase 4
─────────────          ─────────────          ─────────────         ─────────────
NextGen GA             AOAI → FDP             Hub Deprecation       Retire Legacy
for FDP users          + NextGen              + Foundry Tools       Experiences
                                              → FDP + NextGen
Mar 13 → Mar 17       Mar '26 → Mar '27      TBD (Apr '26+)        TBD
─────────────          ─────────────          ─────────────         ─────────────
  Low impact            Moderate-High          Moderate              High
  (toggle back)         (resource change)      (destination change)  (hard cutoff)
```

### Phase 1: NextGen GA for FDP Customers (March 13–17, 2026)

**Goal:** Make NextGen the trusted default for FDP (Foundry Data Platform) customers with GA quality.

| Milestone | Description | Target | KPI |
|-----------|-------------|--------|-----|
| M0 (Done) | Users can opt-in to NextGen via toggle | Live | 12% of Mainline users using NextGen |
| M1 | NextGen GA — FDP users default to NextGen, can toggle back | **March 13** (announced March 17) | 30% of Mainline users using NextGen |
| M2 | Full Mainline parity for FDP; toggle removed after KPIs met | Post-GA | Error rates < 1%, retention targets met |

**Key M1 blockers being resolved:**
- API key support for project-scoped resources (short-term: API-key access for default project only)
- UX continuity for vector stores, files, and assistants created in Mainline
- Agents V2 GA
- OAI v1 endpoint discoverability from NextGen UX

**Critical nuance:** Hub projects and AOAI-only resources remain **Mainline-only** in Phase 1. NextGen shows only Foundry projects.

### Phase 2: AOAI → FDP + NextGen (March 2026 – March 2027)

**Goal:** Move the largest legacy cohort (Azure OpenAI customers) onto the Foundry resource type and NextGen portal.

| Milestone | Description | Target |
|-----------|-------------|--------|
| M3 | Any AOAI user can opt-in to upgrade to Foundry + land in NextGen | Post-Phase 1 |
| M4 | Auto-upgrade all AOAI customers; rollback available; opt-out via Policy | TBD (gating metrics must be met) |

**Auto-upgrade gating metrics (draft):**
- Parity + no experience cliffs
- Rollback rate < 0.6%
- 30-day retention post-upgrade on par with AOAI baseline
- 15%+ MoM token growth
- Non-OAI model/feature attach
- ICM and support case volume stable

**Critical risk:** DSAT because NextGen alternatives for OAI sub-studio provide same functionality but not same API surface in the UX (e.g., Agents instead of OAI Assistants, Foundry evals over OAI evals, AI Search index over OAI vector store). The API still supports all legacy patterns.

### Phase 3: Hub Deprecation + Foundry Tools Migration (TBD, ~April 2026+)

**Goal:** Consolidate the Hub fork by transitioning Foundry Tools / managed compute customers.

| Milestone | Description | Target |
|-----------|-------------|--------|
| M5 | Deprecate Hub once Foundry Hosting (MaaP) lands | Target: April 30 (depends on Foundry Hosting GA) |
| M6 | NextGen becomes default for Language, Translator, Content Understanding, Speech | Target: April 30 (pending AI Services alignment) |

**Critical dependencies:**
- Foundry Hosting (MaaP) GA timeline has slipped (Feb → Apr → Build)
- Agents v0.5 in preview on Hub has never been retired; needs owner for deprecation
- Language team is *increasing* Hub dependency for Language Studio retirement — conflicts with Hub phase-out
- ML Studio continuation strategy needs clarity (are MaaP and Prompt Flow customers routed to ML Studio or NextGen?)

### Phase 4: Retire Legacy Experiences (TBD)

**Goal:** Remove Mainline, legacy studios, and legacy resource types entirely.

**Workstreams:**
1. **Retire Mainline** — remove toggle, remove Classic docs, redirect ai.azure.com to NextGen, remove Azure Portal AOAI view
2. **Retire 1keyv1 (kind=CognitiveServices)** — depends on Azure AI Search dependency resolution (Target: September 2027)
3. **Retire Azure Speech resource type** — auto-upgrade all Speech customers to FDP
4. **Retire Azure Language resource type** — auto-upgrade all Language customers to FDP

**Open questions:**
- Target date for shutting down Mainline experience
- Cross-org retirement date for all legacy resource types and studios
- Strategy for Azure ML workspace continuation and Foundry Horizon

### What the Migration Plan Means for Documentation

The four-phase plan directly informs what documentation needs to exist and when:

| Phase | Docs Action |
|-------|-------------|
| **Phase 1 (Now)** | NextGen GA docs (docs-vnext) must be production-ready by March 13. "What is Foundry" page updated. Toggle-back guidance documented. |
| **Phase 2** | AOAI → Foundry upgrade guide (exists as `upgrade-azure-openai.mdx`). Must address: default project API key behavior, assistants playground redirect to Mainline, OAI vector store → AI Search transition. |
| **Phase 3** | Hub → ML Studio routing docs. Agents v0.5 deprecation notice. Foundry Tools studio retirement comms. **Hub-to-Foundry migration guide** (does not yet exist). |
| **Phase 4** | Classic docs archived. Redirect documentation. Migration completion verification guides. |

---

## Key Stakeholder Domains

| Person | Domain | What They Uniquely Know |
|--------|--------|------------------------|
| **Bala** | Foundry API | API design decisions, project endpoint routing, Foundry API architecture, API key auth scoping, data plane architect decisions |
| **Dan** | Foundry SDKs | SDK 1.x→2.x migration specifics, language parity (Python/C#/JS/Java), Agent Framework orchestration, SDK deprecation timelines |
| **Jeff** | Foundry Agent Service | Agent v1→v2 backend evolution, Agents v0.5 retirement plan, hosted agent architecture, A2A protocol integration, agent identity model |
| **Marco** | Horizontal platform | Cross-cutting concerns: how all the pieces fit together, Foundry Hosting (MaaP) strategy, ML Studio continuation, Foundry Horizon plans, resource type consolidation strategy |

---

## Naming Lineage Confirmed

Per your clarification, the naming lineage for "Foundry Tools" is:

> **Cognitive Services** (original) → **Azure AI Services** (rebranding) → **Foundry Tools** (current)

These were announced at successive Build/Ignite events. This confirms that "Foundry Tools" is the current name for the collection of domain-specific AI services (Speech, Vision, Language, Content Understanding, Content Safety), **not** the Foundry resource type itself. The `multi-service-resource.mdx` phrasing ("renaming of former 'Foundry Tools'") is misleading and should be clarified.

## Documentation Architecture Confirmed

The dual-docs model is intentional:

| Docs Version | Maps To | Content Scope |
|-------------|---------|---------------|
| `foundry-classic` | Hubs, Agents v1, Mainline portal | Legacy resource types, Assistants API, hub-based projects |
| `foundry` (docs-vnext) | Projects, Agents v2, NextGen portal | Foundry resource type, Responses API, Foundry projects |

Per Phase 4, Classic docs will eventually be **removed** (not just archived) — this is listed as a Phase 4 deliverable: "Remove classic docs (Amir/Sheri)."

---

## Confidence Assessment

### High Confidence
- Branding timeline (Azure AI Studio → Azure AI Foundry → Microsoft Foundry) — confirmed across multiple sources
- Agent API evolution and wire protocol changes — confirmed in `migrate.mdx`[^6] and Dennis's blog[^1]
- **v1 API evolution from monthly `api-version` parameters** — confirmed in `api-version-lifecycle.mdx`[^14] with complete changelog, code examples, and GA surface
- **`AzureOpenAI()` → `OpenAI()` client migration** — confirmed with code examples across 6 languages in `api-version-lifecycle.mdx`[^14]
- SDK evolution and deprecation of `azure-ai-inference` — confirmed by Microsoft Learn docs[^8]
- OpenAI Assistants API sunset (August 26, 2026) — confirmed by OpenAI[^5]
- Resource model changes — confirmed in `upgrade-azure-openai.mdx`[^4] and `sdk-overview.mdx`[^7]
- Portal duality (Classic/New) — confirmed in `what-is-foundry.mdx`[^3]
- **Industry shift from model-centric to agent-centric** — confirmed by model release cadence data, reasoning model timeline (o1-preview Sept 2024, o1 Dec 2024, o3/o4-mini 2025), and Foundry's architectural response
- **NextGen GA date: March 13 (announced March 17)** — confirmed from internal migration plan[^18]
- **Four-phase migration plan with milestones** — confirmed from internal migration plan[^18]
- **Naming lineage: Cognitive Services → Azure AI Services → Foundry Tools** — confirmed by user input citing Build/Ignite announcements
- **Stakeholder domains: Bala (API), Dan (SDKs), Jeff (Agent Service), Marco (horizontal platform)** — confirmed by user input
- **Dual-docs model (foundry-classic / foundry) is intentional** — confirmed by user input and Phase 4 plan to remove classic docs

### Medium Confidence
- "Foundry Direct Models" billing details — the distinction between MaaS and Foundry Direct is documented but the exact billing changes are still evolving
- Azure Policy namespace rename from "Azure AI Services" to "Foundry" — referenced in your alignment table but the `policy-reference.mdx` page is currently minimal[^10]
- Hub deprecation timeline — Phase 3 targets April 30 but depends on Foundry Hosting GA, which has slipped multiple times[^18]
- AOAI auto-upgrade timeline — Phase 2 milestone 4 has gating metrics but no firm date[^18]

### Lower Confidence
- Phase 4 timelines — "TBD" across all workstreams; depends on Phase 2-3 completion
- 1keyv1 (kind=CognitiveServices) retirement — target September 2027, but depends on Azure AI Search dependency resolution[^18]
- ML Studio continuation strategy and Foundry Horizon — listed as "help needed" in the migration plan
- "Admin Console" as replacement for "Management Center" — still not confirmed in docs; may be "Operate" section in NextGen

---

## Footnotes

[^1]: Dennis Drews, "Build Recap: New Azure AI Foundry Resource, Developer APIs, and Tools," Microsoft Tech Community, May 2025. https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/build-recap-new-azure-ai-foundry-resource-developer-apis-and-tools/4427241

[^2]: Perplexity research citing Microsoft Ignite 2025 announcements and market coverage confirming November 2025 rebranding from Azure AI Foundry to Microsoft Foundry.

[^3]: `docs-vnext/overview/what-is-foundry.mdx` — Lines 1-89 in the foundry-docs repository.

[^4]: `docs-vnext/setup/upgrade-azure-openai.mdx` — Lines 1-338 in the foundry-docs repository. Documents the AOAI → Foundry upgrade path, resource type (`AIServices`), and three FQDNs.

[^5]: OpenAI Community announcement: "Assistants API Beta Deprecation — August 26, 2026 Sunset." https://community.openai.com/t/assistants-api-beta-deprecation-august-26-2026-sunset/1354666

[^6]: `docs-vnext/setup/migrate.mdx` — Lines 1-505 in the foundry-docs repository. Documents Threads→Conversations, Runs→Responses, and the dual-client pattern.

[^7]: `docs-vnext/api-sdk/sdk-overview.mdx` — Lines 1-80 in the foundry-docs repository. Defines the SDK table (Foundry SDK, OpenAI SDK, Foundry Tools SDKs, Agent Framework) and the 2.x vs 1.x version mapping.

[^8]: Microsoft Learn, "Endpoints for Azure AI Foundry Models" — deprecation notice for azure-ai-inference SDK with May 30, 2026 retirement date. https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/endpoints

[^9]: `docs-vnext/security/rbac-foundry.mdx` — Lines 1-60 in the foundry-docs repository. Documents new built-in roles (Azure AI User, Azure AI Project Manager, Azure AI Owner).

[^10]: `docs-vnext/security/policy-reference.mdx` — Lines 1-21 in the foundry-docs repository. Currently minimal; Azure Policy definitions are being renamed from "Azure AI Services" to "Foundry Tools."

[^11]: Microsoft Learn, "Models sold directly by Azure" — Foundry Direct Models documentation. https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure

[^12]: `docs-vnext/glossary.mdx` — Lines 1-189 in the foundry-docs repository. Defines current terms but does not include migration mappings from deprecated terms.

[^13]: Microsoft Tech Community, "Microsoft Copilot Studio vs. Microsoft Foundry: Building AI Agents and Apps." https://techcommunity.microsoft.com/blog/microsoft-security-blog/microsoft-copilot-studio-vs-microsoft-foundry-building-ai-agents-and-apps/4483160

[^14]: `docs-vnext/api-sdk/api-version-lifecycle.mdx` — Lines 1-605 in the foundry-docs repository. Documents the v1 API evolution from monthly `api-version` parameters, the complete API version changelog, v1 GA API surface, preview header mechanism, and code examples showing `AzureOpenAI()` → `OpenAI()` migration across Python, C#, JavaScript, Go, Java, and REST.

[^15]: Upstream API provider, "Migrate to the Responses API" guide (`/api/docs/guides/migrate-to-responses/`). Documents: Responses API as "recommended for all new projects"; 3% SWE-bench improvement; 40–80% cache utilization improvement; agentic loop with built-in tools; Chat Completions vs Responses capability matrix; Assistants API deprecation (Aug 26, 2025) with sunset Aug 26, 2026. Quote: "The Responses API represents the future direction for building agents."

[^16]: Upstream API provider, "Assistants Migration Guide" (`/api/docs/assistants/migration/`). Documents: Assistants→Prompts, Threads→Conversations, Runs→Responses, Run Steps→Items mapping; practical migration steps; side-by-side code examples for user chat apps, function-calling apps, and thread backfill; Conversations API as replacement for Threads.

[^17]: Upstream API provider, "Better performance from reasoning models using the Responses API" cookbook (`/cookbook/examples/responses_api/reasoning_items/`). Documents: reasoning item preservation across tool-calling turns; 3% SWE-bench improvement from including reasoning items; cache utilization improvement (40% to 80%); encrypted reasoning items for ZDR/compliance organizations; reasoning summaries feature. [openai/openai-cookbook](https://github.com/openai/openai-cookbook) `examples/responses_api/reasoning_items.ipynb`.

[^18]: Internal document, "Foundry All-Up Migration Plan" (Amir Zur, Dennis Eikelenboom, Shané Winner). Documents the four-phase migration plan: Phase 1 (NextGen GA for FDP, March 13), Phase 2 (AOAI → FDP + NextGen, March '26–March '27), Phase 3 (Hub deprecation + Foundry Tools migration, TBD ~April '26), Phase 4 (Retire legacy experiences, TBD). Includes milestone definitions, gating metrics, blockers, risks, and owner assignments.
