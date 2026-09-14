# Runs

Runs execute an agent against a specific thread. A run reads the thread state, invokes configured tools when needed, and writes assistant output and tool results back to the thread.

## Run lifecycle

A run typically progresses through `queued`, `in_progress`, and a terminal state such as `completed`, `failed`, `cancelled`, or `expired`. Use polling for simple integrations or the events stream for incremental updates.

## Operations

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Create run | `POST /agents/{agentId}/threads/{threadId}/runs` | Start execution for a thread. |
| Retrieve run | `GET /agents/{agentId}/threads/{threadId}/runs/{runId}` | Return the current status of a run. |
| Cancel run | `POST /agents/{agentId}/threads/{threadId}/runs/{runId}/cancel` | Request cancellation for an in-progress run. |
| List runs | `GET /agents/{agentId}/threads/{threadId}/runs` | List runs created for a thread. |
| Stream run events | `GET /agents/{agentId}/threads/{threadId}/runs/{runId}/events` | Receive lifecycle and message events over SSE. |
