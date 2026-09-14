---
title: List connections
description: List project connections.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# List connections

List the connections available in a Foundry project.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /connections`

### Path parameters

This operation does not define path parameters.

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |
| `type` | string | Optional | Return only connections that match the specified connection type. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/connections?api-version=2025-05-01&type=AzureAISearch" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `object` | string | Container type. Returns `list`. |
| `data` | array | Array of connection objects. |
| `data[].id` | string | Fully qualified resource identifier for the connection. |
| `data[].object` | string | Resource type. Returns `connection`. |
| `data[].name` | string | Project-scoped connection name. |
| `data[].type` | string | Connection type. |
| `data[].target` | string | Endpoint URL or resource URI associated with the connection. |
| `data[].status` | string | Current validation status for the connection. |

### Example response
```json
{
  "object": "list",
  "data": [
    {
      "id": "conn_01JWQ8G6DJ7TF2XR5D0R0A9Q4M",
      "object": "connection",
      "name": "search-prod",
      "type": "AzureAISearch",
      "target": "https://contoso-search.search.windows.net",
      "status": "ready"
    },
    {
      "id": "conn_01JWQ8QKJ0M8K1B3W2P65V9V6N",
      "object": "connection",
      "name": "search-staging",
      "type": "AzureAISearch",
      "target": "https://contoso-staging-search.search.windows.net",
      "status": "ready"
    }
  ]
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `400` | `invalid_request` | The `type` filter uses an unsupported value. |
| `429` | `rate_limit_exceeded` | Too many list requests were sent in a short interval. |
