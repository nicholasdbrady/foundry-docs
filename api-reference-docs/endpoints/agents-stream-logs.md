# Stream agent run events

## 1. One-line purpose statement

**Purpose:** Open a server-sent events stream for a run so the client can receive live progress and output events.

## 2. When to use / when not to use

**Use this operation when:**
- You need incremental run status updates without polling.
- You want to render live tokens, tool calls, or lifecycle events in a client application.
- You are diagnosing a run and need the exact event order emitted by the service.

**Do not use this operation when:**
- Use `GET /agents/{agentId}/threads/{threadId}/runs/{runId}` when periodic polling is sufficient.
- Use the create-run operation when the run has not started yet.
- Do not treat the event stream as a paged history API; reconnect and resume only for recent events.

## 3. Method + path + required auth/headers

**HTTP method:** `GET`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/{agentId}/threads/{threadId}/runs/{runId}/events`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to read the target run and must keep the connection open for the lifetime of the stream.

**Required headers:**
- `Accept: text/event-stream`
- `Cache-Control: no-cache`
- `Foundry-Features: HostedAgents=V1Preview`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `agentId` | string | yes | The agent that owns the run. |
| `threadId` | string | yes | The thread that the run executed against. |
| `runId` | string | yes | The run to stream. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01` for this documented stream shape. |

None. This operation does not accept a request body.

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -N -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/agt_01JVQ6J8N6C6W7J0GJ3D2YH5RJ/threads/thread_01JVQAP5R7YB2P5Z8T91A0EJYM/runs/run_01JVQB2MWY9C9SQSHY8Q31V2W4/events?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: text/event-stream" \
  -H "Cache-Control: no-cache" \
  -H "Foundry-Features: HostedAgents=V1Preview"
```

Use `curl -N` or another client that does not buffer SSE output.

## 6. Minimal successful response example

```text
event: thread.run.created
data: {"event_id":"evt_01JVQBN3XRG4J8R3S4A7N7X2QK","type":"thread.run.created","run_id":"run_01JVQB2MWY9C9SQSHY8Q31V2W4","thread_id":"thread_01JVQAP5R7YB2P5Z8T91A0EJYM","created_at":"2025-05-10T09:19:20Z"}

```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | The event stream request is unauthenticated or the token expired before the stream opened. | Refresh credentials and reconnect with a fresh token or API key. |
| `404 Not Found` | The `agentId`, `threadId`, or `runId` does not exist in this project. | Verify that all identifiers belong to the same project and were not deleted. |
| `406 Not Acceptable` | The client did not send `Accept: text/event-stream`. | Set the `Accept` header exactly to `text/event-stream`. |
| `409 Conflict` | The run is not in a streamable state, such as already expired or not yet fully initialized. | Wait briefly and reconnect, or fall back to `GET .../runs/{runId}` for the latest terminal state. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** PREVIEW
- **Required feature flag or header:** `Foundry-Features: HostedAgents=V1Preview`
- **Region or cloud limitations:** Live event streaming might not be enabled in every sovereign or older regional stamp.
- **Behavior differences from GA:** Event names, heartbeat cadence, and resume semantics can change before GA.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Long-lived streams are subject to idle timeouts. Clients should expect occasional disconnects and reconnect when no heartbeat arrives.
- **Pagination:** None.
- **Ordering:** Events arrive in the order emitted by the service for a single connection.
- **Streaming:** Server-sent events (SSE).
- **Retries and idempotency notes:** Reconnect with backoff. If the client supports resume, send the last processed event ID when reopening the stream.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`AgentsClient` runtime operations](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme?view=azure-python) — use the matching thread or run helper. |
| JavaScript | [`AgentsClient` runtime operations](https://learn.microsoft.com/javascript/api/overview/azure/ai-agents-readme?view=azure-node-latest) — use the matching thread or run helper. |
| C# | [`PersistentAgentsClient`](https://learn.microsoft.com/dotnet/api/overview/azure/ai.agents.persistent-readme?view=azure-dotnet) — use the matching thread or run method. |
| Java | [`azure-ai-agents` runtime operations](https://learn.microsoft.com/java/api/overview/azure/ai-agents-readme?view=azure-java-stable) — use the matching thread or run method. |
