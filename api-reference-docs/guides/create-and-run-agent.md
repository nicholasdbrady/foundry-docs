# Create and run an agent

Time: 5-10 minutes.

This guide creates an agent, starts the hosted runtime, creates the hosted-agent conversation equivalent of a thread, runs a prompt, and reads the result. Hosted agents use `conversations` plus `responses` instead of the Assistants `/threads` surface.

## Prerequisites

- A project endpoint: `https://YOUR_RESOURCE.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME`
- A bearer token for `https://ai.azure.com/.default`
- A model deployment name such as `YOUR_DEPLOYMENT_NAME`
- If the agent uses Azure AI Search or OpenAPI tools, an existing project connection
- For hosted container agents, an image in Azure Container Registry

## Happy path

### Step 1: Create the agent definition

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{
    "name": "travel-agent",
    "description": "Answers travel planning questions.",
    "definition": {
      "kind": "prompt",
      "model": "YOUR_DEPLOYMENT_NAME",
      "instructions": "Answer briefly and use tools when needed.",
      "tools": [
        {"type": "code_interpreter"},
        {"type": "file_search"}
      ]
    }
  }'
```

**Python**

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    endpoint="YOUR_PROJECT_ENDPOINT",
    credential=DefaultAzureCredential(),
    allow_preview=True,
)

agent = client.agents.create_version(
    agent_name="travel-agent",
    definition=PromptAgentDefinition(
        model="YOUR_DEPLOYMENT_NAME",
        instructions="Answer briefly and use tools when needed.",
    ),
)
print(agent.version)
```

<Note>
The current SDK guidance uses `create_version()` for new agent definitions. Keep the returned version identifier if the agent is container-backed.
</Note>

### Step 2: Start the hosted runtime when the agent is container-backed

Skip this step for prompt-only agents.

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default:start?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{"min_replicas": 1, "max_replicas": 1}'
```

**Python**

```python
import requests
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://ai.azure.com/.default").token
response = requests.post(
    "YOUR_PROJECT_ENDPOINT/agents/travel-agent/versions/YOUR_AGENT_VERSION/containers/default:start?api-version=v1",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Foundry-Features": "HostedAgents=V1Preview",
    },
    json={"min_replicas": 1, "max_replicas": 1},
    timeout=120,
)
print(response.status_code)
```

### Step 3: Create the conversation

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/endpoint/protocols/openai/conversations?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{}'
```

**Python**

```python
openai_client = client.get_openai_client(agent_name="travel-agent")
conversation = openai_client.conversations.create()
print(conversation.id)
```

### Step 4: Run the agent and read the result

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/endpoint/protocols/openai/responses?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{
    "input": "Find two Seattle hotels under $200.",
    "conversation": "YOUR_CONVERSATION_ID",
    "stream": false
  }'
```

**Python**

```python
response = openai_client.responses.create(
    input="Find two Seattle hotels under $200.",
    extra_body={"conversation": conversation.id},
)
print(response.output_text)
```

### Step 5: Reuse the same conversation on the next turn

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent/endpoint/protocols/openai/responses?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -H "Foundry-Features: HostedAgents=V1Preview"           -d '{
    "input": "Recommend one of those options.",
    "conversation": "YOUR_CONVERSATION_ID",
    "previous_response_id": "YOUR_RESPONSE_ID",
    "stream": false
  }'
```

**Python**

```python
follow_up = openai_client.responses.create(
    input="Recommend one of those options.",
    previous_response_id=response.id,
    extra_body={"conversation": conversation.id},
)
print(follow_up.output_text)
```

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `401` or `403` on agent endpoints | Wrong audience or missing preview header | Use a token for `https://ai.azure.com/.default` and add `Foundry-Features: HostedAgents=V1Preview`. |
| `404` on container start | Wrong `agent_version` | List versions first and use the returned version string exactly. |
| Response hangs | Container is not started or unhealthy | Check `GET .../containers/default` and open `:logstream`. |
| Tool call fails immediately | Missing file, vector store, or connection | Validate the tool resource before the run. |

## Exact endpoint reference links

- [`../task-map-v1.md#create-and-run-a-hosted-agent`](../task-map-v1.md#create-and-run-a-hosted-agent)
- `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
