# Create a thread

Create a conversation thread for an agent.

## Request

`POST /agents/{agentId}/threads`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the agent that will own the thread. |

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
| messages | array<object> | Optional | Initial messages to seed the thread. |
| metadata | object | Optional | Application-defined key-value metadata for the thread. |
| tool_resources | object | Optional | Thread-scoped tool resources, such as vector store bindings. |

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Content-Type: application/json"   -H "Accept: application/json"   -d '{
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "Summarize the current itinerary for booking BK-4021."}
        ]
      }
    ],
    "metadata": {
      "booking_id": "BK-4021",
      "channel": "web"
    }
  }'
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
| 400 | invalid_request | The initial message list or metadata object is malformed. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | agent_not_found | The specified agent does not exist in the project. |
| 429 | rate_limit_exceeded | The project is receiving too many thread creation requests. |
