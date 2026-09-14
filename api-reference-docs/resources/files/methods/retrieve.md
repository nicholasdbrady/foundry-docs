---
title: Retrieve file metadata
description: Retrieve file metadata by identifier.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Retrieve file metadata

Retrieve file metadata by identifier.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /files/{fileId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `fileId` | string | Required | Identifier of the file to retrieve. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/files/file_01JWQ9R7GQSS9B4RP5EM8M7EHC?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable identifier for the uploaded file. |
| `object` | string | Resource type. Returns `file`. |
| `filename` | string | Original filename supplied by the client. |
| `bytes` | integer | Size of the file in bytes. |
| `purpose` | string | Purpose assigned to the file. |
| `status` | string | Current processing state for the file. |
| `created_at` | integer | Unix timestamp for resource creation. |

### Example response
```json
{
  "id": "file_01JWQ9R7GQSS9B4RP5EM8M7EHC",
  "object": "file",
  "filename": "support-playbook.pdf",
  "bytes": 248932,
  "purpose": "assistants",
  "status": "processed",
  "created_at": 1746708000
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `file_not_found` | No file with the specified `fileId` exists in the project. |
| `429` | `rate_limit_exceeded` | Too many read requests were sent in a short interval. |
