# Stream session logs

Time: 5-10 minutes.

This guide opens an SSE response stream, tails hosted container logs in parallel, and shows the fastest checks when the stream disconnects.

## Prerequisites

- `YOUR_PROJECT_ENDPOINT`
- A bearer token for `https://ai.azure.com/.default`
- An active hosted agent version
- A shell that supports `curl -N`

## Happy path

### Step 1: Open the SSE response stream

**cURL**

```bash
curl -N -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/endpoint/protocols/openai/responses?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{
    "input": "Summarize the latest booking request.",
    "stream": true,
    "agent_session_id": "YOUR_SESSION_ID"
  }'
```

**Python**

```python
response = openai_client.responses.create(
    input="Summarize the latest booking request.",
    stream=True,
    extra_body={"agent_session_id": "YOUR_SESSION_ID"},
)
for event in response:
    print(event)
```

### Step 2: Tail the hosted container logs

**cURL**

```bash
curl -N -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default:logstream?api-version=v1&kind=console&tail=50"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Foundry-Features: HostedAgents=V1Preview"
```

**Python**

```python
import requests
from azure.identity import DefaultAzureCredential

token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
with requests.post(
    "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default:logstream?api-version=v1&kind=console&tail=50",
    headers={
        "Authorization": f"Bearer {token}",
        "Foundry-Features": "HostedAgents=V1Preview",
    },
    stream=True,
    timeout=120,
) as resp:
    for line in resp.iter_lines():
        if line:
            print(line.decode())
```

### Step 3: Inspect runtime state when the stream drops

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Foundry-Features: HostedAgents=V1Preview"
```

**Python**

```python
import requests
from azure.identity import DefaultAzureCredential

token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
container = requests.get(
    "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default?api-version=v1",
    headers={
        "Authorization": f"Bearer {token}",
        "Foundry-Features": "HostedAgents=V1Preview",
    },
    timeout=60,
).json()
print(container.get("status"))
```

### Step 4: Check recent operations and restart if needed

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default/operations?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Foundry-Features: HostedAgents=V1Preview"
```

**Python**

```python
import requests
from azure.identity import DefaultAzureCredential

token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
operations = requests.get(
    "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default/operations?api-version=v1",
    headers={
        "Authorization": f"Bearer {token}",
        "Foundry-Features": "HostedAgents=V1Preview",
    },
    timeout=60,
).json()
for operation in operations.get("data", []):
    print(operation.get("id"), operation.get("status"))
```

If the container is unhealthy, restart it with `POST ...:start` and retry the SSE request.

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| SSE stream closes immediately | Container crash on first token | Open `:logstream` and read the first failing stack trace. |
| No console output | Runtime problem is in platform events | Retry `:logstream?kind=system`. |
| Repeated disconnect after 60 seconds | Idle timeout or no output | Emit heartbeat or diagnostic output from the agent during long operations. |
| Session-specific issue cannot be reproduced | New sandbox on retry | Reuse the same `agent_session_id`. |

## Exact endpoint reference links

- [`../task-map-v1.md#stream-and-troubleshoot-session-logs-sse`](../task-map-v1.md#stream-and-troubleshoot-session-logs-sse)
- `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
