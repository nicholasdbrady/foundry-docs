# Create an evaluation

Create an evaluation definition for scoring model outputs or agent behavior.

## Request

`POST /evaluations`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| None. |  |  | This operation uses the project-scoped base URL. |

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
| `name` | string | Required | Display name for the evaluation definition. |
| `description` | string | Optional | Description of the evaluation purpose or scope. |
| `evaluators` | array | Required | Evaluators to apply during runs. |
| `data_source` | object | Required | Default data source configuration for runs created from this evaluation. |

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "support-answer-quality",
    "description": "Scores groundedness and relevance for support responses.",
    "evaluators": [
      {
        "type": "builtin",
        "name": "groundedness",
        "config": {
          "source": "response"
        }
      },
      {
        "type": "custom",
        "name": "contains_refund_policy",
        "config": {
          "pass_condition": "response.includes(\"refund\")"
        }
      }
    ],
    "data_source": {
      "type": "dataset",
      "dataset_id": "ds_01JX8W1Z3JHDSFMC7JJ8YXXF92"
    }
  }'
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier for the evaluation. |
| `object` | string | Object type. This value is `evaluation`. |
| `name` | string | Display name of the evaluation. |
| `description` | string | Description provided when the evaluation was created. |
| `evaluators` | array | Evaluators configured for the evaluation. |
| `data_source` | object | Default data source configuration. |
| `created_at` | string | Timestamp when the evaluation was created. |

### Example response

```json
{
  "id": "eval_01JX8W4E8Q50X89Q6N3S7E3T7A",
  "object": "evaluation",
  "name": "support-answer-quality",
  "description": "Scores groundedness and relevance for support responses.",
  "evaluators": [
    {
      "type": "builtin",
      "name": "groundedness"
    },
    {
      "type": "custom",
      "name": "contains_refund_policy"
    }
  ],
  "data_source": {
    "type": "dataset",
    "dataset_id": "ds_01JX8W1Z3JHDSFMC7JJ8YXXF92"
  },
  "created_at": "2025-05-21T15:03:18Z"
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request_error` | The request body is missing `name`, `evaluators`, or `data_source`, or the evaluator configuration is invalid. |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | The specified dataset or referenced project resource was not found. |
| `409` | `conflict` | Another operation is using the same evaluation name or data source in a conflicting way. |
