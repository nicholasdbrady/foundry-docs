# Get agent

## 1. One-line purpose statement

**Purpose:** Retrieve a single agent by ID so a caller can inspect its configuration and current state.

## 2. When to use / when not to use

**Use this operation when:**
- You need the canonical configuration for one agent before a run or update.
- You want to confirm that an agent ID belongs to the current project.
- You are troubleshooting a runtime issue and need to inspect the stored instructions, tools, or metadata.

**Do not use this operation when:**
- Use `GET /agents` when you need discovery across many agents instead of one known identifier.
- Use `GET /agents/{agentId}/versions` when you need version history rather than the current resource.
- Use `GET /agents/{agentId}/threads/{threadId}/runs/{runId}` when you need runtime status instead of agent metadata.

## 3. Method + path + required auth/headers

**HTTP method:** `GET`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have read access to the project and to the target agent.

**Required headers:**
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent identifier returned when the agent was created. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01` for this operation. |

None. This operation does not accept a request body.

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## 6. Minimal successful response example

```json
{
  "id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
  "object": "agent",
  "name": "travel-agent",
  "description": "Answers travel planning questions.",
  "model": "gpt-4o-mini",
  "instructions": "Answer travel questions briefly and cite the booking policy when relevant.",
  "tools": [
    {
      "type": "file_search"
    }
  ],
  "metadata": {
    "owner": "support-automation",
    "environment": "prod"
  },
  "status": "ready",
  "created_at": "2025-05-09T14:22:11Z",
  "updated_at": "2025-05-09T14:22:11Z"
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | Authentication headers are missing or invalid. | Send a fresh bearer token or valid API key for the same project endpoint. |
| `404 Not Found` | The `agentId` does not exist in the current project or region. | Verify the project name, region, and agent identifier. |
| `403 Forbidden` | The caller can reach the project but does not have permission to read this agent. | Grant the project reader role or use an authorized service principal. |
| `400 Bad Request` | The path or query string is malformed, such as an empty `agentId` or unsupported API version. | Correct the URL format and keep `api-version=2025-05-01`. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** None for prompt-agent reads. Hosted-agent details can vary by cloud.
- **Behavior differences from GA:** Hosted container details can surface extra fields when the project is opted in to hosted-agent preview features.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** No page-size or payload expansion options are required for a single read.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** GET is safe to retry. If repeated reads return `404`, confirm the resource was not deleted or moved across projects.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` in `azure-ai-agents`](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching administration method. |
| JavaScript | [`AgentsClient` in `@azure/ai-agents`](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching administration method. |
| C# | [`AIProjectClient.AgentAdministrationClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.projects-readme?view=azure-dotnet) — use the matching agent administration method. |
| Java | [`azure-ai-agents`](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching administration method. |
