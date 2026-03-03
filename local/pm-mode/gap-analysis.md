# Gap Analysis: Where the Research Needs Your Input

## Executive Summary

After auditing all eight axes of the current research report against the docs-vnext codebase, the original alignment table from your team, publicly available sources, and the limits of what I can fetch/discover, I identified **five axes with significant gaps** where your insider context would materially improve the report, plus **three potential missing axes** that the current framework doesn't cover at all. The gaps fall into two categories: (1) information that exists internally but isn't public/documented, and (2) evolving decisions that only the team can speak to.

---

## Axes with Gaps (Where Your Input Would Help)

### Gap 1: Axis 2 (Portal UX) — NextGen GA Timeline & Feature Parity Plan

**What the report says:** The Classic/New portal distinction is well-documented. The report recommends labeling Classic "the moment NextGen goes GA."

**What I cannot determine:**

- **When is NextGen GA?** No public commitment found. The report flags this as "Lower Confidence." This is the single most important timeline for the entire documentation plan — every action item hinges on it.
- **What's the feature parity plan?** The docs-vnext `what-is-foundry.mdx` says "Only Foundry projects are visible here — use (classic) for all other resource types."[^1] But the report doesn't capture:
  - Will Classic eventually be deprecated entirely, or will it persist indefinitely as the "power user" portal?
  - What's the disposition of **hub-based projects** — deprecated? Frozen? Migration-required?
  - Dennis's blog says "hub-based project type remains accessible"[^2] but new investments are "Foundry project" only — is there a sunset date for hubs?
- **Azure Portal display alignment** — your alignment table calls out "Azure Portal display should align with classic vs new" and "Azure Portal landing page should align." What specifically needs to change in the Azure Portal (as opposed to ai.azure.com)?

**What you could provide:**
- NextGen GA timeline (even approximate: Q1 2026? Q2?)
- Hub-based projects disposition plan
- Azure Portal changes that are planned/in-flight

**Confidence: LOW** — I'm guessing at timelines and can't determine internal roadmap decisions.

---

### Gap 2: Axis 5 (Resource Model) — The Hub → Foundry Project Migration Path

**What the report says:** AOAI → Foundry upgrade is well-documented (`upgrade-azure-openai.mdx`). The resource model diagram is accurate.

**What I cannot determine:**

- **Hub → Foundry project migration** is listed in your "once NextGen GA" migration section but **no migration guide exists yet** in docs-vnext. The current `migrate.mdx` covers Agents v1→v2 only.[^3] There's no `hub-to-foundry.mdx`.
- **What happens to existing hub resources?** The `architecture.mdx` page documents the new Foundry resource types but doesn't address:
  - Do hubs continue to work indefinitely?
  - Is there an automated migration tool planned?
  - What data/state carries over vs. must be recreated?
  - What about Azure Machine Learning workspaces that were connected to hubs?
- **The `multi-service-resource.mdx` page** mentions Foundry resource is "the next version and renaming of former 'Foundry Tools'"[^4] — this is itself confusing. Is "Foundry Tools" the new name for Azure AI Services, or for the Foundry resource? The terminology is inconsistent.

**What you could provide:**
- Hub deprecation/sunset timeline and plan
- Whether a hub→Foundry migration tool is planned
- Clarification of "Foundry Tools" vs "Foundry resource" naming (these seem to be used inconsistently)

**Confidence: MEDIUM** — The AOAI → Foundry upgrade path is clear; the hub → Foundry path is completely absent.

---

### Gap 3: Axis 7 (Terminology) — "Management Center" → "Admin Console" & Foundry Tools Naming

**What the report says:** The terminology table lists "Management Center → Admin Console" as a portal navigation rename.

**What I cannot determine:**

