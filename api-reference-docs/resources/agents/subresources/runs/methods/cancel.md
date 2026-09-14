# Cancel a run

Request cancellation for an in-progress run.

## Request

`POST /agents/{agentId}/threads/{threadId}/runs/{runId}/cancel`

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agentId | string | Required | Identifier of the owning agent. |
| threadId | string | Required | Identifier of the associated thread. |
| runId | string | Required | Identifier of the run to cancel. |

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
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q/threads/thread_01JY50BR4X1SX6N54K9QGQKX7W/runs/run_01JY51J5SABRHNBR4Q7T5M4N3T/cancel?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
|-------|------|-------------|
| id | string | Run identifier. |
| object | string | Resource type. Value is `thread.run`. |
| status | string | Updated run status, typically `cancelling` or `cancelled`. |
| cancelled_at | string or null | UTC timestamp when cancellation completed, if available. |
| thread_id | string | Identifier of the associated thread. |
| agent_id | string | Identifier of the owning agent. |

### Example response

```json
{
  "id": "run_01JY51J5SABRHNBR4Q7T5M4N3T",
  "object": "thread.run",
  "status": "cancelling",
  "cancelled_at": null,
  "thread_id": "thread_01JY50BR4X1SX6N54K9QGQKX7W",
  "agent_id": "agt_01JY4Z9V1Y4D4S6V8M4X2K9B1Q"
}
```

## Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_state | The run is already in a terminal state and cannot be cancelled. |
| 401 | unauthorized | Authentication failed or was not provided. |
| 404 | run_not_found | The specified run does not exist for the thread. |
| 409 | cancellation_conflict | The service cannot cancel the run in its current execution phase. |
