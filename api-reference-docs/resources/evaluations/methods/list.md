# List evaluations

List evaluation definitions in a project.

## Request

`GET /evaluations`

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
| `Accept` | string | Required | Use `application/json`. |

### Request body

This operation does not accept a request body.

### Example request

```bash
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `object` | string | Object type. This value is `list`. |
| `data` | array | Evaluation definitions in the project. |
| `has_more` | boolean | Indicates whether another page is available. |

### Example response

```json
{
  "object": "list",
  "data": [
    {
      "id": "eval_01JX8W4E8Q50X89Q6N3S7E3T7A",
      "object": "evaluation",
      "name": "support-answer-quality",
      "created_at": "2025-05-21T15:03:18Z"
    },
    {
      "id": "eval_01JX8W6JE6Q9XT6M3G4VP5D0FD",
      "object": "evaluation",
      "name": "policy-safety-check",
      "created_at": "2025-05-21T15:18:09Z"
    }
  ],
  "has_more": false
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `429` | `rate_limit_exceeded` | The request exceeded a project rate limit. |
