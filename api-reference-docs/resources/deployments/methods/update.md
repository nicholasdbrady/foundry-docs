---
title: Update a deployment
description: Update a deployment by name.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Update a deployment

Update a deployment by name.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`PATCH /deployments/{deploymentName}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `deploymentName` | string | Required | Name of the deployment to update. |

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
| `sku` | object | Optional | Replacement SKU configuration for the deployment. |
| `sku.capacity` | integer | Optional | Updated capacity for the deployment. |
| `versionUpgradeOption` | string | Optional | Updated upgrade behavior for new compatible model versions. |

### Example request
```bash
curl -X PATCH "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/deployments/gpt-4o-mini-prod?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "sku": {
      "capacity": 30
    },
    "versionUpgradeOption": "NoAutoUpgrade"
  }'
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
| `provisioningState` | string | Current provisioning state after the update request. |
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
    "capacity": 30
  },
  "versionUpgradeOption": "NoAutoUpgrade",
  "provisioningState": "updating",
  "updated_at": 1746877200
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request` | The request body contains an unsupported field or invalid capacity value. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `deployment_not_found` | No deployment with the specified `deploymentName` exists in the project. |
| `409` | `quota_exceeded` | The requested capacity exceeds available regional quota. |
| `422` | `deployment_validation_failed` | The requested upgrade option is not valid for the deployment. |
