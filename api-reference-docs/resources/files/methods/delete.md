---
title: Delete a file
description: Delete a file by identifier.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Delete a file

Delete a file by identifier.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`DELETE /files/{fileId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `fileId` | string | Required | Identifier of the file to delete. |

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
curl -X DELETE "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/files/file_01JWQ9R7GQSS9B4RP5EM8M7EHC?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Identifier of the deleted file. |
| `object` | string | Response type. Returns `file.deleted`. |
| `deleted` | boolean | Indicates whether the file was deleted. |

### Example response
```json
{
  "id": "file_01JWQ9R7GQSS9B4RP5EM8M7EHC",
  "object": "file.deleted",
  "deleted": true
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `file_not_found` | No file with the specified `fileId` exists in the project. |
| `409` | `file_in_use` | The file is currently referenced by another resource and cannot be deleted yet. |
| `429` | `rate_limit_exceeded` | Too many delete requests were sent in a short interval. |
