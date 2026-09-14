# API documentation validation rules

This document defines the quality gates for Microsoft Foundry API reference pages under the DX Improvement Program. The rules are designed for automated enforcement in pull requests and scheduled audits. Unless a rule is marked as partially automated, a failing rule should block merge.

## Scope

- Applies to endpoint reference pages and generated example fragments.
- Uses the checked-in OpenAPI file as the source of truth for paths, parameters, request bodies, response schemas, enum values, and required headers.
- Treats both project data-plane pages (for example, `/agents`, `/threads/{threadId}/runs`) and management-plane pages (for example, project connections) as in scope.

## Required page metadata

Each endpoint page must include the following frontmatter fields:

```yaml
---
title: Create an agent
description: Create a Foundry agent.
last_verified_at: 2026-05-28
api_version: v1
preview_or_ga_status: ga
example_validation_status: passed
---
```

| Field | Required value | Validation rule |
| --- | --- | --- |
| `last_verified_at` | ISO date (`YYYY-MM-DD`) | `META-001`, `META-005` |
| `api_version` | Explicit API version used on the page | `META-002` |
| `preview_or_ga_status` | `preview` or `ga` | `META-003` |
| `example_validation_status` | `passed`, `failed`, or `not-run` | `META-004` |

## Severity model

- **error**: blocks merge until fixed.
- **warning**: merge allowed only with explicit reviewer acknowledgment.
- **info**: recorded in reports, does not block merge.

## Rule summary

| Rule ID | Severity | Automated check feasibility | Summary |
| --- | --- | --- | --- |
| `DOC-EX-001` | error | fully automated | Every endpoint page has at least one runnable cURL example. |
| `DOC-EX-002` | error | fully automated | All required parameters appear in at least one runnable example. |
| `DOC-EX-003` | error | fully automated | Enum values used in examples match the current OpenAPI spec. |
| `DOC-AUTH-001` | error | fully automated | Required auth headers are present in every runnable example. |
| `DOC-AUTH-002` | error | partially automated | Preview or feature-flag headers are documented where required. |
| `DOC-JSON-001` | error | fully automated | Request JSON is valid and matches the request schema shape. |
| `DOC-JSON-002` | error | fully automated | Response JSON is valid and matches the response schema shape. |
| `DOC-PATH-001` | error | fully automated | URL paths in examples match current spec paths. |
| `DOC-QUERY-001` | error | fully automated | Query parameters match spec requirements and names. |
| `DOC-HEAD-001` | warning | fully automated | Content negotiation and body-related headers are present when needed. |
| `DRIFT-OP-001` | warning | fully automated | Changed operation IDs trigger doc review. |
| `DRIFT-PARAM-001` | error | fully automated | Added, removed, or renamed parameters flag impacted pages. |
| `DRIFT-RESP-001` | warning | fully automated | Response shape changes flag impacted pages. |
| `DRIFT-HEAD-001` | error | fully automated | New required headers are added to all affected examples. |
| `META-001` | error | fully automated | `last_verified_at` is present and is an ISO date. |
| `META-002` | error | fully automated | `api_version` is present on every endpoint page. |
| `META-003` | error | fully automated | `preview_or_ga_status` is present and valid. |
| `META-004` | error | fully automated | `example_validation_status` is present and valid. |
| `META-005` | warning | fully automated | Metadata freshness is within the allowed verification window. |
| `DOC-PLACEHOLDER-001` | warning | fully automated | Internal placeholder tokens are not left in published examples. |

---

## `DOC-EX-001` — Runnable cURL example required

- **Description:** Every endpoint page must include at least one complete cURL example that can be executed after substituting documented environment variables.
- **Severity:** error
- **Automated check feasibility:** fully automated by parsing fenced code blocks and verifying `curl`, `--url`, and required request pieces are present.
- **Passing example:**

```bash
curl --request POST \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/agents?api-version=v1" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"support-agent","model":"gpt-4.1-mini"}'
```

- **Failing example:**

```text
POST /agents
{"name":"support-agent"}
```

## `DOC-EX-002` — Required parameters must appear in examples

- **Description:** Every required path, query, header, and body parameter defined in the OpenAPI operation must appear in at least one runnable example on the page.
- **Severity:** error
- **Automated check feasibility:** fully automated by comparing extracted examples with the spec's `required` contract.
- **Passing example:**

```bash
curl --request POST \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/threads/$THREAD_ID/runs?api-version=v1" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"assistant_id":"agent_123"}'
```

- **Failing example:**

