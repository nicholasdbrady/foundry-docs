# Create thread

## 1. One-line purpose statement

**Purpose:** Create a thread under an agent so messages and runs can share conversation state.

## 2. When to use / when not to use

**Use this operation when:**
- You need a new conversation container before starting the first run.
- You want to persist context across multiple user turns for the same agent.
- You are seeding a thread with one or more initial messages before execution begins.

**Do not use this operation when:**
- Use `POST /agents/{agentId}/threads/{threadId}/runs` when the thread already exists and you want execution.
- Use `POST /responses` when you need a one-off model call without thread state.
- Do not create a new thread for every turn if you need the agent to preserve prior context.

## 3. Method + path + required auth/headers

**HTTP method:** `POST`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}/threads`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to invoke the target agent.

**Required headers:**
- `Content-Type: application/json`
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent that will own the thread. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |

### Request body fields

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `messages` | array<object> | no | Optional initial message list. Each item normally includes `role` and `content`. |
| `metadata` | object | no | Application-defined thread metadata such as tenant, case, or session identifiers. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ/threads?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Summarize the latest travel request for case CS-1042."
      }
    ],
    "metadata": {
      "case_id": "CS-1042"
    }
  }'
```

## 6. Minimal successful response example

```json
{
  "id": "thread_01JVQAP5R7YB2P5Z8T91A0EJYM",
  "object": "thread",
  "agent_id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
  "created_at": "2025-05-10T09:18:42Z",
  "messages_count": 1,
  "metadata": {
    "case_id": "CS-1042"
  }
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `400 Bad Request` | One of the seeded messages is malformed or the metadata shape is invalid. | Make sure each message includes a valid `role` and string `content`, and keep metadata values JSON-serializable. |
| `401 Unauthorized` | The request is missing valid authentication. | Send a fresh token or valid project API key. |
| `404 Not Found` | The `agentId` does not exist in the target project. | Verify the agent ID and project endpoint. |
| `429 Too Many Requests` | Too many threads are being created concurrently for the same project or agent. | Apply backoff and pool thread creation instead of stampeding the service. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** None.
- **Behavior differences from GA:** Some hosted-agent tenants can surface extra thread metadata fields, but prompt-agent thread creation is stable.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Keep the seeded message list minimal; large thread histories are better added incrementally after creation.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** If a timeout occurs after submission, search for the thread in your application metadata before creating a second one.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` runtime operations](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching thread or run helper. |
| JavaScript | [`AgentsClient` runtime operations](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching thread or run helper. |
| C# | [`PersistentAgentsClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.agents.persistent-readme?view=azure-dotnet) — use the matching thread or run method. |
| Java | [`azure-ai-agents` runtime operations](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching thread or run method. |
