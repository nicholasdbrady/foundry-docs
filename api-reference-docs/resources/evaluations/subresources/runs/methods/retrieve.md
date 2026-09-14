# Retrieve an evaluation run

Retrieve an evaluation run by ID.

## Request

`GET /evaluations/{evaluationId}/runs/{runId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `evaluationId` | string | Required | Identifier of the parent evaluation. |
| `runId` | string | Required | Identifier of the run to retrieve. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/EVAL_123/runs/RUN_123?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier for the run. |
| `object` | string | Object type. This value is `evaluation.run`. |
| `status` | string | Current lifecycle state for the run. |
| `summary` | object | Aggregate metrics for the run. |
| `summary.pass_rate` | number | Overall pass rate for the evaluated items, when available. |
| `item_scores` | array | Item-level scores or labels returned by the evaluators. |

### Example response

```json
{
  "id": "run_01JX8WAG5J2K6YF3RP6B1TR9BM",
  "object": "evaluation.run",
  "status": "completed",
  "summary": {
    "pass_rate": 0.91,
    "average_scores": {
      "groundedness": 0.94,
      "relevance": 0.88
    }
  },
  "item_scores": [
    {
      "item_id": "case-001",
      "scores": {
        "groundedness": 0.98,
        "relevance": 0.92
      },
      "label": "pass"
    },
    {
      "item_id": "case-002",
      "scores": {
        "groundedness": 0.74,
        "relevance": 0.69
      },
      "label": "fail"
    }
  ]
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | The specified evaluation or run was not found. |
| `429` | `rate_limit_exceeded` | The request exceeded a project rate limit. |
