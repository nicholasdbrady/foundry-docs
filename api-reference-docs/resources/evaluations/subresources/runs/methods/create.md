# Create an evaluation run

Start a run for an evaluation definition.

## Request

`POST /evaluations/{evaluationId}/runs`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `evaluationId` | string | Required | Identifier of the evaluation to run. |

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Authorization` | string | Conditional | Bearer access token. Use this header or `api-key`. |
| `api-key` | string | Conditional | Project API key. Use this header or `Authorization`. |
| `Content-Type` | string | Required | Use `application/json`. |
| `Accept` | string | Required | Use `application/json`. |

### Request body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `data` | array or object | Required | Inline test cases, or a dataset reference used by the run. |
| `configuration` | object | Optional | Run-specific overrides for evaluators, target configuration, or thresholds. |
| `name` | string | Optional | Friendly name for the run. |

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/EVAL_123/runs?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "support-answer-quality-run-001",
    "data": {
      "type": "dataset",
      "dataset_id": "ds_01JX8W1Z3JHDSFMC7JJ8YXXF92"
    },
    "configuration": {
      "thresholds": {
        "groundedness": 0.8,
        "relevance": 0.8
      }
    }
  }'
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier for the run. |
| `object` | string | Object type. This value is `evaluation.run`. |
| `evaluation_id` | string | Parent evaluation identifier. |
| `status` | string | Lifecycle state such as `queued`, `in_progress`, `completed`, `failed`, or `cancelled`. |
| `created_at` | string | Timestamp when the run was created. |
| `configuration` | object | Effective run configuration. |

### Example response

```json
{
  "id": "run_01JX8WAG5J2K6YF3RP6B1TR9BM",
  "object": "evaluation.run",
  "evaluation_id": "eval_01JX8W4E8Q50X89Q6N3S7E3T7A",
  "status": "queued",
  "created_at": "2025-05-21T15:25:02Z",
  "configuration": {
    "thresholds": {
      "groundedness": 0.8,
      "relevance": 0.8
    }
  }
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request_error` | The run request is missing `data` or contains invalid configuration overrides. |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | The specified evaluation or dataset was not found. |
| `409` | `conflict` | The evaluation is not in a state that can accept a new run. |