```bash
curl --request POST \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/threads/$THREAD_ID/runs?api-version=v1" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## `DOC-EX-003` — Enum values in examples must match the spec

- **Description:** Example payloads must only use enum values that are currently allowed by the OpenAPI schema.
- **Severity:** error
- **Automated check feasibility:** fully automated by validating example payloads against enum sets in the spec.
- **Passing example:**

```json
{"tool_choice":"auto"}
```

- **Failing example:**

```json
{"tool_choice":"automatic"}
```

## `DOC-AUTH-001` — Required auth headers must be present

- **Description:** Every runnable example must include the auth header required by the operation, typically `Authorization` for Foundry project endpoints or `api-key` where key-based auth is documented.
- **Severity:** error
- **Automated check feasibility:** fully automated by checking required security schemes and matching headers in code blocks.
- **Passing example:**

```bash
curl --request GET \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/agents/$AGENT_ID?api-version=v1" \
  -H "Authorization: Bearer $AGENT_TOKEN"
```

- **Failing example:**

```bash
curl --request GET \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/agents/$AGENT_ID?api-version=v1"
```

## `DOC-AUTH-002` — Preview and feature-flag headers must be documented

- **Description:** If an operation requires a preview gate or feature-flag header, every example for that operation must show it explicitly.
- **Severity:** error
- **Automated check feasibility:** partially automated because the spec can identify required headers, but rollout notes sometimes live in vendor extensions or release metadata that also need reviewer confirmation.
- **Passing example:**

```bash
curl --request POST \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/evaluations?api-version=v1" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "x-ms-enable-preview: true" \
  -H "Content-Type: application/json" \
  -d '{"name":"support-eval"}'
```

- **Failing example:**

```bash
curl --request POST \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/evaluations?api-version=v1" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"support-eval"}'
```

## `DOC-JSON-001` — Request JSON must be valid and schema-aligned

- **Description:** Request payload examples must parse as valid JSON and match the expected object shape, types, and required fields defined by the request schema.
- **Severity:** error
- **Automated check feasibility:** fully automated by extracting `-d` payloads and validating them with JSON Schema derived from OpenAPI.
- **Passing example:**

```json
{"name":"support-agent","model":"gpt-4.1-mini","instructions":"Answer support questions."}
```

- **Failing example:**

```json
{"name":"support-agent","model":["gpt-4.1-mini"],}
```

## `DOC-JSON-002` — Response JSON must be valid and schema-aligned

- **Description:** Sample responses must be valid JSON and remain consistent with the current response schema, including required properties and container shapes.
- **Severity:** error
- **Automated check feasibility:** fully automated by validating JSON examples against the response schema for the documented status code.
- **Passing example:**

```json
{"id":"agent_123","object":"agent","name":"support-agent","model":"gpt-4.1-mini"}
```

- **Failing example:**

```json
[{"id":"agent_123","name":"support-agent"}]
```

## `DOC-PATH-001` — URL paths must match the current spec

- **Description:** The URL path shown in docs must match an existing path template in the checked-in OpenAPI spec.
- **Severity:** error
- **Automated check feasibility:** fully automated by normalizing hostnames and comparing extracted URL paths against spec paths.
- **Passing example:**

```bash
curl --request POST \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/threads/$THREAD_ID/messages?api-version=v1"
```

- **Failing example:**

```bash
curl --request POST \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/thread/$THREAD_ID/message?api-version=v1"
```

## `DOC-QUERY-001` — Query parameters must match the spec

- **Description:** Required query parameters must always be present, optional query parameters must use supported names, and unsupported query parameters must not appear.
- **Severity:** error
- **Automated check feasibility:** fully automated by comparing example query strings against the OpenAPI parameter list.
- **Passing example:**

```bash
curl --request GET \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/threads/$THREAD_ID/messages?api-version=v1&limit=20&order=desc"
```

- **Failing example:**

```bash
curl --request GET \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/threads/$THREAD_ID/messages?pageSize=20"
```

## `DOC-HEAD-001` — Request-format headers must be present when needed

- **Description:** Examples with request bodies must include `Content-Type: application/json`, and examples that rely on a specific negotiated response should include `Accept` when the API contract requires it.
- **Severity:** warning
- **Automated check feasibility:** fully automated for common cases based on body presence and OpenAPI media types.
- **Passing example:**

```bash
curl --request PUT \
  --url "$MGMT_ENDPOINT/connections/$CONNECTION_NAME?api-version=2025-06-01" \
  -H "Authorization: Bearer $MGMT_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"properties":{"authType":"ApiKey"}}'
```

- **Failing example:**

```bash
curl --request PUT \
  --url "$MGMT_ENDPOINT/connections/$CONNECTION_NAME?api-version=2025-06-01" \
  -H "Authorization: Bearer $MGMT_TOKEN" \
  -d '{"properties":{"authType":"ApiKey"}}'
