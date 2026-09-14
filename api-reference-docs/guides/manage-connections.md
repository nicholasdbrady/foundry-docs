# Manage connections

Time: 5-10 minutes.

This guide validates and consumes project connections. The current public project data-plane spec exposes list, get, and credential retrieval. Provisioning a brand-new connection is usually handled in the portal, provisioning code, or SDK helpers outside this REST surface.

## Prerequisites

- `YOUR_PROJECT_ENDPOINT`
- A bearer token for `https://ai.azure.com/.default`
- At least one existing project connection

## Happy path

### Step 1: List connections

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/connections?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
connections = list(client.connections.list())
for connection in connections:
    print(connection.name, connection.connection_type)
```

### Step 2: Read one connection by name

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/connections/YOUR_CONNECTION_NAME?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
connection = client.connections.get(name="YOUR_CONNECTION_NAME")
print(connection.name)
```

### Step 3: Retrieve credentials only when needed

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/connections/YOUR_CONNECTION_NAME/getConnectionWithCredentials?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
credentialed = client.connections.get_with_credentials(name="YOUR_CONNECTION_NAME")
print(credentialed.name)
```

### Step 4: Validate the linked resource

If the connection targets Azure OpenAI, confirm the downstream deployment exists before wiring it into an agent.

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/deployments?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
for deployment in client.deployments.list():
    print(deployment.name)
```

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Connection is missing from the list | Wrong project or region | Verify the project endpoint and the connection scope. |
| Credentials endpoint is blocked | Caller lacks permission | Grant the caller access to the project connection. |
| Agent config stores raw secrets | Connection not being used correctly | Store only the connection name or identifier in the agent definition. |
| Linked model fails even though the connection exists | Target deployment missing | Validate the downstream deployment separately. |

## Exact endpoint reference links

- [`../task-map-v1.md#manage-connections-and-linked-resources`](../task-map-v1.md#manage-connections-and-linked-resources)
- `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
