# Threads

Threads are persisted conversation containers for an agent. A thread stores messages across turns so later runs can use the existing context instead of sending the full conversation again.

## When to use threads

- Create one thread per user conversation, case, or workflow instance.
- Store metadata that helps correlate the thread with application state.
- Reuse the same thread across multiple runs when context should accumulate over time.

## Operations

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Create thread | `POST /agents/{agentId}/threads` | Create a new thread for an agent. |
| Retrieve thread | `GET /agents/{agentId}/threads/{threadId}` | Return a specific thread. |
| Delete thread | `DELETE /agents/{agentId}/threads/{threadId}` | Delete a thread and its stored messages. |
| List threads | `GET /agents/{agentId}/threads` | List threads that belong to an agent. |
