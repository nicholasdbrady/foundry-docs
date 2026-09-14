# Auth and RBAC failures (401 and 403)

## Symptom

Typical symptoms include one or more of the following:

- `401 Unauthorized`
- `403 Forbidden`
- `token expired`
- `insufficient privileges to complete the operation`
- `invalid audience`
- `The access token is from the wrong issuer or tenant`
- a managed identity call that works locally with developer credentials but fails after deployment

A quick smoke test against a Foundry project endpoint usually looks like this:

```bash
curl -i "https://YOUR_ACCOUNT_NAME.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME/agents?api-version=v1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

If the response is `401` or `403`, continue with the checks in this playbook.

## Probable Cause(s)

The most common causes are:

1. **Expired token** — the token was minted earlier and is now past `exp`.
2. **Wrong audience or scope** — the token was requested for the wrong resource. Foundry project data-plane calls expect `https://ai.azure.com/.default`.
3. **Missing RBAC role** — the principal authenticates successfully but does not have permission on the Foundry account or project.
4. **Wrong tenant** — the principal signed in to a different Microsoft Entra tenant than the tenant that owns the Foundry resource.
5. **Managed identity not configured** — the workload has no system-assigned or user-assigned identity, or the identity exists but has no role assignment.

## Validation Commands

### 1. Decode the token and inspect expiry, audience, and tenant

```bash
python - <<'PY2'
import base64, json, time

token = 'YOUR_TOKEN'
payload = token.split('.')[1]
payload += '=' * (-len(payload) % 4)
claims = json.loads(base64.urlsafe_b64decode(payload))
for key in ('aud', 'tid', 'appid', 'oid', 'exp', 'nbf'):
    print(f"{key}: {claims.get(key)}")
print('expires_in_seconds:', claims['exp'] - int(time.time()))
PY2
```

Expected values:

- `aud` = `https://ai.azure.com`
- `tid` = the tenant that owns `YOUR_SUBSCRIPTION_ID`
- `expires_in_seconds` is positive with enough headroom for the request duration

### 2. Verify the active subscription and tenant

```bash
az account show \
  --query '{subscription:id, tenant:tenantId, user:user.name}' \
  -o yaml
```

### 3. Find the principal object ID used by the request

**Signed-in user or service principal**

```bash
az ad signed-in-user show --query id -o tsv
```

If the request uses a service principal instead of an interactive user:

```bash
az ad sp list --display-name YOUR_APP_REGISTRATION_NAME \
  --query '[0].id' -o tsv
```

**User-assigned managed identity**

```bash
az identity show \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_MANAGED_IDENTITY_NAME \
  --query '{principalId:principalId, clientId:clientId, tenantId:tenantId}' \
  -o yaml
```

### 4. List role assignments at the Foundry account scope

```bash
az role assignment list \
  --assignee YOUR_PRINCIPAL_ID \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME" \
  -o table
```

### 5. Check whether the workload actually has a managed identity enabled

**App Service**

```bash
az webapp identity show \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME
```

**Container Apps**

```bash
az containerapp identity show \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME
```

**Azure Functions**

```bash
az functionapp identity show \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_FUNCTION_APP_NAME
```

## Resolution Steps

### Cause 1: Expired token

1. Request a fresh token immediately before the call.
2. Re-run the API request with the new token.
3. If the token lifetime is too short for long-lived clients, switch from cached shell tokens to a credential flow that automatically refreshes tokens.

Python automatic refresh pattern:

```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential,
    "https://ai.azure.com/.default",
)

client = OpenAI(
    base_url="https://YOUR_ACCOUNT_NAME.services.ai.azure.com/openai/v1/",
    api_key=token_provider,
)
```

### Cause 2: Wrong audience or scope

1. Request the token for `https://ai.azure.com/` for Foundry project data-plane calls.
2. If the call targets OpenAI-compatible model endpoints instead, request a token for `https://cognitiveservices.azure.com/` only when the endpoint documentation says so.
3. Confirm the decoded token `aud` claim matches the endpoint family being called.

Correct Foundry token request:

```bash
az account get-access-token --resource https://ai.azure.com/
```

Incorrect for project endpoints:

```bash
az account get-access-token --resource https://management.azure.com/
```

### Cause 3: Missing RBAC role

1. Decide which operation the principal must perform.
2. Grant the smallest role that satisfies that operation.
3. Wait for RBAC propagation, then retry.

Example role assignment:

```bash
az role assignment create \
  --assignee YOUR_PRINCIPAL_ID \
  --role "Foundry User" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME"
```

If the principal must create or update project resources such as agent definitions, evaluation assets, or connections, use a broader authoring role only when required:

```bash
az role assignment create \
  --assignee YOUR_PRINCIPAL_ID \
  --role "Foundry Project Manager" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME"
```

### Cause 4: Wrong tenant

1. Compare the token `tid` claim to `az account show --query tenantId`.
2. Sign in to the correct tenant.
3. Re-acquire the token after switching tenants.

```bash
az login --tenant YOUR_TENANT_ID
az account set --subscription YOUR_SUBSCRIPTION_ID
az account get-access-token --resource https://ai.azure.com/
```

If the workload uses a service principal, verify the app registration and service principal both exist in the same tenant as the Foundry account.

### Cause 5: Managed identity not configured

1. Enable a system-assigned or user-assigned managed identity on the compute host.
2. Confirm the identity has a principal ID.
3. Assign the correct Foundry role to that principal.
4. Restart the workload if the host caches identity configuration.

System-assigned identity example for App Service:

```bash
az webapp identity assign \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME
```

Then assign the role:

```bash
az role assignment create \
  --assignee YOUR_MANAGED_IDENTITY_PRINCIPAL_ID \
  --role "Foundry User" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME"
```

## Prevention Guidance

### Token refresh patterns

- Acquire tokens on demand instead of pasting static bearer tokens into configuration.
- Prefer `DefaultAzureCredential` or a managed identity in production so refresh is automatic.
- Refresh proactively before long-running upload, streaming, or polling operations.
- Treat `401` on a previously healthy client as a refresh signal first, not a permissions failure.

### Least-privilege role recommendations

| Scenario | Recommended role | Notes |
| --- | --- | --- |
| Call runtime APIs, list agents, create threads, create runs | `Foundry User` | Default role for application execution paths |
| Create or update agents, evaluation rules, and project-scoped assets | `Foundry Project Manager` | Use only for authoring or CI pipelines that need write access |
| Account-wide administration and quota changes | `Foundry Account Owner` or equivalent account-level admin role | Avoid for application identities |

### Operational guardrails

- Standardize one tenant per environment and document the tenant ID next to the subscription ID.
- Keep role assignments at the narrowest scope that still works.
- Add a startup probe that decodes a token and logs `aud`, `tid`, and remaining lifetime.
- Use environment-specific managed identities rather than reusing a developer principal in production.
