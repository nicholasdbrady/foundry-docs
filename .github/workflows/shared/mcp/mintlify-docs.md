---
mcp-servers:
  mintlify-docs:
    url: "https://mintlify.com/docs/mcp"
    allowed: ["*"]
---

# Mintlify Documentation MCP Server & Reference Files

This import provides three complementary resources for Mintlify MDX knowledge:

## 1. MCP Server (Interactive Search)

The `mintlify-docs` MCP server (configured above) provides interactive search access
to all Mintlify platform documentation. Use it for targeted queries about specific
components, configuration, or syntax.

## 2. llms.txt (Page Directory)

Mintlify hosts an `llms.txt` at the docs root that lists every documentation page
with descriptions — a directory of all available content. Fetch it with web-fetch
when you need to discover which pages exist:

```
web-fetch: https://mintlify.com/docs/llms.txt
```

A more comprehensive `llms-full.txt` combines all pages into a single file:

```
web-fetch: https://mintlify.com/docs/llms-full.txt
```

Use `llms.txt` for discovery (lightweight, structured links).
Use `llms-full.txt` when you need the complete reference in one pass (token-heavy).

## 3. skill.md (Capability Summary)

Mintlify hosts a `skill.md` at the docs root — a structured, machine-readable file
that tells agents what they can do with Mintlify and how to do it correctly:

```
web-fetch: https://mintlify.com/docs/skill.md
```

The skill.md includes:
- CLI commands (`mint dev`, `mint broken-links`, `mint validate`)
- Required file conventions and frontmatter schema
- Component decision table (when to use `<Accordion>` vs `<Tabs>` vs `<CodeGroup>`)
- Callout severity levels (`<Note>`, `<Info>`, `<Tip>`, `<Warning>`, `<Check>`)
- Writing standards and formatting rules
- Navigation configuration patterns
- API documentation setup

**Recommended workflow**: Fetch `skill.md` once at the start of your run for a
comprehensive reference. Use the MCP server for follow-up searches on specific topics.

## When to Use Each

| Resource | Best For | Token Cost |
|----------|----------|------------|
| MCP server search | Targeted queries about specific components | Low per query |
| `skill.md` | Comprehensive reference at start of run | Medium (one-time) |
| `llms.txt` | Discovering which pages exist | Low |
| `llms-full.txt` | Complete docs dump (last resort) | Very high |

## Critical MDX Rules

These are verified from the Mintlify docs — always double-check via MCP search if uncertain:

1. Use `{/* */}` for comments, NOT `<!-- -->`
2. Use `<br />` (self-closing), NOT `<br>`
3. Use `<CodeGroup>` for multi-language code examples, NOT `<Tabs>`
4. Components in list items must be de-indented to top level
5. Every page requires `title` in frontmatter; include `description` for SEO
6. Use root-relative paths without file extensions for internal links: `/getting-started/quickstart`
