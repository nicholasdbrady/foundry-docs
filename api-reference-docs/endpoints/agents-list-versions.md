# List agent versions

## 1. One-line purpose statement

**Purpose:** Return the version history for one agent so a caller can review rollout state and choose a specific version.

## 2. When to use / when not to use

**Use this operation when:**
- You want to see the published versions of an agent before rollout or rollback.
- You need the exact version string for a hosted or versioned agent operation.
- You are auditing how an agent definition changed over time.

**Do not use this operation when:**
- Use `GET /agents` when you need the current agent catalog rather than version history for one resource.
- Use `GET /agents/{agentId}` when you only need the current definition of the resource.
- Do not mutate production by guessing a version identifier; list versions first and select an exact value.

## 3. Method + path + required auth/headers

**HTTP method:** `GET`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}/versions`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to read the target agent and its version history.

**Required headers:**
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent whose versions should be listed. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |
| `top` | integer | no | Optional page size for long version histories. |
| `continuationToken` | string | no | Opaque cursor for the next page of versions. |

None. This operation does not accept a request body.

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ/versions?api-version=2025-05-01&top=2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## 6. Minimal successful response example

```json
{
  "data": [
    {
      "version": "3",
      "status": "ready",
      "model": "gpt-4o-mini",
      "created_at": "2025-05-10T08:14:03Z",
      "created_by": "support-bot-ci"
    },
    {
      "version": "2",
      "status": "ready",
      "model": "gpt-4o-mini",
      "created_at": "2025-05-08T16:31:18Z",
      "created_by": "support-bot-ci"
    }
  ],
  "has_more": false
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | Authentication is missing or invalid. | Send a fresh bearer token or valid project API key. |
| `404 Not Found` | The `agentId` does not exist in the project. | Verify the agent identifier and project endpoint before listing versions. |
| `400 Bad Request` | The page size or continuation token is invalid. | Use a small positive integer for `top` and replay the continuation token exactly as returned. |
| `429 Too Many Requests` | The version history is being scanned too aggressively. | Throttle list operations and reuse continuation tokens instead of restarting scans. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** Container-backed hosted-agent version fields can vary by cloud.
- **Behavior differences from GA:** Prompt-agent version history is stable. Hosted-agent tenants can emit extra rollout details and may still require `Foundry-Features: HostedAgents=V1Preview` for container-specific metadata.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Deep version histories page like any other collection; keep `top` modest for interactive UIs.
- **Pagination:** Uses `top` and `continuationToken`.
- **Ordering:** Most recent versions are typically returned first.
- **Streaming:** None.
- **Retries and idempotency notes:** GET is safe to retry. Reuse the latest continuation token after transient failures.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` in `azure-ai-agents`](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching administration method. |
| JavaScript | [`AgentsClient` in `@azure/ai-agents`](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching administration method. |
| C# | [`AIProjectClient.AgentAdministrationClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.projects-readme?view=azure-dotnet) — use the matching agent administration method. |
| Java | [`azure-ai-agents`](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching administration method. |
