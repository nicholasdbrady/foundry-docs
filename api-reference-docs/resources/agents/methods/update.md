# Update an agent

Modify mutable properties on an existing agent.

## Request

`PATCH /agents/{agentId}`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the agent to update. |

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
| name | string | Optional | Updated agent name. |
| instructions | string | Optional | Replacement default instructions. |
| description | string | Optional | Updated human-readable description. |
| tools | array<object> | Optional | Replacement tool list. |
| metadata | object | Optional | Replacement metadata object. |
| temperature | number | Optional | Updated sampling temperature. |
| response_format | object | Optional | Updated output formatting preference. |

### Example request

```bash
curl -X PATCH "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "instructions": "Answer travel support questions in three bullet points and cite policy names when available.",
    "tools": [
      {"type": "file_search"},
      {"type": "code_interpreter"},
      {"type": "openapi", "connection_name": "travel-booking-api"}
    ],
    "metadata": {
      "owner": "support-automation",
      "environment": "prod",
      "release": "2025-05-03"
    }
  }'
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Agent identifier. |
| object | string | Resource type. Value is `agent`. |
| name | string | Agent name after the update. |
| instructions | string | Stored default instructions after the update. |
| description | string | Agent description after the update. |
| tools | array<object> | Configured tool definitions after the update. |
| metadata | object | Metadata stored with the agent after the update. |
| status | string | Current resource state. |
| updated_at | string | UTC timestamp when the update was applied. |

### Example response

```json
{
  "id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "object": "agent",
  "name": "travel-agent",
  "instructions": "Answer travel support questions in three bullet points and cite policy names when available.",
  "description": "Handles itinerary and policy questions.",
  "tools": [
    {"type": "file_search"},
    {"type": "code_interpreter"},
    {"type": "openapi", "connection_name": "travel-booking-api"}
  ],
  "metadata": {
    "owner": "support-automation",
    "environment": "prod",
    "release": "2025-05-03"
  },
  "status": "ready",
  "updated_at": "2025-05-03T07:41:12Z"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | The update document contains unsupported or malformed fields. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | agent_not_found | The specified agent does not exist in the project. |
| 409 | agent_update_conflict | The resource is temporarily locked or cannot be updated in its current state. |
