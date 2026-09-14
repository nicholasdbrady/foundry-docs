# List evaluation runs

List runs for an evaluation definition.

## Request

`GET /evaluations/{evaluationId}/runs`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `evaluationId` | string | Required | Identifier of the parent evaluation. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/EVAL_123/runs?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `object` | string | Object type. This value is `list`. |
| `data` | array | Runs for the specified evaluation. |
| `has_more` | boolean | Indicates whether another page is available. |

### Example response

```json
{
  "object": "list",
  "data": [
    {
      "id": "run_01JX8WAG5J2K6YF3RP6B1TR9BM",
      "object": "evaluation.run",
      "status": "completed",
      "created_at": "2025-05-21T15:25:02Z"
    },
    {
      "id": "run_01JX8WC6P6Q3TK6B5N9VYB6G1V",
      "object": "evaluation.run",
      "status": "in_progress",
      "created_at": "2025-05-21T15:41:55Z"
    }
  ],
  "has_more": false
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | The specified evaluation was not found. |
| `429` | `rate_limit_exceeded` | The request exceeded a project rate limit. |
