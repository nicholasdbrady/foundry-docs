---
title: List deployments
description: List project deployments.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# List deployments

List the deployments available in a Foundry project.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /deployments`

### Path parameters

This operation does not define path parameters.

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |
| `provisioningState` | string | Optional | Return only deployments that match the specified provisioning state. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/deployments?api-version=2025-05-01&provisioningState=succeeded" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `object` | string | Container type. Returns `list`. |
| `data` | array | Array of deployment objects. |
| `data[].id` | string | Fully qualified resource identifier for the deployment. |
| `data[].object` | string | Resource type. Returns `deployment`. |
| `data[].name` | string | Project-scoped deployment name. |
| `data[].model` | object | Model definition associated with the deployment. |
| `data[].sku` | object | Capacity configuration for the deployment. |
| `data[].provisioningState` | string | Current provisioning state. |

### Example response
```json
{
  "object": "list",
  "data": [
    {
      "id": "dep_01JWQ94Z4J2BRBB3WM5D6M5WDB",
      "object": "deployment",
      "name": "gpt-4o-mini-prod",
      "model": {
        "name": "gpt-4o-mini",
        "version": "2025-04-14"
      },
      "sku": {
        "name": "Standard",
        "capacity": 20
      },
      "provisioningState": "succeeded"
    }
  ]
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request` | The `provisioningState` filter uses an unsupported value. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `429` | `rate_limit_exceeded` | Too many list requests were sent in a short interval. |
