# Phase 2 — Task-first IA + Concision (Weeks 4-7)

## Objective

Layer task-oriented navigation over object-oriented reference pages so developers can complete workflows quickly without deep taxonomy knowledge.

## Workstreams

### 1) Introduce task-first entry pages

Create task pages that route to exact endpoint docs:

1. Create and run a hosted agent
2. Update and version an agent safely
3. Stream and troubleshoot session logs (SSE)
4. Create datasets and run evaluations
5. Manage deployments and model routing

Each task page should contain:

- Prerequisites
- 5-10 minute happy path
- Common failure branches
- Links to exact endpoint reference pages
- SDK and REST side-by-side snippets

### 2) Sidebar information architecture improvements

- Keep resource groups in sidebar, but add “Top tasks” group at the top.
- Normalize naming and casing (e.g., humanized labels for generated resource names).
- Ensure operation labels are concise verb-first phrases.

### 3) Concision pass

For pilot pages:

- Move giant schema dumps below the practical examples
- Replace repeated prose with reusable callout components
- Add short glossary for Foundry-specific terms at page or section level

## Deliverables

- `task-map-v1.md` (task -> endpoint mapping)
- 8-12 task-first guide pages
- Updated sidebar proposal with naming conventions

## Exit criteria

- New users can complete 3 core workflows from task pages without searching docs externally
- Median clicks from landing page to first successful endpoint <= 4
- No critical flow requires reading more than 2 reference pages before first successful request

## Risks and mitigations

- Risk: duplicate content drift between task guides and endpoint refs.
  - Mitigation: centralize shared snippets and include “single source” links.
- Risk: IA changes break existing bookmarks.
  - Mitigation: preserve canonical URLs and add redirects/aliases.
