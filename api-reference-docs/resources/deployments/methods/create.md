---
title: Create a deployment
description: Create a model deployment in a project.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Create a deployment

Create a deployment that provisions inference capacity for a model.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`POST /deployments`

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
| `name` | string | Required | Project-scoped deployment name used at runtime. |
| `model` | object | Required | Model definition for the deployment. |
| `model.name` | string | Required | Model family or catalog name to deploy. |
| `model.version` | string | Required | Specific model version for the deployment. |
| `sku` | object | Required | Capacity configuration for the deployment. |
| `sku.name` | string | Required | SKU name, such as `Standard`. |
| `sku.capacity` | integer | Required | Requested capacity units for the deployment. |
| `versionUpgradeOption` | string | Optional | Upgrade behavior when a newer compatible version becomes available. |

### Example request
```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/deployments?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "gpt-4o-mini-prod",
    "model": {
      "name": "gpt-4o-mini",
      "version": "2025-04-14"
    },
    "sku": {
      "name": "Standard",
      "capacity": 20
    },
    "versionUpgradeOption": "OnceNewDefaultVersionAvailable"
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
| `provisioningState` | string | Current provisioning state. |
| `created_at` | integer | Unix timestamp for resource creation. |

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
  "provisioningState": "creating",
  "created_at": 1746704400
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request` | The request body is missing a required field or uses an unsupported model and SKU combination. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `409` | `deployment_already_exists` | A deployment with the same `name` already exists in the project. |
| `409` | `quota_exceeded` | The requested capacity exceeds available regional quota. |
| `422` | `deployment_validation_failed` | The model version or upgrade option is not valid for the selected deployment. |
