# Delete an agent

Delete an agent definition by ID.

## Request

`DELETE /agents/{agentId}`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the agent to delete. |

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
curl -X DELETE "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Identifier of the deleted agent. |
| object | string | Resource type. Value is `agent.deleted`. |
| deleted | boolean | Indicates whether the delete succeeded. |

### Example response

```json
{
  "id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "object": "agent.deleted",
  "deleted": true
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 401 | unauthorized | Authentication failed or was not provided. |
| 403 | forbidden | The caller does not have permission to delete this agent. |
| 404 | agent_not_found | The specified agent does not exist in the project. |
| 409 | agent_in_use | The agent cannot be deleted while active runs or dependent resources still exist. |