- **Is "Admin Console" the actual name?** I searched docs-vnext for "Admin Console" and found zero hits. The Classic portal uses "Management Center" in navigation. The New portal doesn't appear to use either term — it uses "Operate" as the section name[^5]. Your alignment table says "Admin Console" but this might be an internal/planned name that hasn't landed yet.
- **"Foundry Tools" confusion:** The term "Foundry Tools" appears in docs-vnext with at least three different meanings:
  1. The collection of domain-specific AI services (Speech, Vision, Language, Content Safety, Content Understanding) — as in "Foundry Tools SDKs"[^6]
  2. The Azure resource type itself — as in `multi-service-resource.mdx` saying Foundry resource is "renaming of former 'Foundry Tools'"[^4]
  3. The policy namespace — as in "Azure Policy built-in definitions for Foundry Tools"[^7]
  
  This triple-use of "Foundry Tools" is a conflation point the report doesn't call out.

**What you could provide:**
- Confirm the correct replacement for "Management Center" — is it "Admin Console" or "Operate" or something else?
- Clarify whether "Foundry Tools" refers to (a) AI services collection, (b) resource type, or (c) both — and whether this naming collision is intentional
- Any other terminology changes in the New portal not captured in the table (e.g., "Playground" → ?)

**Confidence: LOW** on "Admin Console"; **HIGH** on the "Foundry Tools" naming confusion being a real problem.

---

### Gap 4: Axis 8 (Billing) — This Axis Is Thin

**What the report says:** A brief table comparing MaaS vs Foundry Direct. The report already acknowledges this is "the least well-documented transition axis."

**What I cannot determine:**

- **Foundry Direct Models billing specifics:** The docs reference "models sold directly by Azure"[^8] and mention fungible PTUs, but the actual billing model differences are vague. Questions I can't answer:
  - Does Foundry Direct change the pricing for customers already using Azure OpenAI standard deployments?
  - How does billing work for non-OpenAI models (DeepSeek, Grok, Meta) — are these billed through Azure meters or still through Marketplace?
  - What's the actual customer impact of the billing path change? Is it just "the invoice looks different" or are there pricing implications?
- **Agent Service billing:** The FAQ says you're charged for model inference + Code Interpreter sessions + File Search vector storage[^9]. But the "new" experience adds:
  - Hosted agents (preview) — how are these billed? The `hosted-agents.mdx` says "See Limits, pricing, and availability (preview)" but the section is sparse.
  - Memory (GA in new) — is this free or billable?
  - Multi-agent workflows — is there per-agent or per-workflow pricing?
  - Foundry IQ — preview pricing model?

**What you could provide:**
- Clarification on Foundry Direct Models billing vs. classic MaaS
- Hosted agent pricing model
- Any net-new billing meters in the "New" experience
- Whether the billing change is transparent to existing customers or requires action

**Confidence: LOW** — Billing is the weakest axis by far.

---

### Gap 5: Axis 3 (Agent API) — The "Bala" and "Dan" Inputs

**What the report says:** Comprehensive coverage of the Assistants→Responses wire protocol change, the dual-client pattern, and upstream migration rationale.

**What I cannot determine:**

Your original alignment table specifically calls out:
- **"Bala - Align Agent v1/v2"** — What specific alignment is needed from Bala? Is this about the backend service evolution, the v1→v2 mapping for specific features, or something else?
- **"Bala's inputs" in next steps** — What context does Bala have that's not in the docs?
- **"Dan's inputs" in next steps** — Same question.
- **"Jeff" and "Marco" in next steps** — What are their areas of input?

Additionally, the **Agent Framework** (for multi-agent orchestration in code) is mentioned briefly in the SDK table but doesn't have its own axis or section. This is a major new capability (workflows, A2A protocol, hosted agents) that exists only in the "New" experience:

| New-Only Agent Capability | Status |
|--------------------------|--------|
| Multi-agent workflows (UI-based) | GA[^10] |
| Agent Framework (code-based orchestration) | Preview |
| Hosted agents (containerized) | Preview[^11] |
| Agent-to-Agent (A2A) protocol | Preview[^12] |
| Agent publishing to M365/Teams | GA[^13] |
| Agent identity (Entra Agent ID) | GA |
| Foundry Control Plane (fleet management) | Preview[^14] |

These "New-only" agent capabilities are a major selling point for migration and currently get no dedicated coverage in the report.

