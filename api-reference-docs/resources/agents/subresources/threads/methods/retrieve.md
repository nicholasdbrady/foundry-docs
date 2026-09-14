# Retrieve a thread

Return a thread by ID.

## Request

`GET /agents/{agentId}/threads/{threadId}`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the owning agent. |
| threadId | string | Required | Identifier of the thread to retrieve. |

### Query parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api-version | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Authorization | string | Conditional | Bearer token in the form `Bearer YOUR_ACCESS_TOKEN`. Required unless `api-key` is provided. |
| api-key | string | Conditional | Project API key. Required unless `Authorization` is provided. |
| Accept | string | Optional | Response format. Use `application/json`. |

### Request body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| None | - | - | This operation does not accept a request body. |

### Example request

```bash
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads/thread_01JY50BR4X1SX6N54K9QGQKX7W?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Thread identifier. |
| object | string | Resource type. Value is `thread`. |
| agent_id | string | Identifier of the owning agent. |
| metadata | object | Metadata stored with the thread. |
| created_at | string | UTC timestamp when the thread was created. |
| tool_resources | object | Thread-scoped tool resources. |

### Example response

```json
{
  "id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
  "object": "thread",
  "agent_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "metadata": {
    "booking_id": "BK-4021",
    "channel": "web"
  },
  "created_at": "2025-05-01T18:30:09Z",
  "tool_resources": {}
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 401 | unauthorized | Authentication failed or was not provided. |
| 403 | forbidden | The caller does not have access to this thread. |
| 404 | thread_not_found | The specified thread does not exist for the agent. |
| 409 | agent_thread_mismatch | The thread does not belong to the specified agent. |
