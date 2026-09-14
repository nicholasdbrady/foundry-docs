# Create a run

Start agent execution for a thread.

## Request

`POST /agents/{agentId}/threads/{threadId}/runs`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the agent that will execute the run. |
| threadId | string | Required | Identifier of the thread that provides conversation state. |

### Query parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api-version | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Authorization | string | Conditional | Bearer token in the form `Bearer YOUR_ACCESS_TOKEN`. Required unless `api-key` is provided. |
| api-key | string | Conditional | Project API key. Required unless `Authorization` is provided. |
| Content-Type | string | Required | Content type. Use `application/json`. |
| Accept | string | Optional | Response format. Use `application/json`. |

### Request body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| additional_instructions | string | Optional | Run-scoped instructions appended to the stored agent instructions. |
| metadata | object | Optional | Application-defined key-value metadata for the run. |
| max_output_tokens | integer | Optional | Upper bound for generated output tokens. |
| temperature | number | Optional | Sampling temperature override for the run. |
| stream | boolean | Optional | If `true`, the create call can return a streamed response instead of a buffered acknowledgement. |

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads/thread_01JY50BR4X1SX6N54K9QGQKX7W/runs?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Content-Type: application/json"   -H "Accept: application/json"   -d '{
    "additional_instructions": "Reply with a short itinerary summary and include the change deadline.",
    "metadata": {
      "request_id": "req_4821",
      "workflow_step": "summarize"
    },
    "max_output_tokens": 300
  }'
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Run identifier. |
| object | string | Resource type. Value is `thread.run`. |
| agent_id | string | Identifier of the agent that is executing the run. |
| thread_id | string | Identifier of the thread associated with the run. |
| status | string | Current run status. |
| metadata | object | Metadata stored with the run. |
| created_at | string | UTC timestamp when the run was created. |

### Example response

```json
{
  "id": "run_01JY51J5SABRHNBR4Q7T5M4N3T",
  "object": "thread.run",
  "agent_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "thread_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
  "status": "queued",
  "metadata": {
    "request_id": "req_4821",
    "workflow_step": "summarize"
  },
  "created_at": "2025-05-01T18:34:55Z"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | The request body contains unsupported or malformed fields. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | thread_not_found | The specified agent or thread does not exist. |
| 409 | run_conflict | The thread already has an active run or cannot accept a new run. |
