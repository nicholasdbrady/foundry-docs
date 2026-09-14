# Retrieve a run

Return the current state of a run.

## Request

`GET /agents/{agentId}/threads/{threadId}/runs/{runId}`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the owning agent. |
| threadId | string | Required | Identifier of the thread associated with the run. |
| runId | string | Required | Identifier of the run to retrieve. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads/thread_01JY50BR4X1SX6N54K9QGQKX7W/runs/run_01JY51J5SABRHNBR4Q7T5M4N3T?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Run identifier. |
| object | string | Resource type. Value is `thread.run`. |
| agent_id | string | Identifier of the owning agent. |
| thread_id | string | Identifier of the associated thread. |
| status | string | Current run status. |
| started_at | string | UTC timestamp when execution started. |
| completed_at | string | UTC timestamp when execution completed, if present. |
| last_error | object or null | Error details for failed runs. |
| usage | object | Token usage for the run when available. |

### Example response

```json
{
  "id": "run_01JY51J5SABRHNBR4Q7T5M4N3T",
  "object": "thread.run",
  "agent_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q",
  "thread_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
  "status": "completed",
  "started_at": "2025-05-01T18:34:56Z",
  "completed_at": "2025-05-01T18:35:03Z",
  "last_error": null,
  "usage": {
    "input_tokens": 841,
    "output_tokens": 126,
    "total_tokens": 967
  }
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 401 | unauthorized | Authentication failed or was not provided. |
| 403 | forbidden | The caller does not have access to this run. |
| 404 | run_not_found | The specified run does not exist for the thread. |
| 409 | agent_thread_run_mismatch | The run does not belong to the specified agent and thread combination. |
