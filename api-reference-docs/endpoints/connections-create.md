# Create connection

## 1. One-line purpose statement

**Purpose:** Create a project connection so agents and project features can securely reference an external resource.

## 2. When to use / when not to use

**Use this operation when:**
- You need to connect the project to Azure AI Search, Azure OpenAI, storage, or another supported external system.
- You want agents or tools to reference a named connection instead of storing raw secrets in application code.
- You are provisioning project infrastructure for a new environment.

**Do not use this operation when:**
- Use `GET /connections` when you only need to inspect existing connections.
- Use the credential-retrieval operation only when the connection already exists and you need to validate its secret material.
- Do not store production secrets directly in agent definitions when a project connection can hold them.

## 3. Method + path + required auth/headers

**HTTP method:** `POST`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/connections`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to manage project connections.

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
| `name` | string | yes | Friendly project-scoped connection name. |
| `type` | string | yes | Connection category such as `CognitiveSearch`, `AzureOpenAI`, or `ApiKey`. |
| `target` | string | yes | Endpoint or resource URI for the external system. |
| `auth_type` | string | yes | Authentication mode such as `ApiKey` or `AAD`. |
| `credentials` | object | no | Credential material required by the selected auth type. Secrets are write-only in the create call. |
| `metadata` | object | no | Tags or non-secret descriptors that help identify the connection purpose. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/connections?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "hotel-search",
    "type": "CognitiveSearch",
    "target": "https://YOUR_SEARCH_SERVICE.search.windows.net",
    "auth_type": "ApiKey",
    "credentials": {
      "key": "YOUR_SEARCH_ADMIN_KEY"
    },
    "metadata": {
      "purpose": "hotel-catalog"
    }
  }'
```

Secrets in `credentials` are typically accepted on create but redacted on later read operations.

## 6. Minimal successful response example

```json
{
  "name": "hotel-search",
  "id": "/projects/YOUR_PROJECT_NAME/connections/hotel-search",
  "type": "CognitiveSearch",
  "target": "https://YOUR_SEARCH_SERVICE.search.windows.net",
  "auth_type": "ApiKey",
  "metadata": {
    "purpose": "hotel-catalog"
  },
  "credentials_redacted": true,
  "created_at": "2025-05-10T11:08:32Z"
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `400 Bad Request` | The request uses an unsupported connection type or is missing a required credential field. | Verify the `type`, `auth_type`, and `credentials` combination for the target system. |
| `401 Unauthorized` | Authentication is missing or invalid. | Send a fresh bearer token or valid project API key. |
| `409 Conflict` | A connection with the same `name` already exists. | Use a different connection name or update the existing resource with the management workflow you use internally. |
| `422 Unprocessable Entity` | The target or credentials failed validation. | Confirm the endpoint URL, secret value, and any downstream RBAC prerequisites. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** Available connection types can vary by cloud and regional service support.
- **Behavior differences from GA:** Some SDKs expose connection creation through management-plane tooling rather than the project data-plane helpers.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Connection counts are project-scoped. Secret values are write-only and should be rotated through your standard secret-management process.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** Treat create as non-idempotent unless your workflow guarantees unique names. After a timeout, read by name before replaying the request.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [Use `azure-mgmt-cognitiveservices` project connection operations](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/ai-search#setup) when you need a management-plane create path. |
| JavaScript | [`@azure/arm-cognitiveservices` `projectConnections.create(...)`](https://learn.microsoft.com/javascript/api/@azure/arm-cognitiveservices/projectconnections?view=azure-node-latest). |
| C# | [Use ARM or infrastructure-as-code for project connection creation; no GA `Azure.AI.Projects` create method is documented](https://learn.microsoft.com/azure/foundry/how-to/connections-add). |
| Java | [Use REST, Bicep, or account-management tooling for connection creation; no GA `azure-ai-projects` create method is documented](https://learn.microsoft.com/azure/foundry/how-to/connections-add). |
