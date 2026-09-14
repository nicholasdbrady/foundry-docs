# Microsoft Foundry API Reference DX Improvement Program

This folder is a holding area for improving the external `ai.azure.com/api-reference` experience.

## Scope

Raise Microsoft Foundry API reference quality to industry-leading standards on:

- Developer experience (time-to-first-success)
- Conciseness (lower cognitive load)
- Technical accuracy (examples and schemas that match behavior)

## Program timeline

- Phase 1: Baseline + template hardening (`phase-1-baseline-template-hardening.md`)
- Phase 2: Task-first IA + concision (`phase-2-task-ia-and-concision.md`)
- Phase 3: Accuracy automation + drift prevention (`phase-3-accuracy-automation.md`)
- Phase 4: Production polish + industry leadership (`phase-4-production-polish.md`)

## Shared success metrics

1. Time-to-first-successful-call: **< 10 minutes**
2. Example validity pass rate: **100%** in CI gates
3. Docs task success rate (usability): **> 85%**
4. Support incidents attributable to API docs ambiguity: **-40%** quarter-over-quarter
5. Search-to-success conversion on docs: **+25%**

## Current-state observations driving this plan

- Endpoint breadth is strong but navigation is mostly object-centric.
- Preview feature flags and headers are present but easy to miss.
- Some examples are placeholder-heavy and not copy-run-edit friendly.
- Error handling sections are often too generic for troubleshooting.
- SDK parity is linked but not consistently mapped per operation.

## Ownership model

- Documentation lead: template, style, IA
- API engineering: OpenAPI/source-of-truth quality
- SDK owners: parity tables and samples
- DevRel/support: top-task prioritization from real incidents
- CI/docs tooling owner: quality gates and drift checks
