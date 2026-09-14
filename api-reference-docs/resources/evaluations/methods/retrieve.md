# Retrieve an evaluation

Retrieve an evaluation definition by ID.

## Request

`GET /evaluations/{evaluationId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `evaluationId` | string | Required | Identifier of the evaluation to retrieve. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/EVAL_123?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier for the evaluation. |
| `object` | string | Object type. This value is `evaluation`. |
| `name` | string | Display name of the evaluation. |
| `description` | string | Description of the evaluation. |
| `evaluators` | array | Evaluators configured for this evaluation. |
| `data_source` | object | Default data source configuration. |
| `updated_at` | string | Last modification timestamp, if available. |

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
  "updated_at": "2025-05-21T15:12:09Z"
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | No evaluation exists with the specified `evaluationId`. |
| `429` | `rate_limit_exceeded` | The request exceeded a project rate limit. |
