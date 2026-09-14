---
title: Create a connection
description: Create a project connection to an external service.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Create a connection

Create a connection that links a Foundry project to an external service.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`POST /connections`

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
| `Content-Type` | string | Required | Must be `application/json`. |
| `Accept` | string | Optional | Set to `application/json`. |

### Request body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | Required | Project-scoped connection name. |
| `type` | string | Required | Connection type. Supported values include `AzureOpenAI`, `AzureAISearch`, `AzureBlobStorage`, `CustomKeys`, and `APIKey`. |
| `target` | string | Required | Endpoint URL or resource URI for the external service. |
| `credentials` | object | Required | Credential definition for the target service. This can contain a key, a token, or a managed identity reference. |
| `metadata` | object | Optional | Non-secret metadata such as environment, owner, or purpose. |

### Example request
```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/connections?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "search-prod",
    "type": "AzureAISearch",
    "target": "https://contoso-search.search.windows.net",
    "credentials": {
      "kind": "ApiKey",
      "key": "YOUR_SEARCH_ADMIN_KEY"
    },
    "metadata": {
      "environment": "prod",
      "owner": "support-search"
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
| `credentials` | object | Redacted credential descriptor. Secret material is not returned. |
| `metadata` | object | Metadata attached to the connection. |
| `created_at` | integer | Unix timestamp for resource creation. |

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
  "created_at": 1746700800
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request` | The request body is missing a required field or uses an unsupported connection type. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `409` | `connection_already_exists` | A connection with the same `name` already exists in the project. |
| `422` | `connection_validation_failed` | The target endpoint or credential payload could not be validated. |
| `429` | `rate_limit_exceeded` | Too many connection management requests were sent in a short interval. |
