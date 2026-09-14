# API reference overview

This API reference describes the REST APIs for interacting with the Microsoft Foundry platform. REST APIs are usable via HTTP from any environment. Language-specific SDKs are available for Python, JavaScript, C#, and Java.

Use this page as the entry point for authentication, endpoint construction, versioning, preview headers, streaming, pagination, and error handling across the API surface.

## Authentication

Microsoft Foundry project APIs support two authentication patterns:

- **Bearer token** — Send `Authorization: Bearer YOUR_ACCESS_TOKEN`. For Microsoft Entra ID, request a token for the `https://ai.azure.com/.default` scope.
- **API key** — Send `api-key: YOUR_API_KEY`.

Store secrets outside source code. Use environment variables, a secret store, or managed identity where available.

```bash
export FOUNDRY_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
export FOUNDRY_API_KEY="YOUR_API_KEY"

curl "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01" \
  -H "Authorization: Bearer ${FOUNDRY_ACCESS_TOKEN}" \
  -H "api-key: ${FOUNDRY_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json"
```

Use one authentication method per request. Do not send both headers in production traffic unless an endpoint explicitly documents dual-header behavior.

## Base URL

The project-scoped base URL has the following form:

```text
https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME
```

- `YOUR_ENDPOINT` is the Foundry resource endpoint.
- `YOUR_PROJECT_NAME` is the project name.

Append the resource path and `api-version` query parameter to this base URL for each call.

## API versioning

Every request must include an `api-version` query parameter.

- **Stable version** — `api-version=2025-05-01`
- **Preview version** — `api-version=2025-05-01-preview`

Use the stable version for production workloads unless a required capability is available only in preview. Preview versions can add, rename, or remove behavior before GA.

```text
GET https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01
GET https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01-preview
```

## Preview features

Some preview operations also require an opt-in header in addition to a preview `api-version`.

```http
Foundry-Features: HostedAgents=V1Preview
```

| Feature family | Header |
| --- | --- |
| Hosted agents | `Foundry-Features: HostedAgents=V1Preview` |
| Agent endpoints | `Foundry-Features: AgentEndpoints=V1Preview` |
| Workflow agents | `Foundry-Features: WorkflowAgents=V1Preview` |
| Evaluations assets and rules | `Foundry-Features: Evaluations=V1Preview` |
| Skills | `Foundry-Features: Skills=V1Preview` |
| Toolboxes | `Foundry-Features: Toolboxes=V1Preview` |

When a preview operation fails unexpectedly, check the required header and version together. See the [feature flag and preview error playbook](./error-playbooks/feature-flag-errors.md).

## Request and response format

JSON is the default wire format.

- Send `Content-Type: application/json` on requests with a body.
- Send `Accept: application/json` for buffered JSON responses.
- Send `Accept: text/event-stream` for SSE streaming endpoints.

Unless an operation documents otherwise, request bodies and response bodies are UTF-8 encoded JSON objects.

## Debugging requests

The following headers are the most useful for correlation and troubleshooting:

- `x-request-id` — Service-generated request identifier. Capture this for support and incident investigation.
- `x-ms-client-request-id` — Client-supplied correlation ID. Send a unique value per request and log it with the corresponding response.
- Processing-time headers such as `Server-Timing` can appear on some operations and are useful for latency analysis when present.

In production systems, log the request URL, status code, `x-request-id`, and `x-ms-client-request-id` for every failed request and sampled successful requests.

## Rate limits

Limits can apply at more than one layer:

- **Per-resource limits** such as requests-per-minute, tokens-per-minute, or concurrency on a deployment or hosted runtime.
- **Per-subscription or per-region limits** for capacity-constrained preview or hosted features.

When a limit is exceeded, the service returns `429 Too Many Requests`.

- Honor the `Retry-After` header exactly when present.
- Use exponential backoff with jitter when `Retry-After` is absent.
- Reduce fan-out, queue background work, and separate interactive from batch traffic.

Rate limit telemetry can include `x-ratelimit-*` headers such as remaining request or token budget values. Treat those headers as advisory and design clients to succeed even when they are absent.

See the [throttling and retry playbook](./error-playbooks/throttling-retry.md).

## Error handling

