# Report Generation

Consult this file when creating an agentic workflow that generates reports — recurring status updates, audits, analysis summaries, or any structured output posted as a GitHub issue, discussion, or comment.

## Choosing the Right Output Type

| Use case | Recommended output |
|---|---|
| Report (default) | `create-issue` with `close-older-issues` |
| Inline update on an existing issue or PR | `add-comment` with `hide-older-comments` |
| Discussion-based report (only when explicitly requested) | `create-discussion` with `close-older-discussions` |

Use `create-issue` by default for reports — issues are familiar, searchable, and support the full close/expire cleanup mechanism.

## Automatic Cleanup

Reports accumulate over time. Always configure automatic cleanup when the workflow runs on a schedule.

- **`expires`**: Auto-closes the issue after a time period (e.g. `7` days, `2w`, `1m`).
- **`close-older-issues: true`**: Closes previous issues from the same workflow before creating a new one.
- **`hide-older-comments: true`**: Minimizes previous comments before posting new ones.

## Report Style and Structure

### Header Levels

**Use `###` or lower for all headers in reports** to maintain proper document hierarchy.

### Progressive Disclosure

Wrap detailed content in `<details><summary><b>Section Name</b></summary>` tags.

Use collapsible sections for:
- Verbose details (full logs, raw data)
- Secondary information
- Per-item breakdowns with many items

Always keep critical information visible (summary, critical issues, key metrics).

### Report Structure Pattern

1. **Overview**: 1–2 paragraphs summarizing key findings
2. **Critical Information**: Summary stats, critical issues (always visible)
3. **Details**: Use `<details>` for expanded content
4. **Context**: Helpful metadata (workflow run, date, trigger)

## Workflow Run References

- Format run IDs as links: `[§12345](https://github.com/owner/repo/actions/runs/12345)`
- Do NOT add footer attribution — the system appends it automatically

## Avoiding Mentions and Backlinks

Use safe-outputs filtering to suppress notifications:

```yaml
safe-outputs:
  mentions: false
  allowed-github-references: []
  max-bot-mentions: 0
```
