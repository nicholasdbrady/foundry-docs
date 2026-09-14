# Phase 3 — Accuracy Automation + Drift Prevention (Weeks 8-10)

## Objective

Shift from manual correctness checks to automated verification so docs remain accurate as APIs evolve.

## Workstreams

### 1) Example quality gates in CI

Automated checks for every published endpoint page:

- Missing required params in examples
- Invalid enum values in examples
- Missing required headers (auth, preview flags)
- URL/path/query mismatch with current OpenAPI spec
- JSON schema shape mismatch in request/response payloads

### 2) Spec-to-doc drift detection

On every spec change:

- Detect changed operation IDs, parameters, or response shapes
- Flag impacted docs pages
- Open/update tracked work items for docs owners

### 3) Runtime validation (where safe)

For a curated smoke-test set:

- Execute sample requests against test environment
- Verify expected status codes and core response fields
- Persist snapshots to detect regressions

### 4) Metadata for trust

Add page metadata fields:

- last_verified_at
- api_version
- preview_or_ga_status
- example_validation_status

## Deliverables

- `docs-validation-rules.md`
- CI workflow for docs/example validation
- `phase3-smoke-test-endpoints.yaml`
- dashboard/report for doc accuracy status

## Exit criteria

- 100% example validation pass rate for in-scope endpoints
- Drift alerts generated for all relevant spec changes
- No stale “last verified” date older than 30 days for tier-1 endpoints

## Risks and mitigations

- Risk: false positives block publishing.
  - Mitigation: baseline mode with gradual strictness ramp.
- Risk: test environment instability causes noisy failures.
  - Mitigation: separate flaky runtime checks from schema checks.
