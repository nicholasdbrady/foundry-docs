# Agent capability and harness map

Date: 2026-06-30

This file is the canonical implementation-readiness map for #467 and the prerequisite for #468 through #475. Keep durable routing, ownership, and capability-gap guidance here. Keep `.github/copilot-instructions.md` limited to always-on project context and command reminders, and keep path-specific writing rules in `.github/instructions/documentation.instructions.md`.

## Implementation readiness gate

| Check | Status | Evidence |
| --- | --- | --- |
| Target harnesses identified | Pass | GitHub Copilot app/project sessions for one-shot issue implementation; gh-aw for scheduled/reporting automation; deterministic Python scripts and tests for data preparation and evaluation; FastMCP/Mintlify MCP for docs retrieval. |
| Repo-local truth read | Pass | `.github/copilot-instructions.md`, `.github/agents/agentic-workflows.agent.md`, `.github/workflows/*.md`, `.github/workflows/shared/**`, `.mcp.json`, `fastmcp.json`, `pyproject.toml`, `README.md`, `foundry_docs_mcp/_server_factory.py`, `scripts/run_testbench.py`, `scripts/run_docs_eval.py`, `scripts/run_abcd_eval.py`, `scripts/scrape_model_catalog.py`, `tests/search_testbench.json`, and `tests/docs_eval_scenarios.json`. |
| Current first-party docs retrieved | Pass | Mintlify MCP/AI-readiness docs, FastMCP client/server testing docs, and GitHub gh-aw v0.67.1 workflow docs were retrieved before this map was written. |
| Conflicts identified | Pass | The repo currently mixes deterministic work and agent interpretation in some workflow prompts; final eval can silently fall back to local search; some report workflows rely on unbounded shell work. |
| User clarity achieved | Pass | The unblocked GitHub issue is #467, which asks for an implementation-ready map rather than immediate changes to dependent tranches. |
| Security boundaries clear | Pass | gh-aw write actions must use `safe-outputs`; direct workflow permissions remain read-only; workflow dispatch/rerun and PR/issue publishing are human-gated unless already encoded through approved safe outputs. |
| Validation plan exists | Pass | Validate this artifact with `git diff --check`; dependent code tranches must run their named script/test/workflow validation in the tables below. |

Confidence: High for repo-local inventory and harness recommendations; Medium for Mintlify hosted readiness checks that require dashboard-plan features or live hosted endpoints outside this repository.

## Current first-party evidence