```

## `DRIFT-OP-001` — Changed operation IDs trigger doc review

- **Description:** If an operation ID changes in the OpenAPI spec, every page mapped to the previous or new operation ID must be flagged for review even if the path is unchanged.
- **Severity:** warning
- **Automated check feasibility:** fully automated by diffing base and head specs.
- **Passing example:**

```text
Base spec: listAgents
Head spec: listAgents
Result: no review required for operation ID drift
```

- **Failing example:**

```text
Base spec: getThreadRun
Head spec: retrieveRun
Result: linked run-status page flagged for review
```

## `DRIFT-PARAM-001` — Parameter changes flag impacted pages

- **Description:** Added, removed, renamed, or newly required parameters must flag every page that documents the impacted operation.
- **Severity:** error
- **Automated check feasibility:** fully automated by comparing base and head parameter signatures.
- **Passing example:**

```text
Base spec parameters: threadId, runId
Head spec parameters: threadId, runId
Result: no action
```

- **Failing example:**

```text
Base spec parameters: threadId, runId
Head spec parameters: threadId, runId, include_steps (required)
Result: run retrieval page flagged until examples include include_steps
```

## `DRIFT-RESP-001` — Response shape changes flag impacted pages

- **Description:** If a success response adds, removes, renames, or changes the type of a property, pages that show sample responses for that operation must be reviewed.
- **Severity:** warning
- **Automated check feasibility:** fully automated by comparing normalized schema fragments for success responses.
- **Passing example:**

```text
Base response fields: id, status, thread_id
Head response fields: id, status, thread_id
Result: no action
```

- **Failing example:**

```text
Base response fields: id, status
Head response fields: id, status, usage
Result: response example review required
```

## `DRIFT-HEAD-001` — New required headers must be added to examples

- **Description:** If a spec change introduces a new required header, every affected example must be updated in the same change or the PR fails.
- **Severity:** error
- **Automated check feasibility:** fully automated by diffing required header parameters and validating examples.
- **Passing example:**

```text
Base required headers: Authorization
Head required headers: Authorization, x-ms-client-request-id
Docs updated: yes
Result: pass
```

- **Failing example:**

```text
Base required headers: Authorization
Head required headers: Authorization, x-ms-client-request-id
Docs updated: no
Result: fail
```

## `META-001` — `last_verified_at` is required and must be ISO formatted

- **Description:** Every endpoint page must include `last_verified_at` in `YYYY-MM-DD` format.
- **Severity:** error
- **Automated check feasibility:** fully automated using frontmatter parsing and strict date validation.
- **Passing example:**

```yaml
last_verified_at: 2026-05-28
```

- **Failing example:**

```yaml
last_verified_at: May 28, 2026
```

## `META-002` — `api_version` is required

- **Description:** Every endpoint page must declare the exact API version used by its examples and schema snapshots.
- **Severity:** error
- **Automated check feasibility:** fully automated by frontmatter parsing.
- **Passing example:**

```yaml
api_version: v1
```

- **Failing example:**

```yaml
api_version:
```

## `META-003` — `preview_or_ga_status` is required and constrained

- **Description:** Every endpoint page must identify whether the page describes a preview or GA contract.
- **Severity:** error
- **Automated check feasibility:** fully automated by checking for `preview` or `ga`.
- **Passing example:**

```yaml
preview_or_ga_status: preview
```

- **Failing example:**

```yaml
preview_or_ga_status: public-preview-ish
```

## `META-004` — `example_validation_status` is required and constrained

- **Description:** Every endpoint page must declare the most recent example validation outcome as `passed`, `failed`, or `not-run`.
- **Severity:** error
- **Automated check feasibility:** fully automated by frontmatter parsing.
- **Passing example:**

```yaml
example_validation_status: passed
```

- **Failing example:**

```yaml
example_validation_status: green
```

## `META-005` — Metadata freshness windows must be respected

- **Description:** GA pages older than 90 days and preview pages older than 30 days must be flagged for reverification.
- **Severity:** warning
- **Automated check feasibility:** fully automated using the frontmatter date and status fields.
- **Passing example:**

```text
preview_or_ga_status: ga
last_verified_at: 2026-05-01
Current date: 2026-05-28
Result: within freshness window
```

- **Failing example:**

```text
preview_or_ga_status: preview
last_verified_at: 2026-03-10
Current date: 2026-05-28
Result: stale, revalidation required
```

## `DOC-PLACEHOLDER-001` — Internal placeholders must not leak into published examples

- **Description:** Published examples must not contain unresolved editorial markers such as `TODO`, `REPLACE_ME`, `<insert-id>`, or placeholder hostnames that were meant for authors rather than readers.
- **Severity:** warning
- **Automated check feasibility:** fully automated with regex-based detection and an allowlist for approved environment-variable placeholders.
- **Passing example:**

```bash
curl --request GET \
  --url "$AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/agents/$AGENT_ID?api-version=v1"
```

- **Failing example:**

```bash
curl --request GET \
  --url "https://REPLACE_ME.services.ai.azure.com/api/projects/TODO/agents/<insert-id>?api-version=v1"
```

## Enforcement notes

1. A PR fails when any **error** rule fails.
2. A PR can merge with **warning** findings only if the summary comment explains the exception and the reviewer approves it.
3. A nightly job should rerun the same rules against the full published API reference corpus to catch stale pages that were not touched in a PR.
4. The authoritative mapping between a page and an operation should be maintained in page metadata or generated from the page path to keep drift detection deterministic.
