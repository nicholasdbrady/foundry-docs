# Get run

## 1. One-line purpose statement

**Purpose:** Retrieve the status and details for a run so a caller can detect completion, failure, or required action.

## 2. When to use / when not to use

**Use this operation when:**
- You need to poll for completion after creating a run asynchronously.
- You want usage numbers, timestamps, or last-error details for one run.
- You are resuming application workflow only after the run reaches a terminal state.

**Do not use this operation when:**
- Use `POST /agents/{agentId}/threads/{threadId}/runs` when you need to start execution instead of reading an existing run.
- Use the events stream endpoint when you need live incremental progress instead of polling.
- Do not call `GET /agents/{agentId}` when the problem is run state rather than stored agent configuration.

## 3. Method + path + required auth/headers

**HTTP method:** `GET`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}/threads/{threadId}/runs/{runId}`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to read the target thread run.

**Required headers:**
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent that owns the run. |
| `threadId` | string | yes | The thread that the run executed against. |
| `runId` | string | yes | The run identifier returned by the create-run operation. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |

None. This operation does not accept a request body.

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ/threads/thread_01JVQAP5R7YB2P5Z8T91A0EJYM/runs/run_01JVQB2MWY9C9SQSHY8Q31V2W4?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## 6. Minimal successful response example

```json
{
  "id": "run_01JVQB2MWY9C9SQSHY8Q31V2W4",
  "object": "thread.run",
  "agent_id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
  "thread_id": "thread_01JVQAP5R7YB2P5Z8T91A0EJYM",
  "status": "completed",
  "created_at": "2025-05-10T09:19:20Z",
  "started_at": "2025-05-10T09:19:21Z",
  "completed_at": "2025-05-10T09:19:24Z",
  "usage": {
    "input_tokens": 281,
    "output_tokens": 97
  },
  "last_error": null
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | Authentication is missing or invalid. | Send a fresh token or valid project API key. |
| `404 Not Found` | The `runId`, `threadId`, or `agentId` does not match a resource in this project. | Verify all three identifiers, especially if they came from different environments. |
| `409 Conflict` | The run has not reached a readable state because it is still being created or the thread is being compacted. | Retry after a short delay with exponential backoff. |
| `429 Too Many Requests` | The client is polling too aggressively. | Increase the poll interval and only poll active runs. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** None.
- **Behavior differences from GA:** Some tenants can expose additional hosted-run fields, but the terminal status contract shown here is stable.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Polling intervals of one to five seconds are typical; faster polling rarely improves completion latency.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** GET is safe to retry. Preserve the original identifiers and back off on `409` or `429` instead of hammering the endpoint.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` runtime operations](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching thread or run helper. |
| JavaScript | [`AgentsClient` runtime operations](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching thread or run helper. |
| C# | [`PersistentAgentsClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.agents.persistent-readme?view=azure-dotnet) — use the matching thread or run method. |
| Java | [`azure-ai-agents` runtime operations](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching thread or run method. |
