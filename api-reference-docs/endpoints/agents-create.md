# Create agent

## 1. One-line purpose statement

**Purpose:** Create an agent definition in a Foundry project so the agent can be used for later thread runs.

## 2. When to use / when not to use

**Use this operation when:**
- You need a reusable agent with its own model, instructions, and optional tools.
- You want a stable agent identifier that multiple threads or applications can reference.
- You are provisioning an agent before creating threads or runs for end users.

**Do not use this operation when:**
- Use `GET /agents` when you only need to inspect existing agents.
- Use `PATCH /agents/{agentId}` when you need to change an existing agent instead of creating a second one.
- Use `POST /agents/{agentId}/threads` when the agent already exists and you only need a conversation thread.

## 3. Method + path + required auth/headers

**HTTP method:** `POST`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to create project-scoped agents.

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
| `api-version` | string | yes | Must be `2025-05-01` for the stable project API surface. |

### Request body fields

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Unique agent name within the project. |
| `model` | string | yes | Deployment name that backs the agent. |
| `instructions` | string | yes | System instructions applied to every run. |
| `description` | string | no | Human-readable summary shown in management experiences. |
| `tools` | array<object> | no | Tool descriptors such as `file_search`, `code_interpreter`, or function tools. |
| `metadata` | object | no | Application-defined tags for routing, ownership, or lifecycle tracking. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "travel-agent",
    "model": "gpt-4o-mini",
    "instructions": "Answer travel questions briefly and cite the booking policy when relevant."
  }'
```

Replace `gpt-4o-mini` with the deployment name that exists in the target project.

## 6. Minimal successful response example

```json
{
  "id": "agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ",
  "object": "agent",
  "name": "travel-agent",
  "description": "Answers travel planning questions.",
  "model": "gpt-4o-mini",
  "instructions": "Answer travel questions briefly and cite the booking policy when relevant.",
  "tools": [],
  "metadata": {
    "owner": "support-automation"
  },
  "status": "ready",
  "created_at": "2025-05-09T14:22:11Z"
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | The bearer token or API key is missing, expired, or scoped to the wrong audience. | Refresh credentials and use a token for `https://ai.azure.com/.default` or a valid project API key. |
| `400 Bad Request` | The request body is missing `name`, `model`, or `instructions`, or one field has the wrong type. | Compare the payload with the minimal example and correct the missing or invalid field. |
| `409 Conflict` | An agent with the same name already exists in the project. | Pick a different `name`, or call the update operation if you intended to modify the existing agent. |
| `404 Not Found` | The project endpoint or referenced deployment name does not exist in this project. | Verify the project URL, region, and deployment name before retrying. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** Hosted container-backed agent definitions might not be available in every sovereign cloud.
- **Behavior differences from GA:** If you create hosted or container-backed agents, some tenants still require `Foundry-Features: HostedAgents=V1Preview`; prompt agents do not.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** One model deployment can be attached per agent definition, and tool resources count toward the underlying project quotas.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** Creation is not inherently idempotent. If the client times out after submission, list agents by name before retrying to avoid duplicate resources.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` in `azure-ai-agents`](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching administration method. |
| JavaScript | [`AgentsClient` in `@azure/ai-agents`](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching administration method. |
| C# | [`AIProjectClient.AgentAdministrationClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.projects-readme?view=azure-dotnet) — use the matching agent administration method. |
| Java | [`azure-ai-agents`](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching administration method. |
