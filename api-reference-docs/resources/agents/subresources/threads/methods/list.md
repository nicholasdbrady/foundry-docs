# List threads

List threads that belong to an agent.

## Request

`GET /agents/{agentId}/threads`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the agent whose threads should be listed. |

### Query parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api-version | string | Required | API version. Use `2025-05-01`. |
| limit | integer | Optional | Maximum number of threads to return. |
| after | string | Optional | Cursor for the next page of results. |
| order | string | Optional | Sort direction for `created_at`. Use `asc` or `desc`. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads?api-version=2025-05-01&limit=2"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| object | string | Collection type. Value is `list`. |
| data | array<object> | Threads returned for the current page. |
| first_id | string | Identifier of the first item in `data`. |
| last_id | string | Identifier of the last item in `data`. |
| has_more | boolean | Indicates whether another page is available. |

### Example response

```json
{
  "object": "list",
  "data": [
    {
      "id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
      "object": "thread",
      "agent_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
      "created_at": "2025-05-01T18:30:09Z"
    },
    {
      "id": "thread_01JY50E8M5D0X7TTT21XJMG1YM",
      "object": "thread",
      "agent_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
      "created_at": "2025-05-01T18:15:54Z"
    }
  ],
  "first_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
  "last_id": "thread_01JY50E8M5D0X7TTT21XJMG1YM",
  "has_more": false
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | The paging or sorting parameters are malformed. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | agent_not_found | The specified agent does not exist in the project. |
| 429 | rate_limit_exceeded | The project is receiving too many thread list requests. |
