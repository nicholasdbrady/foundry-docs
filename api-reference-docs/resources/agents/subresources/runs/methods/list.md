# List runs

List runs created for a thread.

## Request

`GET /agents/{agentId}/threads/{threadId}/runs`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the owning agent. |
| threadId | string | Required | Identifier of the thread whose runs should be listed. |

### Query parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api-version | string | Required | API version. Use `2025-05-01`. |
| limit | integer | Optional | Maximum number of runs to return. |
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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads/thread_01JY50BR4X1SX6N54K9QGQKX7W/runs?api-version=2025-05-01&limit=2"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| object | string | Collection type. Value is `list`. |
| data | array<object> | Runs returned for the current page. |
| first_id | string | Identifier of the first item in `data`. |
| last_id | string | Identifier of the last item in `data`. |
| has_more | boolean | Indicates whether another page is available. |

### Example response

```json
{
  "object": "list",
  "data": [
    {
      "id": "run_01JY51J5SABRHNBR4Q7T5M4N3T",
      "object": "thread.run",
      "status": "completed",
      "thread_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
      "created_at": "2025-05-01T18:34:55Z"
    },
    {
      "id": "run_01JY5196W7C4J0Y99S0M3NR7K0",
      "object": "thread.run",
      "status": "failed",
      "thread_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
      "created_at": "2025-05-01T17:49:21Z"
    }
  ],
  "first_id": "run_01JY51J5SABRHNBR4Q7T5M4N3T",
  "last_id": "run_01JY5196W7C4J0Y99S0M3NR7K0",
  "has_more": false
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | The paging or sorting parameters are malformed. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | thread_not_found | The specified agent or thread does not exist. |
| 429 | rate_limit_exceeded | The project is receiving too many run list requests. |
