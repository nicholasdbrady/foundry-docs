# Delete an evaluation

Delete an evaluation definition by ID.

## Request

`DELETE /evaluations/{evaluationId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `evaluationId` | string | Required | Identifier of the evaluation to delete. |

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
curl -X DELETE "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/EVAL_123?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Identifier of the deleted evaluation. |
| `object` | string | Object type. This value is `evaluation.deleted`. |
| `deleted` | boolean | Indicates whether the delete operation succeeded. |

### Example response

```json
{
  "id": "eval_01JX8W4E8Q50X89Q6N3S7E3T7A",
  "object": "evaluation.deleted",
  "deleted": true
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | No evaluation exists with the specified `evaluationId`. |
| `409` | `conflict` | The evaluation has active runs and cannot be deleted yet. |
