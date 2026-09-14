# Delete a response

Delete a stored response resource by ID.

## Request

`DELETE /responses/{responseId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `responseId` | string | Required | Identifier of the response to delete. |

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
curl -X DELETE "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/responses/RESP_123?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Identifier of the deleted response. |
| `object` | string | Object type. This value is `response.deleted`. |
| `deleted` | boolean | Indicates whether the delete operation succeeded. |

### Example response

```json
{
  "id": "resp_01JX8V6C4FQ2R6P4Z5W8N9K7M1",
  "object": "response.deleted",
  "deleted": true
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | No response resource exists with the specified `responseId`. |
| `409` | `conflict` | The response cannot be deleted because another operation is still finalizing it. |
