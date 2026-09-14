---
title: Delete a connection
description: Delete a project connection by name.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Delete a connection

Delete a connection by name.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`DELETE /connections/{connectionName}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `connectionName` | string | Required | Name of the connection to delete. |

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Authorization` | string | Conditional | Bearer access token. Use when authenticating with Microsoft Entra ID. |
| `api-key` | string | Conditional | Project API key. Use instead of `Authorization` for key-based auth. |
| `Accept` | string | Optional | Set to `application/json`. |

### Request body

This operation does not accept a request body.

### Example request
```bash
curl -X DELETE "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/connections/search-prod?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Fully qualified resource identifier for the deleted connection. |
| `object` | string | Response type. Returns `connection.deleted`. |
| `deleted` | boolean | Indicates whether the connection was deleted. |

### Example response
```json
{
  "id": "conn_01JWQ8G6DJ7TF2XR5D0R0A9Q4M",
  "object": "connection.deleted",
  "deleted": true
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `connection_not_found` | No connection with the specified `connectionName` exists in the project. |
| `409` | `connection_in_use` | The connection is still referenced by another project resource. |
| `429` | `rate_limit_exceeded` | Too many delete requests were sent in a short interval. |
