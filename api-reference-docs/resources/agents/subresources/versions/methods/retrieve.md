# Retrieve an agent version

Return a specific version snapshot for an agent.

## Request

`GET /agents/{agentId}/versions/{versionId}`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the owning agent. |
| versionId | string | Required | Identifier of the version to retrieve. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/versions/ver_01JY4Z9VZXQ2F0A2VMBN3S12GX?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Version identifier. |
| object | string | Resource type. Value is `agent.version`. |
| agent_id | string | Identifier of the parent agent. |
| version | string | Human-readable version number. |
| model | string | Model deployment stored in the version snapshot. |
| instructions | string | Instructions stored in the version snapshot. |
| tools | array<object> | Tool definitions stored in the version snapshot. |
| metadata | object | Metadata stored in the version snapshot. |
| created_at | string | UTC timestamp when the version snapshot was created. |

### Example response

```json
{
  "id": "ver_01JY4Z9VZXQ2F0A2VMBN3S12GX",
  "object": "agent.version",
  "agent_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "version": "3",
  "model": "gpt-4o-mini",
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
  },
  "created_at": "2025-05-03T07:41:12Z"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 401 | unauthorized | Authentication failed or was not provided. |
| 403 | forbidden | The caller does not have access to this version snapshot. |
| 404 | version_not_found | The specified version does not exist for the agent. |
| 409 | agent_version_mismatch | The version does not belong to the specified agent. |
