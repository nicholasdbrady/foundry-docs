# Create an agent

Create a new agent definition in a Foundry project.

## Request

`POST /agents`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| None | - | - | This operation does not define path parameters. |

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
| name | string | Required | Unique agent name within the project. |
| model | string | Required | Model deployment name used by the agent. |
| instructions | string | Required | Default system instructions applied to runs. |
| description | string | Optional | Human-readable summary of the agent. |
| tools | array<object> | Optional | Tool definitions such as `code_interpreter`, `file_search`, `azure_ai_search`, or `openapi`. |
| metadata | object | Optional | Application-defined key-value metadata. |
| temperature | number | Optional | Sampling temperature for model generation. |
| response_format | object | Optional | Output formatting preference for compatible models. |

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "travel-agent",
    "model": "gpt-4o-mini",
    "instructions": "Answer travel support questions briefly and use tools when they improve accuracy.",
    "description": "Handles itinerary and policy questions.",
    "tools": [
      {"type": "file_search"},
      {"type": "code_interpreter"},
      {"type": "azure_ai_search", "connection_name": "travel-search"}
    ],
    "metadata": {
      "owner": "support-automation",
      "environment": "prod"
    },
    "temperature": 0.2
  }'
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier for the created agent. |
| object | string | Resource type. Value is `agent`. |
| name | string | Agent name. |
| model | string | Model deployment name. |
| instructions | string | Stored default instructions. |
| description | string | Agent description. |
| tools | array<object> | Configured tool definitions. |
| metadata | object | Metadata stored with the agent. |
| status | string | Current provisioning state, such as `ready`. |
| created_at | string | UTC timestamp when the agent was created. |

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
    {"type": "code_interpreter"},
    {"type": "azure_ai_search", "connection_name": "travel-search"}
  ],
  "metadata": {
    "owner": "support-automation",
    "environment": "prod"
  },
  "status": "ready",
  "created_at": "2025-05-01T18:22:41Z"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_request | One or more required fields are missing or malformed. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | project_not_found | The project endpoint or project name was not found. |
| 409 | agent_name_conflict | An agent with the same name already exists in the project. |
