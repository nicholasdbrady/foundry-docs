# Manage deployments

Time: 5-10 minutes.

This guide lists models, creates or updates a deployment, confirms project visibility, and adjusts capacity.

## Prerequisites

- `YOUR_OPENAI_ENDPOINT`
- `YOUR_PROJECT_ENDPOINT`
- `YOUR_SUBSCRIPTION_ID`, `YOUR_RESOURCE_GROUP`, and `YOUR_ACCOUNT_NAME`
- Azure RBAC permission to create Cognitive Services deployments

## Happy path

### Step 1: List model identifiers

**cURL**

```bash
curl "YOUR_OPENAI_ENDPOINT/models?api-version=v1"           -H "api-key: YOUR_API_KEY"
```

**Python**

```python
openai_client = client.get_openai_client()
models = openai_client.models.list()
for model in models.data[:5]:
    print(model.id)
```

### Step 2: Create or update the deployment

**cURL**

```bash
curl -X PUT "https://management.azure.com/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME/deployments/YOUR_DEPLOYMENT_NAME?api-version=2024-10-01"           -H "Authorization: Bearer YOUR_ARM_TOKEN"           -H "Content-Type: application/json"           -d '{
    "sku": {"name": "Standard", "capacity": 10},
    "properties": {
      "model": {
        "format": "OpenAI",
        "name": "gpt-4.1",
        "version": "2025-04-14"
      }
    }
  }'
```

**Python**

```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

mgmt = CognitiveServicesManagementClient(
    credential=DefaultAzureCredential(),
    subscription_id="YOUR_SUBSCRIPTION_ID",
)

deployment = mgmt.deployments.begin_create_or_update(
    resource_group_name="YOUR_RESOURCE_GROUP",
    account_name="YOUR_ACCOUNT_NAME",
    deployment_name="YOUR_DEPLOYMENT_NAME",
    deployment={
        "sku": {"name": "Standard", "capacity": 10},
        "properties": {
            "model": {
                "format": "OpenAI",
                "name": "gpt-4.1",
                "version": "2025-04-14",
            }
        },
    },
).result()
print(deployment.name)
```

### Step 3: Confirm the project can see the deployment

**cURL**

```bash
curl "YOUR_PROJECT_ENDPOINT/deployments?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
deployments = client.deployments.list()
for deployment in deployments:
    print(deployment.name)
```

### Step 4: Route traffic by deployment name

Use `YOUR_DEPLOYMENT_NAME` in the agent definition or runtime `model` field. Keep routing strings stable so rollback is just a configuration switch.

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| ARM `409` or quota error | Insufficient regional quota | Lower capacity or request quota before retrying. |
| Project `GET /deployments` does not show the deployment yet | Control plane not finished | Poll the ARM deployment until `Succeeded`. |
| Runtime `model not found` | Wrong routing string | Use the deployed name, not the model family name. |
| Capacity change has no visible effect | Old SKU values cached in callers | Re-read the deployment after the ARM operation completes. |

## Exact endpoint reference links

- [`../task-map-v1.md#manage-deployments-and-model-routing`](../task-map-v1.md#manage-deployments-and-model-routing)
- `https://learn.microsoft.com/en-us/rest/api/cognitiveservices/accountmanagement/deployments/create-or-update`
