---
title: Update a connection
description: Update a project connection by name.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Update a connection

Update a connection by name.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`PATCH /connections/{connectionName}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `connectionName` | string | Required | Name of the connection to update. |

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Authorization` | string | Conditional | Bearer access token. Use when authenticating with Microsoft Entra ID. |
| `api-key` | string | Conditional | Project API key. Use instead of `Authorization` for key-based auth. |
| `Content-Type` | string | Required | Must be `application/json`. |
| `Accept` | string | Optional | Set to `application/json`. |

### Request body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `target` | string | Optional | Updated endpoint URL or resource URI. |
| `credentials` | object | Optional | Replacement credential definition. Secret values are write-only. |
| `metadata` | object | Optional | Replacement or merged metadata fields for the connection. |

### Example request
```bash
curl -X PATCH "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/connections/search-prod?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "credentials": {
      "kind": "ApiKey",
      "key": "YOUR_NEW_SEARCH_ADMIN_KEY"
    },
    "metadata": {
      "environment": "prod",
      "owner": "search-platform"
    }
  }'
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Fully qualified resource identifier for the connection. |
| `object` | string | Resource type. Returns `connection`. |
| `name` | string | Project-scoped connection name. |
| `type` | string | Connection type. |
| `target` | string | Endpoint URL or resource URI associated with the connection. |
| `credentials` | object | Redacted credential descriptor for the connection. |
| `metadata` | object | Metadata attached to the connection. |
| `updated_at` | integer | Unix timestamp for the most recent update. |

### Example response
```json
{
  "id": "conn_01JWQ8G6DJ7TF2XR5D0R0A9Q4M",
  "object": "connection",
  "name": "search-prod",
  "type": "AzureAISearch",
  "target": "https://contoso-search.search.windows.net",
  "credentials": {
    "kind": "ApiKey",
    "redacted": true
  },
  "metadata": {
    "environment": "prod",
    "owner": "search-platform"
  },
  "updated_at": 1746873600
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request` | The request body contains an unsupported field or invalid credential shape. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `connection_not_found` | No connection with the specified `connectionName` exists in the project. |
| `422` | `connection_validation_failed` | The updated target or credentials failed validation. |
| `429` | `rate_limit_exceeded` | Too many update requests were sent in a short interval. |
