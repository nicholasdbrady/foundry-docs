# Cancel a response

Cancel an in-progress response.

## Request

`POST /responses/{responseId}/cancel`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `responseId` | string | Required | Identifier of the response to cancel. |

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
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/responses/RESP_123/cancel?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Identifier of the response. |
| `object` | string | Object type. This value is `response`. |
| `status` | string | Updated lifecycle state after the cancel request. |
| `cancelled_at` | string | Timestamp when cancellation completed, if available. |

### Example response

```json
{
  "id": "resp_01JX8V8K2TQ8F3E8P8M2H7Y0B5",
  "object": "response",
  "status": "cancelled",
  "cancelled_at": "2025-05-21T14:24:02Z"
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | No response resource exists with the specified `responseId`. |
| `409` | `conflict` | The response is already completed, failed, or cancelled and cannot be cancelled again. |
