---
description: Documentation guidelines for foundry-docs project
applyTo: "docs-vnext/**/*.mdx,docs-vnext/**/*.md"
---

# Documentation Guidelines for foundry-docs

## Overview

This project serves Microsoft Foundry documentation via a FastMCP MCP server. Documentation is authored in **Mintlify MDX format** and organized by topic area.

## File Format

- All documentation files use `.mdx` extension (Mintlify MDX)
- Frontmatter uses YAML between `---` markers
- Required frontmatter fields: `title`, `description`

### Frontmatter Example

```yaml
---
title: "Getting Started with Foundry"
description: "Learn how to set up and use Microsoft Foundry for AI projects"
---
```

## Mintlify MDX Syntax

### Callouts

Use Mintlify callout components (NOT GitHub-flavored alerts):

```mdx
<Note>
Important information the reader should notice.
</Note>

<Tip>
Helpful advice for the reader.
</Tip>

<Warning>
Warning about potential issues or pitfalls.
</Warning>

<Info>
Additional context or background information.
</Info>
```

**Do NOT use** `> [!NOTE]` or `> [!WARNING]` GitHub alert syntax.

### Comments

Use JSX comments in MDX files:

```mdx
{/* This is a comment in MDX */}
```

**Do NOT use** `<!-- HTML comments -->` in MDX files.

### Code Blocks

Use fenced code blocks with language tags:

```python
from azure.ai.projects import AIProjectClient
client = AIProjectClient(endpoint="...", credential=credential)
```

For multi-language examples, use Mintlify CodeGroup:

```mdx
<CodeGroup>
```python Python
client = AIProjectClient(endpoint=endpoint, credential=credential)
```

```typescript TypeScript
const client = new AIProjectClient(endpoint, credential);
```
</CodeGroup>
```

### Self-Closing Tags

Always use self-closing tags for void elements:

- ✅ `<br />`
- ❌ `<br>`

### Components in List Items

Mintlify components inside list items must be de-indented to the top level (not nested inside the list markup).

## Diátaxis Framework

Documentation must be organized into four types:

### 1. Tutorials (Learning-Oriented)
- Guide beginners through a specific outcome
- Step-by-step, concrete examples
- Assume minimal prior knowledge
- Imperative mood: "Create a file", "Run the command"

### 2. How-to Guides (Goal-Oriented)
- Solve a specific real-world problem
- Title format: "How to [accomplish specific goal]"
- Assume the user knows basics
- Imperative mood: "Configure the setting"

### 3. Reference (Information-Oriented)
- Accurate, complete technical descriptions
- Organized by structure (APIs, CLI, config)
- Consistent format, all parameters included
- Descriptive mood: "The function accepts..."

### 4. Explanation (Understanding-Oriented)
- Clarify topics, deepen understanding
- Discuss design decisions and tradeoffs
- Connect concepts together
- Indicative mood: "This approach provides..."

## Style Guidelines

- **Tone**: Neutral, technical, not promotional
- **Voice**: Avoid "we", "our" — use "the tool", "this command"
- **Headings**: Use markdown heading syntax, not bold text as headings
- **Lists**: Avoid excessively long bullet lists; prefer prose with structure
- **Code samples**: Minimal, focused, copy-paste ready
- **Placeholders**: Use ALL_CAPS (e.g., `YOUR_ENDPOINT`, `YOUR_API_KEY`)

## Project Structure

```
docs-vnext/
├── docs.json          # Mintlify navigation config
├── agents/            # Agent development docs
│   ├── development/   # Core agent concepts
│   └── tools/         # Agent tools & integration
├── models/            # Model capabilities & fine-tuning
│   ├── capabilities/
│   ├── catalog/
│   └── fine-tuning/
├── setup/             # Setup & configuration
├── security/          # Security & governance
├── observability/     # Evaluation & tracing
├── api-sdk/           # API & SDK reference
├── developer-experience/
├── manage/            # Agent/model management
├── operate/           # Operations & support
├── best-practices/
├── responsible-ai/
├── guardrails/
├── overview/
└── reference/         # Reference docs (glossary, etc.)
```

## Content to Avoid

- "Key Features" marketing sections
- Promotional language or selling points
- Excessive bullet points (prefer structured prose)
- Mixing documentation types (tutorials that become reference)
- Duplicate content across sections