| Surface | Current evidence | Repo implication |
| --- | --- | --- |
| Mintlify hosted search MCP | Mintlify documents that each public site exposes a search MCP server at `/mcp`, with search and query-docs-filesystem tools, skill resources, discovery at `/.well-known/mcp`, server cards at `/.well-known/mcp/server-card.json`, and read-only/non-destructive tool annotations. Source: <https://www.mintlify.com/docs/ai/model-context-protocol>. | Do not hardcode a hosted MCP tool name. Read discovery/server-card metadata or inspect MCP tools before using the hosted site as a benchmark source. |
| Mintlify `skill.md` and `llms.txt` | Mintlify hosts generated `skill.md`, `llms.txt`, and `llms-full.txt` files; `skill.md` summarizes capabilities, workflows, constraints, and can be exposed as MCP resources. Source: <https://www.mintlify.com/docs/ai/skillmd> and <https://www.mintlify.com/docs/ai/llmstxt>. | Agent-readiness checks should verify `/skill.md`, `/llms.txt`, `/.well-known/llms.txt`, and MCP resource discovery for the deployed docs site. |
| Mintlify CI/readiness | Mintlify CI checks can run broken-link and Vale checks on pull requests, and blocking mode fails when errors or suggestions exist. Source: <https://www.mintlify.com/docs/deploy/ci>. | Treat Mintlify CI as an external readiness signal when configured; keep local checks deterministic and report "not configured" rather than guessing. |
| FastMCP client inspection | FastMCP `Client` can connect to in-memory, HTTP, script, or config sources; after initialization it can `ping`, `list_tools`, `list_resources`, `list_prompts`, and expose server info, capabilities, and instructions. Source: <https://gofastmcp.com/clients/client>. | FastMCP readiness should be tested with a programmatic client, not only through LLM vibe tests. |
| FastMCP testing | FastMCP recommends wrapping servers in a `Client` for pytest fixtures, using in-memory transport for deterministic tests, and using snapshots for schemas/API responses. Source: <https://gofastmcp.com/servers/testing> and <https://gofastmcp.com/development/tests>. | Add or update tests that inspect both primary and vnext servers' tools, resources, prompts, schemas, metadata, and instructions. |
| gh-aw compilation and safety | gh-aw workflows are Markdown plus YAML frontmatter and must compile to `.lock.yml`; write permissions are not allowed in workflow permissions and GitHub writes should use `safe-outputs`. Source: <https://github.com/github/gh-aw/blob/v0.67.1/.github/aw/github-agentic-workflows.md>. | Any workflow source change must compile, and mutating outputs should remain in `safe-outputs`, not raw `gh` or write-scoped workflow permissions. |
| gh-aw deterministic boundaries | gh-aw custom `steps`/`jobs` run outside the Agent Workflow Firewall and should be deterministic preparation/cleanup, not agentic compute. `network` and `tools` frontmatter define allowed egress and tools; strict mode must stay enabled. Source: <https://github.com/github/gh-aw/blob/v0.67.1/.github/aw/github-agentic-workflows.md>. | Move data collection/diff generation into deterministic scripts or custom steps; keep agent prompts bounded to summarization and decisions. |

## Repo surface inventory

| Surface | Classification | Canonical source or role |
| --- | --- | --- |
| `.github/copilot-instructions.md` | Always-on Copilot adapter | Project overview, commands, conventions, and links to this map. Do not add tranche-specific workflow detail here. |
| `.github/agent-harness-map.md` | Canonical harness map | Owns issue-tranche routing, capability gaps, verifier roles, and stop conditions. |
| `.github/instructions/documentation.instructions.md` | Scoped docs rule | Canonical MDX and style rules for docs content. |
| `docs.json`, `docs/docs.json`, `docs-vnext/docs.json` | Mintlify navigation/config surfaces | Source of truth for deployed navigation and page grouping across the root site, primary docs corpus, and docs-vnext corpus. |
| `docs-vnext/.mintlify/AGENTS.md` | Nested docs-vnext adapter | Local agent guidance for docs-vnext files. |
| `docs-vnext/.mintlify/Assistant.md` | Mintlify assistant surface | Docs-vnext assistant-facing guidance; include in #474 readiness checks when validating Mintlify agent context. |
| `.github/agents/agentic-workflows.agent.md` | Copilot custom agent | gh-aw dispatcher and workflow-authoring adapter; references gh-aw prompts and constraints. |
| `.github/workflows/*.md` | gh-aw workflow sources | Scheduled, slash-command, and report automation sources that must compile to `.lock.yml`. |
| `.github/workflows/shared/*.md` | Shared gh-aw components | Report style, mood, docs-server lifecycle, and reusable workflow guidance. |
| `.github/workflows/shared/mcp/*.md` | Shared MCP wrappers | Workflow-local MCP configurations for Microsoft Learn, Mintlify docs, and this repo's Foundry docs MCP. |
| `.mcp.json` | Repo MCP client config | Local/client MCP connection hints. Configured servers are `microsoft-foundry-docs-vnext` over HTTP at the hosted Mintlify `/mcp` endpoint, and `perplexity` over stdio with `PERPLEXITY_API_KEY` supplied through user input; the latter is a third-party/private-key surface and must not be used in unattended repo workflows without explicit approval. |
| `fastmcp.json` | FastMCP packaging metadata | Server name, version, description, entrypoint, and deployment transport for the primary server. |
| `foundry_docs_mcp/_server_factory.py` | MCP server implementation | Source of truth for primary/vnext FastMCP tools, resources, prompts, lifespan search indexes, and Azure hybrid fallback behavior. |
| `scripts/*.py` | Deterministic automation | Source of truth for model catalog scrape, docs sync/conversion, indexing, retrieval testbench, A/B/C/D eval, and answer-quality eval. |
| `tests/*.py` and `tests/*.json` | Deterministic validation | Unit tests plus retrieval and answer-quality fixtures; dependent tranches should extend these before relying on reports. |
| `README.md` | Human setup reference | Installation, MCP tools, Azure configuration, pipeline scripts, and ongoing automation summary. |

