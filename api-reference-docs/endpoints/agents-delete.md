# Delete agent

## 1. One-line purpose statement

**Purpose:** Delete an agent so it can no longer be used for new thread runs.

## 2. When to use / when not to use

**Use this operation when:**
- You are cleaning up an unused or superseded agent.
- You need to remove an agent before rotating to a new one with a different lifecycle.
- You want to enforce project hygiene by deleting stale test resources.

**Do not use this operation when:**
- Use `PATCH /agents/{agentId}` when you need to disable or modify behavior without deleting the resource.
- Use `GET /agents/{agentId}` when you only need to inspect configuration or runtime state.
- Do not delete an agent that still has active callers unless you have already switched them to another agent ID.

## 3. Method + path + required auth/headers

**HTTP method:** `DELETE`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to delete project agents.

**Required headers:**
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent identifier to delete. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |

None. This operation does not accept a request body.

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X DELETE "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## 6. Minimal successful response example

```json
{
  "id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
  "object": "agent.deleted",
  "deleted": true
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | Authentication headers are missing or invalid. | Send a fresh bearer token or valid API key. |
| `404 Not Found` | The target `agentId` does not exist in this project. | Confirm the project endpoint and agent identifier before deleting. |
| `409 Conflict` | The agent still has active runs, threads, or a dependent hosted runtime. | Wait for active work to finish or decommission dependents before retrying the delete. |
| `403 Forbidden` | The caller can read the project but does not have delete permissions. | Use a principal with project manager or equivalent delete rights. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** Hosted-agent cleanup timing can vary by cloud.
- **Behavior differences from GA:** Deleting a hosted or container-backed agent can trigger asynchronous cleanup of version artifacts beyond the initial delete acknowledgement.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Deletion can take longer when the agent has large tool resources or dependent hosted runtimes.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** Do not blindly retry deletes after a network timeout. First read the resource or list agents to confirm whether the deletion already succeeded.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` in `azure-ai-agents`](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching administration method. |
| JavaScript | [`AgentsClient` in `@azure/ai-agents`](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching administration method. |
| C# | [`AIProjectClient.AgentAdministrationClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.projects-readme?view=azure-dotnet) — use the matching agent administration method. |
| Java | [`azure-ai-agents`](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching administration method. |
