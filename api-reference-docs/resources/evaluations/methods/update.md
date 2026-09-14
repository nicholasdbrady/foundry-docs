# Update an evaluation

Update fields on an existing evaluation definition.

## Request

`PATCH /evaluations/{evaluationId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `evaluationId` | string | Required | Identifier of the evaluation to update. |

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
| `name` | string | Optional | Updated display name for the evaluation. |
| `description` | string | Optional | Updated description for the evaluation. |
| `evaluators` | array | Optional | Replacement evaluator configuration. |
| `data_source` | object | Optional | Replacement default data source configuration. |

### Example request

```bash
curl -X PATCH "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/EVAL_123?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "description": "Scores groundedness, relevance, and policy coverage for support responses.",
    "evaluators": [
      {
        "type": "builtin",
        "name": "groundedness"
      },
      {
        "type": "builtin",
        "name": "relevance"
      },
      {
        "type": "custom",
        "name": "contains_refund_policy"
      }
    ]
  }'
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier for the evaluation. |
| `object` | string | Object type. This value is `evaluation`. |
| `name` | string | Current display name of the evaluation. |
| `description` | string | Current description of the evaluation. |
| `evaluators` | array | Current evaluator configuration. |
| `updated_at` | string | Timestamp when the evaluation was last updated. |

### Example response

```json
{
  "id": "eval_01JX8W4E8Q50X89Q6N3S7E3T7A",
  "object": "evaluation",
  "name": "support-answer-quality",
  "description": "Scores groundedness, relevance, and policy coverage for support responses.",
  "evaluators": [
    {
      "type": "builtin",
      "name": "groundedness"
    },
    {
      "type": "builtin",
      "name": "relevance"
    },
    {
      "type": "custom",
      "name": "contains_refund_policy"
    }
  ],
  "updated_at": "2025-05-21T15:15:41Z"
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request_error` | The patch payload contains unsupported fields or invalid evaluator configuration. |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | No evaluation exists with the specified `evaluationId`. |
| `409` | `conflict` | The update conflicts with an evaluation run or another resource state. |