## Workflow and automation inventory

| Workflow source | Current owner | Current risk | Follow-on tranche |
| --- | --- | --- | --- |
| `.github/workflows/model-catalog-sync.md` | gh-aw scheduled/report workflow plus `scripts/scrape_model_catalog.py` | Script already uses public asset-gallery API, but the workflow still lets the agent own too much PR/report interpretation and needs explicit watchdog/block handling. | #468 |
| `.github/workflows/docs-vnext-diff-report.md` | gh-aw scheduled report | Prompt performs process substitution and unbounded diff iteration inside the agent. | #469 |
| `.github/workflows/docs-noob-tester.md` | gh-aw scheduled browser/web-fetch report | Prompt allows generic success-shaped reports and does not enforce concrete non-placeholder evidence. | #471 |
| `.github/workflows/post-index-sync-testbench.md` | gh-aw post-index check | Uses `scripts/run_testbench.py`; depends on retrieval harness integrity and explicit Azure setup handling. | #470 |
| `.github/workflows/search-test.md` | gh-aw slash command | One-off search testing; should inherit repaired path normalization and output reporting from the harness. | #470 |
| `.github/workflows/docs-vnext-sync.md`, `post-sync-updater.md`, `post-merge-docs-verify.md` | gh-aw docs maintenance | Must preserve docs/docs-vnext corpus ownership and generated-content boundaries. | #473 |
| `.github/workflows/shared/reporting.md` | Shared report policy | Good baseline for issue reports; dependent workflows should use it for cleanup and progressive disclosure. | #469, #471, #475 |
| `.github/workflows/shared/mcp/*.md` | Workflow MCP context | Useful for workflow-local retrieval, but should not replace deterministic eval source selection. | #470, #474 |

## Deterministic validation commands

Use commands from this table as source-of-truth gates. Do not replace them with agent judgment.

| Area | Command | Owner |
| --- | --- | --- |
| Python unit tests | `pytest` or targeted `pytest tests/test_chunker.py` | Local/Copilot implementation session |
| Python lint | `ruff check .` | Local/Copilot implementation session |
| Retrieval regression | `python scripts/run_testbench.py --test-file tests/search_testbench.json --top-k 10 --min-pass-rate 0.90 --min-tests 1` | #470 actor, then workflow |
| A/B/C/D retrieval comparison | `python scripts/run_abcd_eval.py --test-file tests/search_testbench.json --top-k 10` | #470/#475 actor |
| Answer-quality matrix | `python scripts/run_docs_eval.py --dry-run` first, then selected `--server`, `--models`, and full matrix runs after MCP selection is enforced | #470/#475 actor |
| Azure Search ingestion | `python scripts/ingest_to_azure_search.py --dry-run`, then approved live sync | #470/#475 actor with Azure setup gate |
| Model catalog scrape | `python scripts/scrape_model_catalog.py --include-partners --output docs/static/data` plus bounded docs-vnext copy/check | #468 actor |
| gh-aw compile | `gh aw compile --validate` or `gh aw compile --json --no-emit` where available | Any workflow tranche |
| Markdown diff hygiene | `git diff --check` | Any tranche |
| Mintlify readiness | `mint broken-links`, `mint validate`, and configured Mintlify CI checks where available | #474 actor/verifier |

## Follow-on tranche routing

