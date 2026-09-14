---
title: Retrieve a deployment
description: Retrieve a deployment by name.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Retrieve a deployment

Retrieve a deployment by name.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /deployments/{deploymentName}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `deploymentName` | string | Required | Name of the deployment to retrieve. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/deployments/gpt-4o-mini-prod?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Fully qualified resource identifier for the deployment. |
| `object` | string | Resource type. Returns `deployment`. |
| `name` | string | Project-scoped deployment name. |
| `model` | object | Model definition associated with the deployment. |
| `sku` | object | Capacity configuration for the deployment. |
| `versionUpgradeOption` | string | Current upgrade behavior for the deployment. |
| `provisioningState` | string | Current provisioning state. |
| `created_at` | integer | Unix timestamp for resource creation. |
| `updated_at` | integer | Unix timestamp for the most recent update. |

### Example response
```json
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
  "versionUpgradeOption": "OnceNewDefaultVersionAvailable",
  "provisioningState": "succeeded",
  "created_at": 1746704400,
  "updated_at": 1746790800
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `deployment_not_found` | No deployment with the specified `deploymentName` exists in the project. |
| `429` | `rate_limit_exceeded` | Too many read requests were sent in a short interval. |