**What you could provide:**
- Bala's, Dan's, Jeff's, and Marco's specific input areas
- Whether the Agent Framework / multi-agent story deserves its own axis or section in the evolution narrative
- The "Agent Factory" / "Discovery → Build → Operate" lifecycle framing — is this the official customer-facing framework?

**Confidence: MEDIUM** on the agent capabilities inventory; **LOW** on what Bala/Dan/Jeff/Marco need to contribute.

---

## Potentially Missing Axes

### Missing Axis A: Observability & Evaluation Evolution

The report mentions observability in passing but doesn't capture it as a transition axis. The "New" experience introduces significant observability changes:

| Dimension | Classic | New |
|-----------|---------|-----|
| Tracing | SDK-based tracing with Application Insights | Built-in trace capture + Application Insights |
| Evaluations | `azure-ai-evaluation` SDK | Built-in evaluators in Foundry API + SDK |
| Agent metrics | Limited | Dedicated agent monitoring dashboard[^15] |
| Continuous evaluation | Not available | Python SDK-based continuous eval[^16] |
| AI Red Teaming | Not available | AI Red Teaming Agent[^17] |
| Foundry Control Plane | Not available | Fleet-wide observability[^14] |

**Should this be Axis 9?** Only if the observability changes are substantial enough to cause customer confusion or require migration. If evaluations code from 1.x SDK works differently in 2.x, that's a migration axis.

**What you could provide:** Is the evaluation SDK migration significant enough to warrant its own axis? Are there breaking changes in how tracing/eval works between classic and new?

---

### Missing Axis B: Multi-Agent & Orchestration Architecture

The "New" Foundry introduces an entirely new layer that didn't exist in Classic:

- **Workflow Agent** (UI-based, low-code)[^10]
- **Hosted Agents** (containerized, code-first)[^11]
- **Agent Framework** (open-source, cloud-agnostic)
- **A2A Protocol** support[^12]
- **MCP Protocol** support (remote servers)
- **Agent Publishing** to M365/Teams/BizChat[^13]
- **Foundry Control Plane** for fleet management[^14]

This isn't a "Classic → New" migration — it's an entirely new capability layer. But customers migrating from Classic need to understand that these capabilities exist and are only available in the New experience.

**What you could provide:** Should this be a dedicated axis? Or is it better covered as part of the "Why Migrate?" value proposition rather than a transition axis?

---

### Missing Axis C: Documentation Architecture Itself

Your original table includes "Docs" as a dimension:

> **Classic:** "Classic use of AI Services tools – Domain specific docs for speech service, language service etc."
> **New:** "Forward-looking scenarios where Foundry Tools enrich Agentic capabilities for Agent Factory scenarios demonstrated in NextGen. Branches out to classic docs for domain-specific API."

The docs-vnext structure is itself an axis of change. The `whats-new-foundry.mdx` page says: "This month marks a significant update to our documentation structure. With the introduction of the new Microsoft Foundry portal, we now maintain two corresponding versions of the documentation"[^18].

This dual-version documentation model is a source of confusion:
- Which docs should a customer read?
- How do the two versions relate?
- What's the versioning strategy going forward?

**What you could provide:** Is the dual-docs model permanent? Will classic docs eventually be archived? How should customers navigate between the two?

---

## Summary: Priority Input Requests

| Priority | Gap | What You Know That I Don't |
|----------|-----|---------------------------|
| 🔴 **Critical** | NextGen GA timeline | Even approximate timing drives all action items |
| 🔴 **Critical** | Hub deprecation/sunset plan | Determines whether a migration guide is needed |
| 🟡 **High** | Billing axis substance | Foundry Direct Models, hosted agent pricing, new billing meters |
| 🟡 **High** | "Foundry Tools" naming clarification | Three conflicting usages need resolution |
| 🟡 **High** | "Management Center" → ? replacement | Confirm actual new term |
| 🟡 **High** | Bala/Dan/Jeff/Marco input areas | What context do they uniquely hold? |
| 🟢 **Medium** | Agent Framework as its own axis | New-only capabilities inventory for the "Why Migrate?" story |
| 🟢 **Medium** | Observability evolution | Breaking changes in eval/tracing between classic and new? |
| 🟢 **Medium** | Dual-docs strategy | Permanent or transitional? Navigation guidance? |
| ⚪ **Nice to Have** | Azure Portal specific changes needed | What display names need to change in portal.azure.com? |