| Issue | Harness surface | Mode | Tool and permission policy | Stop condition | Verifier role |
| --- | --- | --- | --- | --- | --- |
| #468 Model catalog API sync with Playwright watchdog | Copilot implementation session plus deterministic Python script; gh-aw only after script contract is stable | One-shot repo task, then scheduled workflow | Allow editing `scripts/scrape_model_catalog.py`, tests, bounded data outputs, and workflow source/lock. Use read-only GitHub tools; PR creation only via gh-aw `safe-outputs`. Deny protected workflow-file mutation from an agent-created PR unless explicitly approved. | API pagination/detail data validates, output shape remains compatible with `docs/static/data` and `docs-vnext/static/data`, watchdog reports API/UI contract drift or blocked infra explicitly. | Code-review or task verifier checks diff, output bounds, and failure modes. |
| #469 Deterministic docs-vnext diff report workflow | Deterministic Python artifact generator plus gh-aw report summarizer | Sequential pipeline | Script may read `docs/`, `docs-vnext/`, git metadata, and GitHub PR metadata. Agent prompt consumes precomputed JSON/Markdown only. Report issue through `safe-outputs.create-issue`; noop through `safe-outputs.noop`. | Bounded JSON and Markdown artifacts include file counts, vnext-only files, modified files, line/word deltas, recent PR activity, noop/blocked states. Workflow no longer performs unbounded shell diffing in prompt. | Verifier runs generator on current repo and inspects artifact schema and report prompt. |
| #470 Evaluation harness matrix integrity | Copilot implementation session with deterministic tests/scripts | One-shot repo task with optional Builder/Inspector verification | Allow edits to `scripts/run_testbench.py`, `scripts/run_abcd_eval.py`, `scripts/run_docs_eval.py`, eval fixtures, and tests. Deny silent local fallback for final Azure-required mode. External model/API calls must be explicit and configurable. | Path normalization, Windows-safe output, required Azure mode diagnostics, per-server/model enforcement, complete raw/scored denominators, and separated retrieval vs answer-quality artifacts are implemented. | Independent verifier runs dry-run, targeted unit tests, and at least local deterministic eval smoke. |
| #471 Noob tester quality gate and infrastructure-blocked reporting | gh-aw report workflow plus deterministic report validator | Sequential pipeline | Agent may fetch docs-vnext pages and use Playwright where available. Publishing requires non-placeholder report schema or explicit blocked output through `report-incomplete`/issue. | Success reports contain URLs, task attempts, friction, failures, what worked, and recommendations; browser/network/firewall blocks cannot publish as success. | Verifier checks validator rejects placeholders and workflow distinguishes no findings from incomplete execution. |
| #472 Hosted-agent freshness, pivot, truncation, and disambiguation tests | Deterministic eval fixture/test extension | One-shot repo task | Allow edits to retrieval and answer-quality fixtures plus scoring metadata. No docs content changes until #473. | New scenarios fail stale/bad patterns and pass intended hosted-agent guidance with normalized expected paths. | Verifier runs repaired harness slice from #470. |
| #473 Refresh hosted-agent docs through proper corpus paths | Docs-vnext content implementation plus generated docs pipeline only for `docs/` | One-shot docs task | `docs/` changes only through upstream sync/conversion output; `docs-vnext/` may diverge intentionally under docs-vnext rules. No manual corruption of generated canonical docs. | Hosted-agent stale packages, azd versions, commands, prerequisites, deployment/test steps, navigation, links, and terminology pass #472 scenarios. | Documentation verifier checks scoped MDX rules, nav, links, and drift scenarios. |
| #474 Mintlify and FastMCP agent-readiness surface update | Deterministic MCP inspection tests plus docs/readiness workflow guidance | One-shot repo task | Allow FastMCP client tests, MCP discovery checks, README/workflow references. Mintlify dashboard checks reported as unavailable/not configured unless verifiable. | Primary/vnext FastMCP tools/resources/prompts/schemas/metadata are inspected; Mintlify `/mcp`, `/.well-known/mcp*`, `/skill.md`, and `llms` readiness state is documented or checked; variants are distinguishable in reports. | Verifier runs in-memory FastMCP tests and hosted endpoint checks where network allows. |
| #475 Workflow rerun and final evidence package | Copilot app/session orchestration plus gh-aw/manual workflow dispatch | Human-gated final pipeline | Workflow reruns, final Azure-backed retrieval, and model answer-quality runs require explicit human approval and configured credentials. Agent may package evidence after approved runs. | Fixed workflows rerun, raw/scored artifacts and stakeholder report exist, Azure-backed setup is included or marked setup-failed, and repo-owned evidence is separated from Microsoft Learn issues. | Synthesizer plus verifier reviews links, denominators, blocked states, and report claims. |

