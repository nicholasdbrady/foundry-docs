---
title: Retrieve a connection
description: Retrieve a project connection by name.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Retrieve a connection

Retrieve a connection by name.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /connections/{connectionName}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `connectionName` | string | Required | Name of the connection to retrieve. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/connections/search-prod?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
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
| `status` | string | Current validation status for the connection. |
| `created_at` | integer | Unix timestamp for resource creation. |
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
    "owner": "support-search"
  },
  "status": "ready",
  "created_at": 1746700800,
  "updated_at": 1746787200
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `connection_not_found` | No connection with the specified `connectionName` exists in the project. |
| `429` | `rate_limit_exceeded` | Too many read requests were sent in a short interval. |
