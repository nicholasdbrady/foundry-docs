# docs-vnext: Art-of-the-Possible Documentation

This directory is an **experimental, agent-maintained** copy of the canonical `docs/` directory. It demonstrates how GitHub Agentic Workflows (gh-aw) can autonomously maintain, improve, and validate documentation.

## Purpose

- **Stakeholder demo**: Show Microsoft stakeholders what agentic doc maintenance looks like in practice
- **Before/after comparison**: Compare `docs/` (canonical upstream) with `docs-vnext/` (agent-improved)
- **Safe experimentation**: Agentic workflows write to `docs-vnext/` only — never to `docs/`

## How It Works

1. `docs-vnext/` is periodically seeded from `docs/` as a baseline
2. Agentic workflows layer improvements on top:
   - **Daily Doc Updater** — updates docs based on recent code changes
   - **Daily Doc Healer** — finds gaps the updater missed
   - **Documentation Unbloat** — reduces verbosity while preserving clarity
   - **Glossary Maintainer** — keeps a glossary synchronized with the codebase
   - **Noob Tester** — tests docs from a beginner's perspective
   - **Multi-device Tester** — validates responsive layout across devices
   - **Docs Auditor** — validates accuracy and link integrity
   - **Slide Deck Maintainer** — keeps stakeholder presentations current
3. A weekly diff report summarizes what agents changed

## Relationship to `docs/`

- `docs/` = production, synced daily from MicrosoftDocs/azure-ai-docs-pr
- `docs-vnext/` = experimental, agent-improved fork
- Changes proven valuable in `docs-vnext/` can be upstreamed to azure-ai-docs-pr

## Viewing

To preview locally:

```bash
cd docs-vnext
npx mintlify dev --port 3333
```
