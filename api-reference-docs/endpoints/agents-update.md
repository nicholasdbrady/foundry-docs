# Update agent

## 1. One-line purpose statement

**Purpose:** Apply partial changes to an existing agent without recreating its identifier.

## 2. When to use / when not to use

**Use this operation when:**
- You need to revise instructions, metadata, or tool configuration on an existing agent.
- You want to change the backing deployment name while keeping the same agent ID.
- You need a targeted patch instead of creating a replacement resource and updating all callers.

**Do not use this operation when:**
- Use `POST /agents` when you need a second agent with a different identity.
- Use `GET /agents/{agentId}/versions` when you need a versioned rollout history rather than an in-place patch.
- Do not send a full replacement payload if you only need to inspect the resource; use `GET /agents/{agentId}` first.

## 3. Method + path + required auth/headers

**HTTP method:** `PATCH`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to modify project agents.

**Required headers:**
- `Content-Type: application/json`
- `Accept: application/json`
- `X-HTTP-Method-Override: PATCH` when a legacy client must send `POST` instead of `PATCH`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent identifier to update. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01` for the stable patch contract. |

### Request body fields

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `instructions` | string | no | New system instructions. Omit the field to keep the current value. |
| `description` | string | no | Updated description shown in management experiences. |
| `model` | string | no | Replacement deployment name for future runs. |
| `tools` | array<object> | no | Replacement tool definitions for the agent. |
| `metadata` | object | no | Updated application-defined metadata object. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X PATCH "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "instructions": "Answer travel questions in under 120 words and include the cancellation window.",
    "metadata": {
      "owner": "support-automation",
      "environment": "prod"
    }
  }'
```

Send only the fields you want to change. Omitted mutable fields keep their existing values.

## 6. Minimal successful response example

```json
{
  "id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
  "object": "agent",
  "name": "travel-agent",
  "model": "gpt-4o-mini",
  "instructions": "Answer travel questions in under 120 words and include the cancellation window.",
  "metadata": {
    "owner": "support-automation",
    "environment": "prod"
  },
  "status": "ready",
  "updated_at": "2025-05-10T08:14:03Z"
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `400 Bad Request` | The body is empty, contains an immutable field, or uses the wrong type for a patch value. | Send at least one mutable field and remove immutable values such as the resource `id` or `name` if the service rejects them. |
| `401 Unauthorized` | Credentials are missing, expired, or invalid. | Refresh the bearer token or API key and retry. |
| `404 Not Found` | The `agentId` does not exist in this project. | Verify the target project and agent identifier before patching. |
| `409 Conflict` | The agent is locked by another update or the new configuration conflicts with current runtime state. | Wait for the in-flight operation to finish, then retry the patch. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** None for prompt-agent patches.
- **Behavior differences from GA:** Legacy clients that cannot send `PATCH` can usually use `POST` plus `X-HTTP-Method-Override: PATCH`; the response shape is the same.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Patch only the fields that changed to keep payloads small and reduce accidental drift.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** PATCH is not automatically idempotent. If the connection drops after submission, read the resource before replaying the same patch.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` in `azure-ai-agents`](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching administration method. |
| JavaScript | [`AgentsClient` in `@azure/ai-agents`](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching administration method. |
| C# | [`AIProjectClient.AgentAdministrationClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.projects-readme?view=azure-dotnet) — use the matching agent administration method. |
| Java | [`azure-ai-agents`](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching administration method. |
