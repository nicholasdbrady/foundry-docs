# API doc accuracy dashboard

This dashboard definition provides a repeatable scorecard for Microsoft Foundry API reference quality. It is intended for weekly review by documentation owners, SDK partners, and API program leads.

## Overall accuracy score methodology

The overall accuracy score is a weighted score from 0 to 100.

| Signal | Weight | Scoring rule |
| --- | --- | --- |
| Example validity | 45% | Percent of endpoint pages whose runnable examples pass JSON, auth-header, required-field, and placeholder checks. |
| Spec alignment | 35% | Percent of endpoint pages with no unresolved path, parameter, enum, or response drift findings. |
| Metadata freshness | 20% | Percent of endpoint pages whose metadata is complete and within the freshness SLA. |

**Formula**

```text
overall_accuracy_score =
  (example_validity * 0.45) +
  (spec_alignment * 0.35) +
  (metadata_freshness * 0.20)
```

**Interpretation**

- `95-100`: release-ready
- `90-94.9`: healthy, monitor minor drift
- `80-89.9`: needs planned remediation
- `<80`: escalation required

## Current reporting snapshot

- Reporting date: **2026-05-28**
- Pages in scope: **128**
- Pages with passing runnable examples: **111**
- Pages with zero unresolved spec drift findings: **106**
- Pages with fresh metadata: **118**
- Overall score: **86.4**

## Per-resource-group accuracy breakdown

| Resource group | Example validity | Spec alignment | Metadata freshness | Overall score | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Agents | 94% | 91% | 96% | 93.4 | Healthy |
| Threads | 92% | 89% | 95% | 91.6 | Healthy |
| Runs | 86% | 84% | 93% | 86.7 | Needs work |
| Messages | 90% | 88% | 94% | 90.1 | Healthy |
| Connections | 79% | 83% | 90% | 82.6 | Needs work |
| Deployments | 72% | 77% | 88% | 77.0 | Escalate |
| Evaluations | 68% | 74% | 85% | 73.5 | Escalate |

## Sample dashboard layout

### 1. Executive scorecard

| Metric | Current week | Previous week | Delta |
| --- | ---: | ---: | ---: |
| Overall accuracy score | 86.4 | 84.7 | +1.7 |
| Example validity | 86.7 | 82.8 | +3.9 |
| Spec alignment | 82.8 | 80.5 | +2.3 |
| Metadata freshness | 92.2 | 90.6 | +1.6 |
| Blocking errors | 14 | 21 | -7 |
| Warning findings | 32 | 37 | -5 |

### 2. Resource-group detail

| Resource group | Pages | Passing examples | Drift-free pages | Fresh pages | Top issue |
| --- | ---: | ---: | ---: | ---: | --- |
| Agents | 24 | 23 | 22 | 23 | Missing `api-key` alternative on two examples |
| Threads | 18 | 17 | 16 | 17 | One stale `last_verified_at` field |
| Runs | 21 | 18 | 17 | 20 | `submit-tool-outputs` examples missing required fields |
| Messages | 14 | 13 | 12 | 13 | Pagination query examples need `order` cleanup |
| Connections | 16 | 12 | 13 | 14 | ARM payload examples drifted from latest auth schema |
| Deployments | 17 | 11 | 12 | 15 | Deployment list examples still use legacy path names |
| Evaluations | 18 | 12 | 14 | 15 | Preview headers missing from multiple examples |

### 3. Open issues requiring action

| Severity | Resource group | Issue | Owner | SLA due |
| --- | --- | --- | --- | --- |
| Error | Deployments | `DOC-PATH-001`: legacy `/modelDeployments` path still documented on three pages | Models docs owner | 2026-06-03 |
| Error | Evaluations | `DOC-AUTH-002`: preview header omitted from create-evaluation examples | Eval docs owner | 2026-06-02 |
| Error | Runs | `DOC-EX-002`: required `assistant_id` missing from one create-run example | Agent docs owner | 2026-06-01 |
| Warning | Connections | `META-005`: four connection pages older than 90 days | Platform docs owner | 2026-06-07 |
| Warning | Messages | `DRIFT-RESP-001`: list response now includes `has_more` but sample response does not | Agent docs owner | 2026-06-05 |

## Trend tracking

Track week-over-week movement by storing one record per resource group and one aggregate record per run.

Recommended fields:

| Field | Description |
| --- | --- |
| `report_week` | ISO week, for example `2026-W22` |
| `resource_group` | Agents, Threads, Runs, Messages, Connections, Deployments, Evaluations, or `ALL` |
| `example_validity` | Percentage for the week |
| `spec_alignment` | Percentage for the week |
| `metadata_freshness` | Percentage for the week |
| `overall_score` | Weighted score for the week |
| `blocking_errors` | Count of error findings |
| `warning_findings` | Count of warning findings |

Example trend table:

| Week | Overall | Agents | Runs | Deployments | Evaluations |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-W19 | 81.7 | 89.8 | 80.6 | 71.2 | 69.0 |
| 2026-W20 | 83.4 | 90.7 | 82.1 | 73.0 | 70.4 |
| 2026-W21 | 84.7 | 92.3 | 84.6 | 75.8 | 72.5 |
| 2026-W22 | 86.4 | 93.4 | 86.7 | 77.0 | 73.5 |

## Alert thresholds

| Condition | Threshold | Action |
| --- | --- | --- |
| Overall score drop | More than 3 points week over week | Notify DX program lead and owning content lead within one business day |
| Resource group score | Below 80 | Create remediation work item and include in weekly review |
| Blocking errors | 10 or more on any resource group | Escalate to engineering and docs owner |
| Metadata freshness | Below 90% for GA pages | Trigger reverification sweep |
| Preview coverage | Below 85% freshness for preview pages | Freeze new preview page publication until reverified |
| Spec drift backlog | Any unresolved drift older than 7 days | Escalate in ship-room review |

## Operational guidance

1. Publish the dashboard after every PR validation run and nightly full-corpus scan.
2. Keep the sample data source immutable for week-over-week comparisons.
3. Separate blocking findings from warning-only findings so teams can prioritize remediation work.
4. Pair the dashboard with the smoke-test endpoint set to confirm that high-scoring pages also map to live, callable operations.
