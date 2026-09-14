# Create deployment

## 1. One-line purpose statement

**Purpose:** Create a model deployment in the project so runtime APIs can route requests by deployment name.

## 2. When to use / when not to use

**Use this operation when:**
- You need a new named deployment for a model family, version, and SKU combination.
- You are provisioning inference capacity before exposing a model to agents or application code.
- You want a stable deployment name that callers can reference for routing and rollback.

**Do not use this operation when:**
- Use `GET /deployments` when you only need to inspect existing deployments.
- Use a deployment update or scale workflow when you need to change capacity on an existing deployment rather than creating a new one.
- Do not send the model family name to runtime callers until the deployment reaches a succeeded provisioning state.

## 3. Method + path + required auth/headers

**HTTP method:** `POST`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/deployments`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to create or manage deployments for the project.

**Required headers:**
- `Content-Type: application/json`
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |

### Request body fields

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Project-scoped deployment name that runtime callers will use. |
| `model` | object | yes | Model metadata, typically including `name`, `version`, and `format`. |
| `sku` | object | yes | Provisioned SKU information such as tier and capacity. |
| `properties` | object | no | Optional deployment properties such as scaling or content filtering settings. |
| `tags` | object | no | Application-defined tags that help track environment or ownership. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/deployments?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "gpt-4.1-mini-prod",
    "model": {
      "name": "gpt-4.1-mini",
      "version": "2025-04-14",
      "format": "OpenAI"
    },
    "sku": {
      "name": "Standard",
      "capacity": 10
    }
  }'
```

Choose a deployment `name` that can stay stable for callers even if you later move traffic to a different model version.

## 6. Minimal successful response example

```json
{
  "name": "gpt-4.1-mini-prod",
  "object": "deployment",
  "provisioning_state": "Creating",
  "model": {
    "name": "gpt-4.1-mini",
    "version": "2025-04-14",
    "format": "OpenAI"
  },
  "sku": {
    "name": "Standard",
    "capacity": 10
  },
  "created_at": "2025-05-10T11:32:40Z"
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `400 Bad Request` | The model, version, region, or SKU combination is invalid. | Verify that the selected model version is supported in the region and that the SKU matches the model family requirements. |
| `401 Unauthorized` | Authentication is missing or invalid. | Use a fresh bearer token or valid project API key. |
| `409 Conflict` | A deployment with the same name already exists or quota is exhausted for the requested capacity. | Use a different deployment name, reduce capacity, or request additional quota before retrying. |
| `429 Too Many Requests` | Too many deployment-management operations are being issued concurrently. | Poll the current provisioning operation instead of resubmitting the same create request. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** Model family support still depends on region and cloud.
- **Behavior differences from GA:** Some SDKs expose deployment creation through management-plane APIs instead of the project data-plane helpers.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Provisioning capacity, supported SKUs, and concurrent deployment operations are quota-bound by region.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** Deployment creation is long-running. After submission, poll the deployment state instead of resending the same create request.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [Use `azure-mgmt-cognitiveservices` deployment create or update operations](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/create-model-deployments). |
| JavaScript | [Use Cognitive Services management APIs or infrastructure-as-code for deployment creation](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/create-model-deployments). |
| C# | [Use ARM/Cognitive Services management APIs or Bicep; no GA `Azure.AI.Projects` create method is documented](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/create-model-deployments). |
| Java | [Use ARM/Cognitive Services management APIs or Bicep; no GA `azure-ai-projects` create method is documented](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/create-model-deployments). |
