# List agents

## 1. One-line purpose statement

**Purpose:** Return the agents in a Foundry project so a caller can discover, filter, and page through them.

## 2. When to use / when not to use

**Use this operation when:**
- You need to show available agents in an admin or picker experience.
- You are validating whether an agent already exists before creating a new one.
- You want a paged inventory of project agents for audit or automation workflows.

**Do not use this operation when:**
- Use `GET /agents/{agentId}` when you already know the identifier for the agent you need.
- Use `GET /agents/{agentId}/versions` when you need version history for one agent rather than the project catalog.
- Use `POST /agents` when you need to provision a new resource instead of enumerating existing ones.

## 3. Method + path + required auth/headers

**HTTP method:** `GET`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to list agents in the project.

**Required headers:**
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |
| `top` | integer | no | Optional page size. Omit it to use the service default. |
| `continuationToken` | string | no | Opaque cursor from a previous page when more results are available. |

None. This operation does not accept a request body.

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01&top=2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## 6. Minimal successful response example

```json
{
  "data": [
    {
      "id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
      "object": "agent",
      "name": "travel-agent",
      "model": "gpt-4o-mini",
      "status": "ready",
      "created_at": "2025-05-09T14:22:11Z"
    },
    {
      "id": "agt_01JVQ6PKP3W6MNBX1D5B84ES3Y",
      "object": "agent",
      "name": "refund-agent",
      "model": "gpt-4.1-mini",
      "status": "ready",
      "created_at": "2025-05-09T09:03:44Z"
    }
  ],
  "has_more": true,
  "next_link": "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01&continuationToken=eyJza2lwVG9rZW4iOiIyIn0"
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | The request is unauthenticated or uses a token for the wrong audience. | Use a valid bearer token for `https://ai.azure.com/.default` or a valid project API key. |
| `400 Bad Request` | The `top` value is invalid or the continuation token is malformed. | Use a positive integer for `top` and pass the continuation token exactly as returned. |
| `403 Forbidden` | The caller lacks permission to enumerate project agents. | Grant project reader or higher access. |
| `429 Too Many Requests` | The caller is scanning the collection too quickly or in too many concurrent workers. | Apply exponential backoff and reuse continuation tokens instead of restarting from the first page. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** None.
- **Behavior differences from GA:** Projects opted into hosted-agent preview can return extra hosted-specific fields on each list item.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Page size is service-limited; use moderate `top` values for inventory jobs to reduce response size.
- **Pagination:** Uses `top` and `continuationToken`.
- **Ordering:** Results are typically returned in descending creation order unless the service introduces a different default.
- **Streaming:** None.
- **Retries and idempotency notes:** GET is safe to retry. If a page fails after a continuation token is issued, retry with the same token instead of restarting the scan.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` in `azure-ai-agents`](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching administration method. |
| JavaScript | [`AgentsClient` in `@azure/ai-agents`](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching administration method. |
| C# | [`AIProjectClient.AgentAdministrationClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.projects-readme?view=azure-dotnet) — use the matching agent administration method. |
| Java | [`azure-ai-agents`](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching administration method. |
