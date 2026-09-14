---
title: Retrieve file content
description: Download raw file bytes by identifier.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Retrieve file content

Download the raw bytes for an uploaded file.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /files/{fileId}/content`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `fileId` | string | Required | Identifier of the file content to download. |

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Authorization` | string | Conditional | Bearer access token. Use when authenticating with Microsoft Entra ID. |
| `api-key` | string | Conditional | Project API key. Use instead of `Authorization` for key-based auth. |
| `Accept` | string | Optional | Set to `application/octet-stream` to request raw bytes. |

### Request body

This operation does not accept a request body.

### Example request
```bash
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/files/file_01JWQ9R7GQSS9B4RP5EM8M7EHC/content?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/octet-stream" \
  --output support-playbook.pdf
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| Body | binary | Raw file bytes for the requested file. |

### Example response
```text
%PDF-1.7
...binary content omitted...
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `file_not_found` | No file with the specified `fileId` exists in the project. |
| `409` | `file_not_ready` | The file has not finished processing and content is not available yet. |
| `429` | `rate_limit_exceeded` | Too many download requests were sent in a short interval. |