---

## Confidence Assessment

### What the Report Handles Well (No Input Needed)
- ✅ Branding evolution timeline — complete and verified
- ✅ Agent API lineage (Assistants → Agents v2) — deeply covered with upstream rationale
- ✅ API versioning (monthly → v1) — fully documented with code examples
- ✅ SDK evolution — deprecation timelines and migration paths confirmed
- ✅ Wire protocol change rationale — seven upstream reasons incorporated
- ✅ Copilot Studio differentiation — decision framework is solid
- ✅ Terminology mapping — comprehensive table verified against codebase

### What Needs Your Insider Knowledge (Input Requested)
- ❌ NextGen GA timing
- ❌ Hub sunset plan
- ❌ Billing specifics
- ❌ "Foundry Tools" naming resolution
- ❌ "Admin Console" vs "Operate" naming
- ❌ Bala/Dan/Jeff/Marco contribution areas
- ❌ Whether Agent Framework / Observability deserve their own axes

---

## Footnotes

[^1]: `docs-vnext/overview/what-is-foundry.mdx` — Line 21. "Only Foundry projects are visible here — use (classic) for all other resource types."

[^2]: Dennis Drews, Build 2025 recap blog. "hub-based project type remains accessible in Azure AI Foundry portal for GenAI capabilities that are not yet supported by the new resource type."

[^3]: `docs-vnext/setup/migrate.mdx` — covers Agents v1→v2 migration only. No hub→Foundry project migration guide exists in docs-vnext.

[^4]: `docs-vnext/setup/multi-service-resource.mdx` — Line 14. "Foundry resource is the next version and renaming of former 'Foundry Tools'."

[^5]: `docs-vnext/manage/overview.mdx` — Line 6. "Microsoft Foundry Control Plane is a unified management interface..." under the "Operate" section of the new portal.

[^6]: `docs-vnext/api-sdk/sdk-overview.mdx` — Line 12-13. "Foundry Tools SDKs" listed as SDK category for Speech, Vision, Language, Content Safety.

[^7]: `docs-vnext/security/policy-reference.mdx` — Line 5. "Azure Policy built-in policy definitions for Foundry Tools."

[^8]: Microsoft Learn, "Models sold directly by Azure." https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure

[^9]: `docs-vnext/agents/development/faq.mdx` — Lines 92-100. Agent Service billing: model inference cost + Code Interpreter per session + File Search vector storage.

[^10]: `docs-vnext/agents/development/workflow.mdx` — Lines 1-39. Workflow-based agent orchestration with visual builder, sequential/group-chat/human-in-the-loop patterns.

[^11]: `docs-vnext/agents/development/hosted-agents.mdx` — Lines 1-38. Containerized agent deployment with managed hosting, scaling, and observability.

[^12]: `docs-vnext/agents/tools/agent-to-agent.mdx` — Lines 1-40. A2A protocol support for cross-agent communication in Foundry Agent Service (preview).

[^13]: `docs-vnext/agents/development/publish-copilot.mdx` — Lines 1-40. Publishing agents to Microsoft 365 Copilot and Teams.

[^14]: `docs-vnext/manage/overview.mdx` — Lines 1-50. Foundry Control Plane for fleet management, observability, compliance, and security.

[^15]: `docs-vnext/agents/development/how-to-monitor-agents-dashboard.mdx` — referenced in `what-is-foundry.mdx` as "Real-Time Observability."

[^16]: `docs-vnext/agents/development/how-to-monitor-agents-dashboard.mdx` — referenced for continuous evaluation via Python SDK.

[^17]: `docs-vnext/observability/ai-red-teaming-agent.mdx` — AI Red Teaming Agent for automated scanning.

[^18]: `docs-vnext/operate/whats-new-foundry.mdx` — Lines 7-9. "This month marks a significant update to our documentation structure."
