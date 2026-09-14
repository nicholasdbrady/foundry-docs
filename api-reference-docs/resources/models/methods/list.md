---
title: List models
description: List models available for deployment.
last_verified_at: 2026-05-28
api_version: 2025-05-01
preview_or_ga_status: ga
example_validation_status: not-run
---

# List models

List the models available for deployment in a Foundry project.

Base URL: `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME`

Authentication: `Authorization: Bearer YOUR_ACCESS_TOKEN` or `api-key: YOUR_API_KEY`

## Request

`GET /models`

### Path parameters

This operation does not define path parameters.

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |
| `capability` | string | Optional | Return only models that support the specified capability. |
| `status` | string | Optional | Return only models that match the specified lifecycle status. |

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
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/models?api-version=2025-05-01&capability=reasoning&status=ga" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `object` | string | Container type. Returns `list`. |
| `data` | array | Array of model records. |
| `data[].id` | string | Stable identifier for the model record. |
| `data[].object` | string | Resource type. Returns `model`. |
| `data[].name` | string | Display name for the model. |
| `data[].version` | string | Default or selected model version. |
| `data[].capabilities` | array | Capability tags exposed by the model. |
| `data[].lifecycle_status` | string | Lifecycle state for the model version. |
| `data[].deprecation_date` | string | Planned deprecation date in ISO 8601 format, if known. |

### Example response
```json
{
  "object": "list",
  "data": [
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
    },
    {
      "id": "o4-mini",
      "object": "model",
      "name": "o4-mini",
      "version": "2025-03-20",
      "capabilities": [
        "reasoning",
        "tool_use"
      ],
      "lifecycle_status": "ga",
      "deprecation_date": "2027-03-31"
    }
  ]
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request` | The `capability` or `status` filter uses an unsupported value. |
| `401` | `unauthorized` | The request is not authenticated or the credential is expired. |
| `429` | `rate_limit_exceeded` | Too many list requests were sent in a short interval. |
