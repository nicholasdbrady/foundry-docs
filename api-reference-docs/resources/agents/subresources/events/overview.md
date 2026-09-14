# Streaming events

The run events endpoint uses server-sent events (SSE) to stream lifecycle changes and incremental message output for a run.

## Endpoint

`GET /agents/{agentId}/threads/{threadId}/runs/{runId}/events`

Use `Accept: text/event-stream` and keep the connection open until a terminal event is received. A typical request looks like this:

```bash
curl -N "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/agents/YOUR_AGENT_ID/threads/YOUR_THREAD_ID/runs/YOUR_RUN_ID/events?api-version=2025-05-01"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Accept: text/event-stream"   -H "Cache-Control: no-cache"
```

## Event types

| Event | Description |
|-------|-------------|
| `thread.run.created` | Emitted when the run record is created. |
| `thread.run.in_progress` | Emitted when execution starts. |
| `thread.run.completed` | Emitted when the run reaches a successful terminal state. |
| `thread.run.failed` | Emitted when the run reaches a failed terminal state. |
| `thread.message.delta` | Emitted for incremental assistant message content. |
| `thread.message.completed` | Emitted when a message is fully assembled and stored. |
| `done` | Final sentinel event indicating the stream is complete. |

## SSE format

Each event is transmitted as standard SSE frames. The `event:` line identifies the event type. The `data:` line contains a JSON payload.

```text
event: thread.run.created
data: {"id":"evt_01JY53K8Y7B7K6B2V0B1T4PQ5M","type":"thread.run.created","run_id":"run_01JY51J5SABRHNBR4Q7T5M4N3T","thread_id":"thread_01JY50BR4X1SX6N54K9QGQKX7W","created_at":"2025-05-01T18:34:55Z"}

event: thread.message.delta
data: {"id":"evt_01JY53MB6K6X0WNT42YHHVNMVB","type":"thread.message.delta","message_id":"msg_01JY53M4RMGEEG70SR2E4S8JKE","delta":{"type":"text_delta","text":"Booking BK-4021 includes"}}

event: done
data: [DONE]
```

## Reconnection

SSE connections can close because of idle timeouts, network changes, or client restarts. Reconnect with exponential backoff and, when supported by the client, send the last processed event identifier in the `Last-Event-ID` header. Clients should treat terminal run events and `done` as completion signals and stop reconnecting after those events have been processed.
