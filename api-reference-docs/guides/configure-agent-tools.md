# Configure agent tools

Time: 5-10 minutes.

This guide adds Code Interpreter, File Search, Azure AI Search, and OpenAPI-backed tools to an agent.

## Prerequisites

- `YOUR_PROJECT_ENDPOINT`
- `YOUR_OPENAI_ENDPOINT`
- A project agent that can be updated
- For Azure AI Search or OpenAPI tools, an existing project connection
- For File Search, at least one input file

## Happy path

### Step 1: Upload the file used by tools

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/files?api-version=v1"           -H "api-key: YOUR_API_KEY"           -F "purpose=assistants"           -F "file=@knowledge-base.pdf"
```

**Python**

```python
openai_client = client.get_openai_client()
uploaded = openai_client.files.create(
    file=open("knowledge-base.pdf", "rb"),
    purpose="assistants",
)
print(uploaded.id)
```

### Step 2: Create the vector store for File Search

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/vector_stores?api-version=v1"           -H "api-key: YOUR_API_KEY"           -H "Content-Type: application/json"           -d '{"name": "travel-kb"}'
```

**Python**

```python
vector_store = openai_client.vector_stores.create(name="travel-kb")
print(vector_store.id)
```

### Step 3: Attach the file to the vector store

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/vector_stores/YOUR_VECTOR_STORE_ID/files?api-version=v1"           -H "api-key: YOUR_API_KEY"           -H "Content-Type: application/json"           -d '{"file_id": "YOUR_FILE_ID"}'
```

**Python**

```python
openai_client.vector_stores.files.create(
    vector_store_id=vector_store.id,
    file_id=uploaded.id,
)
```

### Step 4: Resolve connection-backed tool dependencies

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/connections?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
for connection in client.connections.list():
    print(connection.name, connection.connection_type)
```

### Step 5: Update the agent definition with the tool list

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/agents/travel-agent?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -d '{
    "definition": {
      "kind": "prompt",
      "model": "YOUR_DEPLOYMENT_NAME",
      "instructions": "Use tools when they reduce hallucination.",
      "tools": [
        {"type": "code_interpreter"},
        {"type": "file_search"},
        {"type": "azure_ai_search", "connection_name": "YOUR_SEARCH_CONNECTION"},
        {"type": "openapi", "connection_name": "YOUR_OPENAPI_CONNECTION"}
      ],
      "tool_resources": {
        "file_search": {"vector_store_ids": ["YOUR_VECTOR_STORE_ID"]},
        "code_interpreter": {"file_ids": ["YOUR_FILE_ID"]}
      }
    }
  }'
```

**Python**

```python
updated = client.agents.create_version(
    agent_name="travel-agent",
    definition={
        "kind": "prompt",
        "model": "YOUR_DEPLOYMENT_NAME",
        "instructions": "Use tools when they reduce hallucination.",
        "tools": [
            {"type": "code_interpreter"},
            {"type": "file_search"},
            {"type": "azure_ai_search", "connection_name": "YOUR_SEARCH_CONNECTION"},
            {"type": "openapi", "connection_name": "YOUR_OPENAPI_CONNECTION"},
        ],
        "tool_resources": {
            "file_search": {"vector_store_ids": [vector_store.id]},
            "code_interpreter": {"file_ids": [uploaded.id]},
        },
    },
)
print(updated.version)
```

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| File Search returns nothing | File was uploaded but not attached to the vector store | Check `POST /vector_stores/{id}/files`. |
| Azure AI Search tool fails at runtime | Wrong connection name or credentials | Re-read the connection and validate its secret material. |
| Code Interpreter cannot read the file | File ID missing from `tool_resources` | Attach the same file ID to the Code Interpreter resource block. |
| Tool update appears to do nothing | Caller still uses an older version | Pin and verify the new version before testing. |

## Exact endpoint reference links

- [`../task-map-v1.md#configure-agent-tools`](../task-map-v1.md#configure-agent-tools)
- [`../task-map-v1.md#manage-connections-and-linked-resources`](../task-map-v1.md#manage-connections-and-linked-resources)
