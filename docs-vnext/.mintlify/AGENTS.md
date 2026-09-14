# Documentation Agent Instructions

## File format

- All documentation files use `.mdx` extension (Mintlify MDX format).
- Every page must start with YAML frontmatter between `---` markers.
- Required frontmatter fields: `title` and `description`.
- `description` should be 50–160 characters, plain language, summarizing the page.

```yaml
---
title: "Clear, specific, keyword-rich title"
description: "Concise description explaining the page purpose and value"
---
```

## MDX syntax rules

### Callouts

Use Mintlify callout components. **Never** use GitHub-flavored alert syntax (`> [!NOTE]`).

```mdx
<Note>Important information the reader should notice.</Note>
<Tip>Helpful advice for the reader.</Tip>
<Warning>Warning about potential issues or pitfalls.</Warning>
<Info>Additional context or background information.</Info>
```

### Comments

Use JSX comments: `{/* This is a comment */}`. **Never** use HTML comments (`<!-- -->`).

### Self-closing tags

Always use self-closing tags for void elements: `<br />` not `<br>`.

### Code blocks

Use fenced code blocks with language tags. For multi-language examples, use `<CodeGroup>`:

````mdx
<CodeGroup>
```python Python
client = AIProjectClient(endpoint=endpoint, credential=credential)
```

```typescript TypeScript
const client = new AIProjectClient(endpoint, credential);
```
</CodeGroup>
````

### Components in list items

Mintlify components inside list items must be de-indented to the top level, not nested inside the list markup.

## Content standards

### Diátaxis framework

Organize content into four types:

1. **Tutorials** (learning-oriented): Step-by-step, concrete examples, assume minimal prior knowledge. Imperative mood.
2. **How-to guides** (goal-oriented): Solve a specific problem. Title format: "How to [accomplish goal]". Imperative mood.
3. **Reference** (information-oriented): Accurate, complete technical descriptions. Consistent format. Descriptive mood.
4. **Explanation** (understanding-oriented): Clarify topics, discuss design decisions. Indicative mood.

Do not mix documentation types in a single page.

### Style

- **Tone**: Neutral, technical, not promotional.
- **Voice**: Avoid "we", "our". Use "the tool", "this command", "Foundry".
- **Person**: Use "you" for instructions.
- **Headings**: Use markdown heading syntax (`##`), not bold text as headings.
- **Lists**: Avoid excessively long bullet lists; prefer prose with structure.
- **Code samples**: Minimal, focused, copy-paste ready.
- **Placeholders**: Use ALL_CAPS (e.g., `YOUR_ENDPOINT`, `YOUR_API_KEY`, `YOUR_MODEL_DEPLOYMENT`).

### Code example standards

- Include examples in Python, C#, and TypeScript where applicable.
- Always include import statements.
- Use realistic parameter values, not `foo`/`bar`.
- Include error handling for production-facing examples.
- Show the `DefaultAzureCredential` pattern for authentication.
- Show environment variable patterns: `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL_DEPLOYMENT_NAME`.

### Terminology

| Use this | Not this |
|---|---|
| Foundry resource | AI hub, workspace |
| Agent | Bot, chatbot |
| Project endpoint | API key (for primary endpoint) |
| Foundry (new) | New portal |
| Foundry (classic) | Old portal |
| Model deployment | Model instance |

## What to avoid

- "Key Features" marketing sections
- Promotional language or selling points
- Excessive bullet points (prefer structured prose)
- Mixing documentation types (tutorials that become reference)
- Duplicate content across sections
- HTML comments (`<!-- -->`) — use `{/* */}` instead
- GitHub-flavored alerts — use Mintlify callout components instead
