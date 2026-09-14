# Create a message

Append a message to a thread.

## Request

`POST /agents/{agentId}/threads/{threadId}/messages`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the owning agent. |
| threadId | string | Required | Identifier of the thread that will receive the message. |

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
| role | string | Required | Message role, such as `user`. |
| content | array<object> | Required | Message content parts. |
| attachments | array<object> | Optional | File attachments or other message-scoped resources. |
| metadata | object | Optional | Application-defined metadata for the message. |

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads/thread_01JY50BR4X1SX6N54K9QGQKX7W/messages?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Content-Type: application/json"   -H "Accept: application/json"   -d '{
    "role": "user",
    "content": [
      {"type": "text", "text": "What is the baggage allowance for booking BK-4021?"}
    ],
    "metadata": {
      "channel": "web"
    }
  }'
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Message identifier. |
| object | string | Resource type. Value is `thread.message`. |
| thread_id | string | Identifier of the thread that owns the message. |
| role | string | Message role. |
| content | array<object> | Stored message content parts. |
| metadata | object | Metadata stored with the message. |
| created_at | string | UTC timestamp when the message was created. |

### Example response

```json
{
  "id": "msg_01JY52E4X45D52ZXQ9FSA4B6SZ",
  "object": "thread.message",
  "thread_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
  "role": "user",
  "content": [
    {"type": "text", "text": "What is the baggage allowance for booking BK-4021?"}
  ],
  "metadata": {
    "channel": "web"
  },
  "created_at": "2025-05-01T18:39:17Z"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | The message body is missing `role` or `content`, or a content part is malformed. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | thread_not_found | The specified agent or thread does not exist. |
| 409 | thread_locked | The thread cannot accept a new message while a conflicting operation is active. |
