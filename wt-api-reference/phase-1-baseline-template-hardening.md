# Phase 1 — Baseline + Template Hardening (Weeks 1-3)

## Objective

Create a consistent endpoint-page standard that makes each API operation understandable and runnable in under 2 minutes.

## Workstreams

### 1) Define the canonical endpoint template

Every endpoint page must include, in this order:

1. One-line purpose statement
2. When to use / when not to use
3. Method + path + required auth/headers
4. Required query parameters and path parameters
5. Minimal request example (copy-run-edit)
6. Minimal successful response example
7. Common error responses with likely causes and fixes
8. Preview/feature-flag notes (if applicable)
9. Limits, pagination, and streaming behavior notes
10. SDK parity links (Py/JS/C#/Java)

### 2) Top endpoint baseline audit

Audit top 20% traffic endpoints (starting with Agents, Responses, Evals):

- Missing required field documentation
- Missing or inconsistent feature flag guidance
- Non-runnable examples
- Terminology inconsistencies
- Oversized schema blocks before practical examples

### 3) Quick-win rewrites

Apply template to first 15 high-impact operations:

- 10 in Agents (CRUD, session, version, log stream)
- 3 in Responses/Evals
- 2 in Connections/Deployments

## Deliverables

- `endpoint-template-v1.md`
- `phase1-endpoint-audit.csv`
- Rewritten pages for first 15 target operations

## Exit criteria

- 100% of pilot endpoints follow template sections in order
- Each pilot endpoint has at least one runnable cURL example
- Preview headers documented where required
- Error section includes at least 3 actionable failure patterns for each pilot endpoint

## Risks and mitigations

- Risk: docs generated from spec overwrite manual improvements.
  - Mitigation: encode template changes upstream in generation pipeline metadata.
- Risk: schema complexity bloats pages.
  - Mitigation: collapse advanced schema and keep “minimal payload first.”
