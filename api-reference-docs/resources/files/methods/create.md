---
title: Upload a file
description: Upload a file to a project.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Upload a file

Upload a file for agents or evaluations.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`POST /files`

### Path parameters

This operation does not define path parameters.

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Authorization` | string | Conditional | Bearer access token. Use when authenticating with Microsoft Entra ID. |
| `api-key` | string | Conditional | Project API key. Use instead of `Authorization` for key-based auth. |
| `Content-Type` | string | Required | Must be `multipart/form-data`. `curl` sets the boundary automatically when `-F` is used. |
| `Accept` | string | Optional | Set to `application/json`. |

### Request body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | binary | Required | File contents to upload. |
| `purpose` | string | Required | Intended use for the file. Supported values include `assistants`, `fine-tune`, and `evaluations`. |

### Example request
```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/files?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json" \
  -F "purpose=assistants" \
  -F "file=@YOUR_FILE_PATH"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable identifier for the uploaded file. |
| `object` | string | Resource type. Returns `file`. |
| `filename` | string | Original filename supplied by the client. |
| `bytes` | integer | Size of the uploaded file in bytes. |
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
| `400` | `invalid_request` | The multipart form is missing `file` or `purpose`. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `413` | `file_too_large` | The uploaded file exceeds the maximum allowed size. |
| `415` | `unsupported_media_type` | The uploaded file format is not supported for the specified purpose. |
| `429` | `rate_limit_exceeded` | Too many upload requests were sent in a short interval. |
