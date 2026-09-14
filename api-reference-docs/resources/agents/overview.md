# Agents

Agents are reusable project-scoped resources that combine instructions, a model deployment, and optional tools for multi-turn execution. An agent can own conversation threads, execute runs against those threads, and expose version history for controlled updates.

## Capabilities

- Tool-enabled conversations with persisted thread state.
- Code Interpreter for data transformation, calculation, and file generation tasks.
- File Search for retrieval over attached files and vector-store-backed content.
- Azure AI Search tools for grounded retrieval through project connections.
- OpenAPI tools for invoking external APIs through connected specifications.

## Related guides

- [Create and run an agent](../../guides/create-and-run-agent.md)
- [Update and version an agent](../../guides/update-and-version-agent.md)
- [Configure agent tools](../../guides/configure-agent-tools.md)

## Resource model

- **Agent**: reusable definition containing model, instructions, tools, and metadata.
- **Thread**: persisted conversation container scoped to an agent.
- **Run**: execution of an agent against a thread.
- **Message**: individual user, assistant, or tool item stored in a thread.
- **Version**: point-in-time snapshot of an agent definition.
- **Event stream**: server-sent events (SSE) emitted while a run is executing.

## Operations

### Agents

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Create agent | `POST /agents` | Create a new agent definition in a project. |
| Retrieve agent | `GET /agents/{agentId}` | Return the current definition for an agent. |
| Update agent | `PATCH /agents/{agentId}` | Modify mutable fields on an existing agent. |
| Delete agent | `DELETE /agents/{agentId}` | Delete an agent definition. |
| List agents | `GET /agents` | List agents in a project. |

### Threads

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Create thread | `POST /agents/{agentId}/threads` | Create a conversation thread for an agent. |
| Retrieve thread | `GET /agents/{agentId}/threads/{threadId}` | Return a specific thread. |
| Delete thread | `DELETE /agents/{agentId}/threads/{threadId}` | Delete a thread and its messages. |
| List threads | `GET /agents/{agentId}/threads` | List threads that belong to an agent. |

### Runs

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Create run | `POST /agents/{agentId}/threads/{threadId}/runs` | Start execution for a thread. |
| Retrieve run | `GET /agents/{agentId}/threads/{threadId}/runs/{runId}` | Return the current status of a run. |
| Cancel run | `POST /agents/{agentId}/threads/{threadId}/runs/{runId}/cancel` | Request cancellation for an in-progress run. |
| List runs | `GET /agents/{agentId}/threads/{threadId}/runs` | List runs created for a thread. |

### Messages

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Create message | `POST /agents/{agentId}/threads/{threadId}/messages` | Append a message to a thread. |
| Retrieve message | `GET /agents/{agentId}/threads/{threadId}/messages/{messageId}` | Return a single thread message. |
| List messages | `GET /agents/{agentId}/threads/{threadId}/messages` | List messages in a thread. |

### Versions

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| List versions | `GET /agents/{agentId}/versions` | List version history for an agent. |
| Retrieve version | `GET /agents/{agentId}/versions/{versionId}` | Return a specific agent version. |

### Streaming events

| Operation | Method and path | Description |
|-----------|-----------------|-------------|
| Run events stream | `GET /agents/{agentId}/threads/{threadId}/runs/{runId}/events` | Open an SSE stream for run lifecycle and message events. |
