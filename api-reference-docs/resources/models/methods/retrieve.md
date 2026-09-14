---
title: Retrieve a model
description: Retrieve a model record by identifier.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# Retrieve a model

Retrieve a model record by identifier.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /models/{modelId}`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `modelId` | string | Required | Identifier of the model record to retrieve. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/models/gpt-4o-mini?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable identifier for the model record. |
| `object` | string | Resource type. Returns `model`. |
| `name` | string | Display name for the model. |
| `version` | string | Default or selected model version. |
| `capabilities` | array | Capability tags exposed by the model. |
| `lifecycle_status` | string | Lifecycle state for the model version. |
| `deprecation_date` | string | Planned deprecation date in ISO 8601 format, if known. |

### Example response
```json
{
  "id": "gpt-4o-mini",
  "object": "model",
  "name": "GPT-4o mini",
  "version": "2025-04-14",
  "capabilities": [
    "chat",
    "reasoning",
    "vision"
  ],
  "lifecycle_status": "ga",
  "deprecation_date": "2027-01-31"
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `404` | `model_not_found` | No model with the specified `modelId` is available to the project. |
| `429` | `rate_limit_exceeded` | Too many read requests were sent in a short interval. |
