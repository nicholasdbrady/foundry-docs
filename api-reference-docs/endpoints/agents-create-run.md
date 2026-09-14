# Create run

## 1. One-line purpose statement

**Purpose:** Start an agent run on an existing thread so the agent can process the accumulated messages.

## 2. When to use / when not to use

**Use this operation when:**
- You have an existing thread and want the agent to generate a reply or take actions.
- You want to pass per-run instructions without mutating the stored agent definition.
- You are orchestrating agent execution asynchronously and need a run identifier to poll later.

**Do not use this operation when:**
- Use `POST /agents/{agentId}/threads` when the conversation thread does not exist yet.
- Use `GET /agents/{agentId}/threads/{threadId}/runs/{runId}` when you need status for an existing run rather than starting a new one.
- Do not start a second run on the same thread if the previous run is still in progress unless your application explicitly supports that pattern.

## 3. Method + path + required auth/headers

**HTTP method:** `POST`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}/threads/{threadId}/runs`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to invoke the target agent and thread.

**Required headers:**
- `Content-Type: application/json`
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent that will execute the thread. |
| `threadId` | string | yes | The thread that supplies conversation context for the run. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |

### Request body fields

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `additional_instructions` | string | no | Per-run instructions appended to the stored agent instructions. |
| `metadata` | object | no | Run-scoped metadata such as correlation IDs or workflow stage. |
| `max_output_tokens` | integer | no | Upper bound on generated output tokens for this run. |
| `stream` | boolean | no | Set to `true` only when the create call should stream events instead of returning a buffered acknowledgement. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ/threads/thread_01JVQAP5R7YB2P5Z8T91A0EJYM/runs?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "additional_instructions": "Answer in two bullet points and mention the cancellation deadline.",
    "metadata": {
      "workflow_step": "case-summary"
    }
  }'
```

## 6. Minimal successful response example

```json
{
  "id": "run_01JVQB2MWY9C9SQSHY8Q31V2W4",
  "object": "thread.run",
  "agent_id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
  "thread_id": "thread_01JVQAP5R7YB2P5Z8T91A0EJYM",
  "status": "queued",
  "created_at": "2025-05-10T09:19:20Z",
  "metadata": {
    "workflow_step": "case-summary"
  }
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `400 Bad Request` | The body contains an invalid field or incompatible run option. | Remove unsupported fields and keep `stream` false unless the client is prepared for a streamed response. |
| `401 Unauthorized` | The request is not properly authenticated. | Use a fresh bearer token or valid project API key. |
| `404 Not Found` | The `agentId` or `threadId` does not exist in this project. | Verify both identifiers and confirm they belong to the same project. |
| `409 Conflict` | Another run is still active on the thread, or the thread is locked for execution. | Wait for the current run to complete or design the workflow to serialize runs per thread. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** None.
- **Behavior differences from GA:** If `stream` is enabled on the create call, the service can return a streamed event envelope instead of the buffered queued response shown here.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Most projects allow only one active run per thread at a time; output-token limits remain model-specific.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** Optional streamed responses are available when the client requests them.
- **Retries and idempotency notes:** If the network drops before you receive the run ID, inspect recent thread activity before submitting the same turn again.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` runtime operations](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching thread or run helper. |
| JavaScript | [`AgentsClient` runtime operations](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching thread or run helper. |
| C# | [`PersistentAgentsClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.agents.persistent-readme?view=azure-dotnet) — use the matching thread or run method. |
| Java | [`azure-ai-agents` runtime operations](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching thread or run method. |