## Capability gaps and routes

| Gap | Impact | Recommended route |
| --- | --- | --- |
| No committed FastMCP inspection tests for both servers | MCP readiness can regress without failing CI. | Use existing FastMCP client and pytest patterns; add targeted tests in #474. |
| Eval harness does not enforce selected MCP/server source per row | Answer-quality matrix can claim a source without actually constraining the agent to it. | Keep deterministic; repair `scripts/run_docs_eval.py` in #470 before final rerun. |
| Azure hybrid mode can fall back to local in server/runtime paths | Final evidence could omit the required Azure-backed variant. | Add explicit required mode/setup diagnostics in #470; keep local fallback only for non-final dev mode. |
| gh-aw report prompts perform unbounded shell work | Scheduled agents can time out or produce inconsistent reports. | Move collection to deterministic scripts/custom prep steps; agent summarizes bounded artifacts in #469 and #471. |
| Mintlify dashboard CI/readiness settings are not represented in repo | Agents cannot distinguish missing setup from passing readiness. | In #474, inspect hosted endpoints and document dashboard-dependent checks as "not configured" unless verifiable. |
| No reusable committed skill for this repo's evaluation rerun | Future agents may repeat context-heavy setup from issues. | After #470/#474 stabilize, consider `skill-creator` for a repo skill only if the workflow repeats. |
| Protected workflow-file PR behavior is unclear for automation | Agents could attempt unsafe workflow-file edits or PRs. | Keep gh-aw workflow mutations in human-owned implementation sessions; use safe-output fallback issue/report paths for scheduled agents. |

## Human-gated actions

These actions require explicit human approval or an already-approved gh-aw safe-output path with bounded payloads:

- Creating, closing, or updating public issues/PRs beyond configured `safe-outputs`.
- Dispatching, rerunning, or enabling workflows for the final evidence package.
- Publishing or merging PRs.
- Installing MCP servers, skills, plugins, or marketplace packages.
- Connecting authenticated Mintlify MCP, Azure, Microsoft 365, or other private-data providers.
- Running Azure-backed final evals that consume credentials or quota.
- Editing generated `docs/` content outside the sync/conversion pipeline.

## Canonical source-of-truth rules

- Project overview, commands, and coding conventions: `.github/copilot-instructions.md`.
- Tranche routing, harness ownership, capability gaps, and verification roles: `.github/agent-harness-map.md`.
- Docs-vnext MDX writing rules: `.github/instructions/documentation.instructions.md` and `docs-vnext/.mintlify/AGENTS.md`.
- gh-aw workflow behavior: `.github/workflows/*.md`, shared imports, compiled `.lock.yml` files, and current gh-aw docs.
- MCP server behavior: `foundry_docs_mcp/_server_factory.py`, `foundry_docs_mcp/server.py`, `foundry_docs_vnext_mcp/server.py`, and FastMCP client inspection tests.
- Evaluation truth: `tests/search_testbench.json`, `tests/docs_eval_scenarios.json`, `scripts/run_testbench.py`, `scripts/run_abcd_eval.py`, `scripts/run_docs_eval.py`, and generated raw/scored artifacts.
