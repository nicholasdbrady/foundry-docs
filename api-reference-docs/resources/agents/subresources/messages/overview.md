# Messages

Messages are the persisted items stored in a thread. A message can represent user input, assistant output, tool results, or other conversation content emitted during a run.

## Message model

A message contains a `role`, a `content` array, timestamps, and optional attachments or metadata. Runs append assistant and tool messages to the same thread that receives user messages.

## Operations

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Create message | `POST /agents/{agentId}/threads/{threadId}/messages` | Append a message to a thread. |
| Retrieve message | `GET /agents/{agentId}/threads/{threadId}/messages/{messageId}` | Return a specific thread message. |
| List messages | `GET /agents/{agentId}/threads/{threadId}/messages` | List messages stored in a thread. |
