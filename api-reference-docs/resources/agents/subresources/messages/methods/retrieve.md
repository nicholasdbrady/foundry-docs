# Retrieve a message

Return a message from a thread by ID.

## Request

`GET /agents/{agentId}/threads/{threadId}/messages/{messageId}`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the owning agent. |
| threadId | string | Required | Identifier of the thread that owns the message. |
| messageId | string | Required | Identifier of the message to retrieve. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads/thread_01JY50BR4X1SX6N54K9QGQKX7W/messages/msg_01JY52E4X45D52ZXQ9FSA4B6SZ?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: application/json"
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
| status | string | Message status when applicable. |
| created_at | string | UTC timestamp when the message was created. |

### Example response

```json
{
  "id": "msg_01JY52E4X45D52ZXQ9FSA4B6SZ",
  "object": "thread.message",
  "thread_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
  "role": "assistant",
  "content": [
    {"type": "text", "text": "Booking BK-4021 includes one checked bag up to 23 kilograms and one cabin bag."}
  ],
  "status": "completed",
  "created_at": "2025-05-01T18:39:20Z"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 401 | unauthorized | Authentication failed or was not provided. |
| 403 | forbidden | The caller does not have access to this message. |
| 404 | message_not_found | The specified message does not exist for the thread. |
| 409 | agent_thread_message_mismatch | The message does not belong to the specified agent and thread combination. |
