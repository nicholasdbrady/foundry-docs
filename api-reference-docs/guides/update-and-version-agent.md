# Update and version an agent safely

Time: 5-10 minutes.

This guide creates a new version, smoke-tests it, and rolls back cleanly if the new version regresses.

## Prerequisites

- `YOUR_PROJECT_ENDPOINT`
- A bearer token for `https://ai.azure.com/.default`
- An existing agent name
- For hosted agents, a working container image tag for the new version

## Happy path

### Step 1: Capture the current state

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
versions = list(client.agents.list_versions(agent_name="travel-agent"))
for version in versions:
    print(version.version, version.id)
```

Record the exact version or agent identifier that production is using before creating anything new.

### Step 2: Create the new version

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{
    "definition": {
      "kind": "hosted",
      "image": "YOUR_REGISTRY.azurecr.io/travel-agent:2025-05-01",
      "cpu": "1",
      "memory": "2Gi"
    }
  }'
```

**Python**

```python
from azure.ai.projects.models import HostedAgentDefinition, ProtocolVersionRecord, AgentProtocol

new_version = client.agents.create_version(
    agent_name="travel-agent",
    definition=HostedAgentDefinition(
        image="YOUR_REGISTRY.azurecr.io/travel-agent:2025-05-01",
        cpu="1",
        memory="2Gi",
        container_protocol_versions=[
            ProtocolVersionRecord(protocol=AgentProtocol.RESPONSES, version="v1")
        ],
    ),
)
print(new_version.version)
```

### Step 3: Start and smoke-test the new version

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_NEW_VERSION/containers/default:start?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{"min_replicas": 1, "max_replicas": 1}'
```

**Python**

```python
import requests
from azure.identity import DefaultAzureCredential

token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
requests.post(
    f"YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/{new_version.version}/containers/default:start?api-version=v1",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Foundry-Features": "HostedAgents=V1Preview",
    },
    json={"min_replicas": 1, "max_replicas": 1},
    timeout=120,
)
```

Run a single smoke prompt against the new version before switching production callers.

### Step 4: Roll back by switching the pinned version

Do not delete the previous version until the new version has passed real traffic validation.

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_NEW_VERSION/containers/default:stop?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Foundry-Features: HostedAgents=V1Preview"
```

**Python**

```python
import requests
from azure.identity import DefaultAzureCredential

token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
requests.post(
    f"YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/{new_version.version}/containers/default:stop?api-version=v1",
    headers={
        "Authorization": f"Bearer {token}",
        "Foundry-Features": "HostedAgents=V1Preview",
    },
    timeout=120,
)
```

Point callers back to the last known good version identifier instead of mutating the old version in place.

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| New version returns `AcrImageNotFound` | Wrong image tag | Rebuild or retag the image and create another version. |
| Version created but container never starts | Missing ACR permissions | Grant the project identity pull access to the registry. |
| Rollback is slow | Production callers use floating names | Pin the concrete version or agent identifier in callers. |
| Update changed scale but not behavior | Runtime update only | Create a fresh version for definition changes. |

## Exact endpoint reference links

- [`../task-map-v1.md#update-and-version-an-agent-safely`](../task-map-v1.md#update-and-version-an-agent-safely)
- `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
