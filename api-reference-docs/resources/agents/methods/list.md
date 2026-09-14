# List agents

List agents in a Foundry project.

## Request

`GET /agents`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| None | - | - | This operation does not define path parameters. |

### Query parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api-version | string | Required | API version. Use `2025-05-01`. |
| limit | integer | Optional | Maximum number of agents to return. |
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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01&limit=2&order=desc" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| object | string | Collection type. Value is `list`. |
| data | array<object> | Agents returned for the current page. |
| first_id | string | Identifier of the first item in `data`. |
| last_id | string | Identifier of the last item in `data`. |
| has_more | boolean | Indicates whether another page is available. |

### Example response

```json
{
  "object": "list",
  "data": [
    {
      "id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
      "object": "agent",
      "name": "travel-agent",
      "model": "gpt-4o-mini",
      "status": "ready",
      "created_at": "2025-05-01T18:22:41Z"
    },
    {
      "id": "agt_01JY4ZE8D0P7X1QX0HVC2M5Q9J",
      "object": "agent",
      "name": "refund-agent",
      "model": "gpt-4.1-mini",
      "status": "ready",
      "created_at": "2025-04-28T11:09:15Z"
    }
  ],
  "first_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "last_id": "agt_01JY4ZE8D0P7X1QX0HVC2M5Q9J",
  "has_more": false
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | The paging or sorting parameters are malformed. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 403 | forbidden | The caller does not have permission to list agents. |
| 429 | rate_limit_exceeded | The project is receiving too many list requests. |
