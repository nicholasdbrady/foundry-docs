# Retrieve an agent

Return the current definition for an agent by ID.

## Request

`GET /agents/{agentId}`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the agent to retrieve. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Agent identifier. |
| object | string | Resource type. Value is `agent`. |
| name | string | Agent name. |
| model | string | Model deployment name. |
| instructions | string | Stored agent instructions. |
| description | string | Agent description. |
| tools | array<object> | Configured tool definitions. |
| metadata | object | Metadata stored with the agent. |
| status | string | Current resource state. |
| created_at | string | UTC timestamp when the agent was created. |
| updated_at | string | UTC timestamp when the agent was last updated. |

### Example response

```json
{
  "id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "object": "agent",
  "name": "travel-agent",
  "model": "gpt-4o-mini",
  "instructions": "Answer travel support questions briefly and use tools when they improve accuracy.",
  "description": "Handles itinerary and policy questions.",
  "tools": [
    {"type": "file_search"},
    {"type": "code_interpreter"}
  ],
  "metadata": {
    "owner": "support-automation",
    "environment": "prod"
  },
  "status": "ready",
  "created_at": "2025-05-01T18:22:41Z",
  "updated_at": "2025-05-03T07:41:12Z"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | The request path or query string is malformed. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 403 | forbidden | The caller does not have access to this agent. |
| 404 | agent_not_found | The specified agent does not exist in the project. |
