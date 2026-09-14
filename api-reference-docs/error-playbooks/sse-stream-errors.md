# SSE streaming errors

## Symptom

Common streaming failures include:

- the connection closes before a terminal event arrives
- `thread.message.delta` never becomes `thread.message.completed`
- the client receives partial text and then hangs
- timeouts during long-running runs or responses
- missing events after reconnecting
- the client falls behind and stops processing events fast enough

A raw reproduction with `curl` is often the fastest way to separate a service issue from a client bug:

```bash
curl -N \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  "https://YOUR_ENDPOINT" \
  -d @request.json
```

## Probable Cause(s)

1. **Network interruption** — proxies, gateways, or client-side idle timeouts close the connection.
2. **Token or request limit reached** — the underlying run fails or expires before the stream finishes.
3. **Server timeout** — the request exceeds the endpoint's allowed execution window.
4. **Slow client event handling** — the client blocks while parsing or rendering, so the receive buffer backs up.
5. **Reconnect logic is incomplete** — the client reconnects but does not resume from the last known event or resource state.

## Validation Commands

### 1. Inspect the raw event stream

```bash
curl -N -D response-headers.txt \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  "https://YOUR_ENDPOINT" \
  -d @request.json
```

Look for these markers:

- `event:` lines
- `data:` lines
- any `id:` fields emitted by the server
- terminal events such as `thread.run.completed`, `response.completed`, `thread.run.failed`, or `error`

### 2. Check whether the underlying run completed even if the stream dropped

If the stream disconnects but the server created a run or response resource, poll that resource directly before retrying from scratch.

### 3. Check client timeout settings

Confirm that reverse proxies, HTTP clients, and load balancers have timeouts longer than the longest expected run.

## Resolution Steps

### Step 1: Buffer partial events correctly

An SSE event is complete only after a blank line. Do not try to parse each individual line as a standalone message.

### Step 2: Reconnect safely

1. Persist the last server-emitted `id:` field when present.
2. Reconnect with `Last-Event-ID` if the endpoint supports SSE replay.
3. If the endpoint does not emit replayable SSE IDs, resume by polling the run or response resource and continue from the last completed state.

### Step 3: Keep event processing non-blocking

- append incoming deltas to an in-memory buffer
- move rendering, database writes, and analytics to another worker or queue
- avoid synchronous logging on every token-sized delta

### Step 4: Handle partial completions explicitly

If a disconnect happens after some `delta` events but before a terminal event:

1. mark the stream as interrupted
2. preserve the accumulated partial text
3. query the run or response status
4. only replay or retry if the server-side resource is not already terminal

## Python SSE client example

This example parses events incrementally, tracks the last event ID, and keeps partial text if the stream is interrupted.

```python
import json
import requests


def iter_sse(url: str, headers: dict, payload: dict):
    last_event_id = None

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=300) as response:
        response.raise_for_status()

        event = {"event": None, "data": [], "id": None}
        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue

            line = raw_line.strip()
            if line == "":
                if event["data"]:
                    body = "\n".join(event["data"])
                    data = json.loads(body)
                    if event["id"]:
                        last_event_id = event["id"]
                    yield event["event"], data, last_event_id
                event = {"event": None, "data": [], "id": None}
                continue

            if line.startswith("event:"):
                event["event"] = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                event["data"].append(line.split(":", 1)[1].strip())
            elif line.startswith("id:"):
                event["id"] = line.split(":", 1)[1].strip()


def consume_stream(url, headers, payload):
    partial_text = []
    last_event_id = None

    try:
        for event_name, data, last_event_id in iter_sse(url, headers, payload):
            if event_name == "thread.message.delta":
                text = data.get("delta", {}).get("content", [{}])[0].get("text", {}).get("value", "")
                partial_text.append(text)
            elif event_name in {"thread.run.completed", "response.completed"}:
                return "".join(partial_text)
            elif event_name in {"thread.run.failed", "response.failed", "error"}:
                raise RuntimeError(data)
    except requests.RequestException:
        print("stream interrupted")
        print("last_event_id:", last_event_id)
        print("partial_text:", "".join(partial_text))
        raise
```

## JavaScript SSE client example

```javascript
async function streamSse(url, headers, body) {
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error("HTTP " + response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let lastEventId = null;
  let partialText = "";

  while (true) {
    const packet = await reader.read();
    if (packet.done) break;

    buffer += decoder.decode(packet.value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop();

    for (const chunk of chunks) {
      const event = { event: null, data: [], id: null };
      for (const line of chunk.split("\n")) {
        if (line.startsWith("event:")) event.event = line.slice(6).trim();
        if (line.startsWith("data:")) event.data.push(line.slice(5).trim());
        if (line.startsWith("id:")) event.id = line.slice(3).trim();
      }

      if (event.id) lastEventId = event.id;
      const payload = event.data.length ? JSON.parse(event.data.join("\n")) : null;

      if (event.event === "thread.message.delta") {
        partialText += payload?.delta?.content?.[0]?.text?.value ?? "";
      }
      if (event.event === "thread.run.completed" || event.event === "response.completed") {
        return { text: partialText, lastEventId };
      }
      if (event.event === "thread.run.failed" || event.event === "response.failed" || event.event === "error") {
        throw new Error(JSON.stringify(payload));
      }
    }
  }

  return { text: partialText, lastEventId };
}
```

## Event types and meanings

The following events are the most important ones to handle explicitly.

| Event type | Meaning | Recommended client action |
| --- | --- | --- |
| `thread.run.created` | Run resource was created | store run ID |
| `thread.run.queued` | Work is accepted but not yet executing | keep waiting |
| `thread.run.in_progress` | Model or tools are actively running | keep waiting |
| `thread.run.requires_action` | Tool outputs are required from the client | pause stream workflow and submit tool outputs |
| `thread.run.completed` | Run finished successfully | finalize output |
| `thread.run.failed` | Run ended with an error | surface the error and inspect run details |
| `thread.run.cancelled` | Run was cancelled | stop retrying the same stream |
| `thread.run.expired` | Run exceeded its allowed lifetime | recreate or redesign the workflow |
| `thread.run.incomplete` | Run ended without a complete result | preserve partial output and inspect status |
| `thread.message.created` | Message object exists | prepare output buffer |
| `thread.message.in_progress` | Message is being assembled | keep waiting |
| `thread.message.delta` | Partial message content arrived | append to output buffer |
| `thread.message.completed` | Message content is complete | mark final text ready |
| `thread.message.incomplete` | Message ended before completion | keep partial content and inspect run status |
| `thread.run.step.created` | A run step started | optionally show progress |
| `thread.run.step.delta` | Partial run-step detail arrived | update progress |
| `thread.run.step.completed` | Run step finished | continue |
| `thread.run.step.failed` | A specific step failed | inspect step diagnostics |
| `error` | Stream-level error event | stop and inspect payload |
| `done` | Stream terminator | close cleanly |
| `response.created` / `response.in_progress` / `response.completed` / `response.failed` | Equivalent lifecycle events for Responses API streams | handle the same way as run lifecycle events |

## Prevention Guidance

- Keep transport timeouts higher than the longest expected streamed run.
- Persist the last known server resource ID even if the network path is unstable.
- Treat `delta` events as partial data, not final output.
- Make event handling idempotent so reconnects do not duplicate downstream writes.
- Test under packet loss or forced disconnects before rolling streaming clients into production.
