# Quarterly competitive benchmark template

## Benchmark summary

- **Quarter:** YYYY-QN
- **Prepared by:** TEAM_OR_OWNER
- **Date completed:** YYYY-MM-DD
- **Primary scenario set:** FIRST_RUN_FLOW, CORE_AGENT_TASKS, ERROR_RECOVERY, OBSERVABILITY
- **Evidence links:** DOC_LINK_1, DOC_LINK_2, TEST_RUN_LINK_1

## Benchmark dimensions

Score every comparison target on the following dimensions.

1. **First-run flow clarity** — how quickly a new developer can find the right entry point and produce the first successful call.
2. **Task completion speed** — how many steps are required to complete common tasks without outside help.
3. **Error resolution quality** — how directly the docs explain failure modes, diagnostics, and fixes.
4. **Example trustworthiness** — whether examples are current, runnable, and aligned with the actual API behavior.
5. **Observability guidance depth** — whether tracing, metrics, retries, streaming diagnostics, and production debugging guidance are easy to find and actionable.

## Scoring rubric (1 to 5)

| Score | Criteria |
| --- | --- |
| **1** | Major task blockers. Entry points are unclear, examples are incomplete or stale, and failure handling is mostly absent. |
| **2** | Basic task coverage exists, but important setup or troubleshooting steps are missing. Readers often need outside sources to finish. |
| **3** | Most common tasks are documented and mostly accurate, but the experience still has friction, gaps, or inconsistent depth. |
| **4** | Core tasks are easy to complete, examples are reliable, and troubleshooting is practical for most production scenarios. |
| **5** | Best-in-class experience. Readers can move from first run to production operations with minimal ambiguity and strong diagnostic support. |

## Comparison targets

- OpenAI
- Google Vertex AI
- AWS Bedrock
- Anthropic
- LangChain
- Microsoft Foundry

## Data collection methodology

### Scenario set

Run the same scenario set for every vendor each quarter.

| Scenario ID | Scenario | Expected outcome |
| --- | --- | --- |
| `FR-01` | Create a new project and complete the first successful API call | Working request in less than 30 minutes |
| `AG-01` | Create an agent, send a prompt, and retrieve output | End-to-end success with current examples |
| `ER-01` | Diagnose a forced auth or payload error | Root cause identified and fixed using docs only |
| `RT-01` | Handle a throttling or retry case | Retry logic implemented from documentation |
| `OB-01` | Find tracing, metrics, or streaming diagnostics guidance | Production debugging path documented clearly |

### Collection process

1. Use a fresh evaluator who did not author the docs being scored.
2. Time each scenario from first page load to successful completion.
3. Record every page visited, command run, and blocker encountered.
4. Force at least one authentication, payload, and throttling failure during the run.
5. Score each dimension immediately after the scenario while evidence is still fresh.
6. Capture screenshots or page URLs for any claim that materially affects the score.

### Evidence checklist

- scenario timing notes
- failed commands and final working commands
- screenshots or links for missing content
- copied error messages
- URLs for the pages that resolved or failed to resolve the issue

## Scoring table template

| Vendor | First-run flow clarity | Task completion speed | Error resolution quality | Example trustworthiness | Observability guidance depth | Weighted average | Evidence summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Microsoft Foundry | SCORE | SCORE | SCORE | SCORE | SCORE | AVG | SHORT_SUMMARY |
| OpenAI | SCORE | SCORE | SCORE | SCORE | SCORE | AVG | SHORT_SUMMARY |
| Google Vertex AI | SCORE | SCORE | SCORE | SCORE | SCORE | AVG | SHORT_SUMMARY |
| AWS Bedrock | SCORE | SCORE | SCORE | SCORE | SCORE | AVG | SHORT_SUMMARY |
| Anthropic | SCORE | SCORE | SCORE | SCORE | SCORE | AVG | SHORT_SUMMARY |
| LangChain | SCORE | SCORE | SCORE | SCORE | SCORE | AVG | SHORT_SUMMARY |

## Sample filled-in table (realistic example)

| Vendor | First-run flow clarity | Task completion speed | Error resolution quality | Example trustworthiness | Observability guidance depth | Weighted average | Evidence summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Microsoft Foundry | 4 | 4 | 4 | 4 | 3 | 3.8 | Strong task coverage and better playbooks; observability still split across pages |
| OpenAI | 5 | 5 | 3 | 5 | 3 | 4.2 | Fast first run and strong examples; troubleshooting is less operationally specific |
| Google Vertex AI | 3 | 3 | 3 | 4 | 4 | 3.4 | Good platform depth, but first-run path remains fragmented |
| AWS Bedrock | 3 | 3 | 2 | 3 | 4 | 3.0 | Production details are present, but common task flow is slower |
| Anthropic | 4 | 4 | 3 | 4 | 2 | 3.4 | Simple model usage is strong; platform operations are comparatively light |
| LangChain | 3 | 4 | 2 | 3 | 3 | 3.0 | Fast orchestration examples, but vendor-specific failure guidance is limited |

## Gap analysis notes

Use this section to explain why a score moved.

### What improved this quarter

- IMPROVEMENT_1
- IMPROVEMENT_2

### What regressed this quarter

- REGRESSION_1
- REGRESSION_2

### Where competitors still lead

- COMPETITOR_ADVANTAGE_1
- COMPETITOR_ADVANTAGE_2

## Action items template

| Gap ID | Dimension | Evidence | Current impact | Recommended action | Owner | Target quarter | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GAP-01 | Error resolution quality | LINK_OR_NOTE | SUPPORT_LOAD_OR_TASK_FAILURE | CREATE_OR_UPDATE_PLAYBOOK | OWNER | YYYY-QN | Not started |
| GAP-02 | Observability guidance depth | LINK_OR_NOTE | SLOW_PRODUCTION_DEBUGGING | ADD_TRACING_AND_METRICS_GUIDE | OWNER | YYYY-QN | Not started |
| GAP-03 | Example trustworthiness | LINK_OR_NOTE | COPY_PASTE_FAILURES | REFRESH_SAMPLES_AND_ADD_CONTRACT_TESTS | OWNER | YYYY-QN | Not started |

## Quarter-over-quarter trend tracking

### Dimension trend table

| Dimension | Previous quarter | Current quarter | Delta | Trend note |
| --- | --- | --- | --- | --- |
| First-run flow clarity | PREV | CURR | DELTA | NOTE |
| Task completion speed | PREV | CURR | DELTA | NOTE |
| Error resolution quality | PREV | CURR | DELTA | NOTE |
| Example trustworthiness | PREV | CURR | DELTA | NOTE |
| Observability guidance depth | PREV | CURR | DELTA | NOTE |

### Vendor rank trend table

| Quarter | Microsoft Foundry rank | Closest leader | Biggest gap | Biggest improvement |
| --- | --- | --- | --- | --- |
| YYYY-QN | RANK | VENDOR | DIMENSION | DIMENSION |
| YYYY-QN-1 | RANK | VENDOR | DIMENSION | DIMENSION |
| YYYY-QN-2 | RANK | VENDOR | DIMENSION | DIMENSION |

## Final readout

- **Top strength this quarter:** STRENGTH
- **Most urgent gap:** GAP
- **Docs investment recommended next quarter:** INVESTMENT_AREA
- **Expected success metric:** TARGET_METRIC
