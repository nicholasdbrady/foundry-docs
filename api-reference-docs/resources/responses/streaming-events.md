# Streaming events for responses

Streaming responses use server-sent events (SSE). When `stream` is `true` on `POST /responses`, the service sends a sequence of `event:` and `data:` frames over a `text/event-stream` connection until the response reaches a terminal state.

## Event format

Each SSE message contains an event name and a JSON payload:

```text
event: response.created
data: {"type":"response.created","response":{"id":"resp_123","status":"queued"}}

```

The server terminates each event with a blank line. Clients should parse the stream incrementally and preserve event order.

## Event sequence

A typical successful stream looks like this:

1. `response.created`
2. `response.in_progress`
3. `response.output_item.added`
4. One or more `response.content_part.delta`
5. `response.content_part.done`
6. `response.output_item.done`
7. `response.completed`

A failed stream ends with `response.failed` instead of `response.completed`.

## Event reference

### `response.created`

Sent after the response resource is created and assigned an ID.

```text
event: response.created
data: {"type":"response.created","response":{"id":"resp_01JX8VBRAVN7WJQG3Y2F8A0V2S","object":"response","status":"queued"}}

```

### `response.in_progress`

Sent when generation starts.

```text
event: response.in_progress
data: {"type":"response.in_progress","response":{"id":"resp_01JX8VBRAVN7WJQG3Y2F8A0V2S","status":"in_progress"}}

```

### `response.output_item.added`

Sent when a new output item is opened in the stream, such as an assistant message.

```text
event: response.output_item.added
data: {"type":"response.output_item.added","output_index":0,"item":{"id":"msg_01JX8VC0YB7BEEZAMX8VV3H9YQ","type":"message","role":"assistant"}}

```

### `response.content_part.delta`

Sent for incremental content tokens within the active output item.

```text
event: response.content_part.delta
data: {"type":"response.content_part.delta","output_index":0,"content_index":0,"delta":"The invoice total is $4,250.00"}

```

### `response.content_part.done`

Sent when a content part is complete.

```text
event: response.content_part.done
data: {"type":"response.content_part.done","output_index":0,"content_index":0,"part":{"type":"output_text","text":"The invoice total is $4,250.00 and payment is due on 2025-05-31."}}

```

### `response.output_item.done`

Sent when the active output item is complete.

```text
event: response.output_item.done
data: {"type":"response.output_item.done","output_index":0,"item":{"id":"msg_01JX8VC0YB7BEEZAMX8VV3H9YQ","type":"message","role":"assistant"}}

```

### `response.completed`

Sent when the overall response finishes successfully.

```text
event: response.completed
data: {"type":"response.completed","response":{"id":"resp_01JX8VBRAVN7WJQG3Y2F8A0V2S","status":"completed","usage":{"input_tokens":87,"output_tokens":19,"total_tokens":106}}}

```

### `response.failed`

Sent when the response ends in a terminal error state.

```text
event: response.failed
data: {"type":"response.failed","response":{"id":"resp_01JX8VBRAVN7WJQG3Y2F8A0V2S","status":"failed"},"error":{"code":"tool_execution_failed","message":"The requested file search index was unavailable."}}

```

## Client considerations

- Use the `Accept: text/event-stream` header for streaming requests.
- Treat SSE events as append-only state transitions for the response resource.
- Persist the `response.id` from `response.created` so the client can retrieve or cancel the response later.
- Handle `response.failed` as terminal and fall back to non-stream diagnostics when needed.
