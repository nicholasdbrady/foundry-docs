---
title: List files
description: List uploaded files.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# List files

List the files available in a Foundry project.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /files`

### Path parameters

This operation does not define path parameters.

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |
| `purpose` | string | Optional | Return only files with the specified purpose. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/files?api-version=2025-05-01&purpose=assistants" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `object` | string | Container type. Returns `list`. |
| `data` | array | Array of file objects. |
| `data[].id` | string | Stable identifier for the uploaded file. |
| `data[].object` | string | Resource type. Returns `file`. |
| `data[].filename` | string | Original filename supplied by the client. |
| `data[].bytes` | integer | Size of the file in bytes. |
| `data[].purpose` | string | Purpose assigned to the file. |
| `data[].status` | string | Current processing state for the file. |

### Example response
```json
{
  "object": "list",
  "data": [
    {
      "id": "file_01JWQ9R7GQSS9B4RP5EM8M7EHC",
      "object": "file",
      "filename": "support-playbook.pdf",
      "bytes": 248932,
      "purpose": "assistants",
      "status": "processed"
    },
    {
      "id": "file_01JWQ9V2F4ES3MX1E9QDWAFQ7N",
      "object": "file",
      "filename": "faq-index.csv",
      "bytes": 18342,
      "purpose": "assistants",
      "status": "processed"
    }
  ]
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request` | The `purpose` filter uses an unsupported value. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `429` | `rate_limit_exceeded` | Too many list requests were sent in a short interval. |
