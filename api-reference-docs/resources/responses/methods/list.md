# List responses

List responses in a project with offset-based pagination.

## Request

`GET /responses`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| None. |  |  | This operation uses the project-scoped base URL. |

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |
| `top` | integer | Optional | Maximum number of items to return. |
| `skip` | integer | Optional | Number of items to skip before returning results. |

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
curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/responses?api-version=2025-05-01&top=2&skip=0" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `object` | string | Object type. This value is `list`. |
| `data` | array | Page of response resources. |
| `has_more` | boolean | Indicates whether more items are available after this page. |
| `top` | integer | Page size applied to the request. |
| `skip` | integer | Offset applied to the request. |

### Example response

```json
{
  "object": "list",
  "data": [
    {
      "id": "resp_01JX8V6C4FQ2R6P4Z5W8N9K7M1",
      "object": "response",
      "status": "completed",
      "model": "gpt-4.1-mini",
      "created_at": "2025-05-21T14:22:31Z"
    },
    {
      "id": "resp_01JX8V8K2TQ8F3E8P8M2H7Y0B5",
      "object": "response",
      "status": "in_progress",
      "model": "gpt-4.1-mini",
      "created_at": "2025-05-21T14:23:10Z"
    }
  ],
  "has_more": true,
  "top": 2,
  "skip": 0
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request_error` | The `top` or `skip` value is invalid. |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `429` | `rate_limit_exceeded` | The request exceeded a project or deployment rate limit. |
