# Cancel an evaluation run

Cancel an in-progress evaluation run.

## Request

`POST /evaluations/{evaluationId}/runs/{runId}/cancel`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `evaluationId` | string | Required | Identifier of the parent evaluation. |
| `runId` | string | Required | Identifier of the run to cancel. |

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Authorization` | string | Conditional | Bearer access token. Use this header or `api-key`. |
| `api-key` | string | Conditional | Project API key. Use this header or `Authorization`. |
| `Accept` | string | Required | Use `application/json`. |

### Request body

This operation does not accept a request body.

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/EVAL_123/runs/RUN_123/cancel?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier for the run. |
| `object` | string | Object type. This value is `evaluation.run`. |
| `status` | string | Updated lifecycle state after the cancel request. |
| `cancelled_at` | string | Timestamp when cancellation completed, if available. |

### Example response

```json
{
  "id": "run_01JX8WC6P6Q3TK6B5N9VYB6G1V",
  "object": "evaluation.run",
  "status": "cancelled",
  "cancelled_at": "2025-05-21T15:44:13Z"
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | The specified evaluation or run was not found. |
| `409` | `conflict` | The run is already completed, failed, or cancelled and cannot be cancelled again. |