Error responses use a standard envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "target": "field_name",
    "details": []
  }
}
```

| Status code | Meaning | Typical action |
| --- | --- | --- |
| `400 Bad Request` | Invalid syntax, missing field, or unsupported parameter combination | Fix the request shape before retrying |
| `401 Unauthorized` | Missing, expired, or invalid credentials | Refresh the token or key and retry |
| `403 Forbidden` | Authenticated but not authorized | Check RBAC, tenant, scope, or feature access |
| `404 Not Found` | Resource, route, or version not found | Verify the path, IDs, project, and API version |
| `409 Conflict` | Current resource state blocks the operation | Wait, serialize the workflow, or resolve the state conflict |
| `422 Unprocessable Entity` | The JSON is valid but semantically invalid | Correct the field values or object relationships |
| `429 Too Many Requests` | The request exceeded a service limit | Honor `Retry-After` and back off |
| `500 Internal Server Error` | Unexpected server-side failure | Retry with backoff and capture request IDs |
| `503 Service Unavailable` | Temporary service unavailability or capacity issue | Retry later and monitor regional health |

Related playbooks:

- [Auth and RBAC failures](./error-playbooks/auth-rbac-failures.md)
- [Payload and schema errors](./error-playbooks/payload-schema-errors.md)
- [Feature flag and preview operation errors](./error-playbooks/feature-flag-errors.md)
- [SSE streaming errors](./error-playbooks/sse-stream-errors.md)
- [Throttling and retry strategy](./error-playbooks/throttling-retry.md)

## Streaming (Server-Sent Events)

Some run and response operations support Server-Sent Events (SSE).

- Send `Accept: text/event-stream`.
- Keep the connection open until a terminal event or the `[DONE]` sentinel arrives.
- Parse events as blocks separated by a blank line, not line by line.

```text
event: thread.message.delta
data: {"id":"evt_123","delta":{"content":[{"type":"output_text","text":"Hello"}]}}

event: thread.message.completed
data: {"id":"msg_123","status":"completed"}

data: [DONE]
```

If a stream drops, preserve the last known run, thread, or response identifier. Reconnect only when the endpoint supports replay semantics; otherwise poll the underlying resource and resume from the latest durable state.

## Pagination

List endpoints can paginate with query parameters such as `top` and `skip`, or with continuation tokens depending on the operation family.

A typical list response looks like this:

```json
{
  "value": [
    {
      "id": "item_001",
      "name": "example"
    }
  ],
  "nextLink": "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents?api-version=2025-05-01&skip=50"
}
```

If `nextLink` is present, continue paging until it is absent. Do not assume every collection supports offset pagination or that page sizes remain constant across versions.

## SDKs

| Language | Package | Install |
| --- | --- | --- |
| Python | `azure-ai-projects` | `pip install azure-ai-projects` |
| JavaScript | `@azure/ai-projects` | `npm install @azure/ai-projects` |
| C# | `Azure.AI.Projects` | `dotnet add package Azure.AI.Projects` |
| Java | `azure-ai-projects` | Add `com.azure:azure-ai-projects` as a Maven dependency |

SDKs wrap the same project endpoint concepts described in this reference. For HTTP debugging or unsupported preview behavior, raw REST remains the lowest common denominator.

## Backwards compatibility

The stable API version is intended to evolve without unnecessary breaking changes.

**Breaking changes** include:

- removing a field, path, operation, or enum value
- changing a field type or semantic meaning
- making an optional field required
- introducing a new required header, query parameter, or authentication behavior
- tightening validation in a way that rejects previously valid requests

**Non-breaking changes** include:

- adding optional request or response fields
- adding new endpoints or resource types
- adding new enum values that existing clients can ignore safely
- clarifying validation messages, examples, or documentation

Clients should ignore unknown response properties, tolerate new enum values when possible, and pin the intended `api-version` explicitly.

## Resources

The following resource groups are the main entry points in the API surface.

| Resource group | Description | Reference |
| --- | --- | --- |
| Agents | Create, update, list, and version AI agents. | [Agents](./endpoints/agents-list.md) |
| Threads | Manage conversation threads that hold message history for agent execution. | [Threads](./endpoints/agents-create-thread.md) |
| Runs | Execute agent runs on threads and inspect run state. | [Runs](./endpoints/agents-create-run.md) |
| Messages | Read and write messages within a thread. | [Messages](./guides/create-and-run-agent.md) |
| Responses | Generate model responses through the Responses API. | [Responses](./endpoints/responses-create.md) |
| Evaluations | Create evaluation definitions, start runs, and inspect results. | [Evaluations](./endpoints/evaluations-create.md) |
| Connections | Manage and inspect external service connections used by tools and workflows. | [Connections](./guides/manage-connections.md) |
| Deployments | Manage model deployments and route traffic by deployment name. | [Deployments](./endpoints/deployments-create.md) |
| Models | List and inspect available models before deployment or invocation. | [Models](./guides/manage-deployments.md) |
| Files | Upload and manage files used by tools, vector stores, and evaluations. | [Files](./guides/configure-agent-tools.md) |

## Related pages

- [Create response](./endpoints/responses-create.md)
- [Create run](./endpoints/agents-create-run.md)
- [Create thread](./endpoints/agents-create-thread.md)
- [Create evaluation](./endpoints/evaluations-create.md)
- [Manage deployments](./guides/manage-deployments.md)
