# Feature flag and preview operation errors

## Symptom

Typical symptoms include:

- `400 Bad Request` on a preview-only operation
- `404 Not Found` or `operation not found` when the path is correct
- `preview_feature_required`
- different behavior between environments even though the request body matches
- a preview SDK call that succeeds locally but fails in CI or another region

A minimal reproduction usually looks like this:

```bash
curl -i "https://YOUR_ACCOUNT_NAME.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME/evaluationrules/YOUR_RULE?api-version=v1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

If the operation is in preview, the request can fail even when authentication is valid.

## Probable Cause(s)

1. **Missing preview header** — the endpoint requires an opt-in header such as `Foundry-Features` or `aoai-evals`.
2. **Wrong `api-version`** — the path exists only in a preview API version or has moved between preview and GA.
3. **Feature not enabled in the selected region** — the operation is documented but not available where the resource is deployed.
4. **SDK generation mismatch** — the SDK call targets a preview operation group but the installed package version does not send the required header or path.

## Validation Commands

### 1. Check the failing response headers and service error code

```bash
curl -sS -D response-headers.txt \
  "https://YOUR_ENDPOINT" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -o response-body.json

cat response-headers.txt
cat response-body.json
```

Look for:

- `x-ms-error-code`
- `preview_feature_required`
- `UnsupportedApiVersion`
- `NoRegisteredProviderFound`
- `OperationNotAllowed`

### 2. Confirm the exact API version in the request URL

```bash
printf '%s\n' "https://YOUR_ENDPOINT" | sed 's/[?&]/\n/g'
```

### 3. Verify the installed SDK version

**Python**

```bash
python -m pip show azure-ai-projects
```

**JavaScript**

```bash
npm ls @azure/ai-projects
```

**.NET**

```bash
dotnet list package | grep Azure.AI.Projects
```

**Java**

```bash
mvn dependency:tree | grep azure-ai-projects
```

### 4. Verify region and resource details

```bash
az resource show \
  --ids "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME" \
  --query '{name:name, location:location, kind:kind}' \
  -o yaml
```

## Resolution Steps

### Cause 1: Missing preview header

Add the required preview header and retry the same request unchanged.

Example for a preview evaluation rules call:

```bash
curl -X PUT \
  "https://YOUR_ACCOUNT_NAME.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME/evaluationrules/YOUR_RULE?api-version=v1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Foundry-Features: Evaluations=V1Preview" \
  -d @evaluation-rule.json
```

Example for OpenAI evaluations preview:

```bash
curl -X GET \
  "https://YOUR_OPENAI_RESOURCE.openai.azure.com/openai/v1/evals?api-version=preview" \
  -H "api-key: YOUR_API_KEY" \
  -H "aoai-evals: preview"
```

### Cause 2: Wrong `api-version`

1. Replace the version in the URL with the version documented for the operation.
2. Re-run the same payload.
3. If the feature recently moved to GA, remove the old preview query parameter and keep the preview header only when still documented.

Common corrections:

- `api-version=v1` for stable Foundry project APIs
- `api-version=2025-11-15-preview` for current project preview reference pages
- `api-version=preview` for OpenAI v1 preview-only add-ons such as `/openai/v1/evals`

### Cause 3: Feature not enabled in the region

1. Check whether the feature is region-limited.
2. If the feature is preview and region-gated, test against a supported region.
3. Move only the affected workload if migrating the whole project is unnecessary.

Example diagnostic workflow:

```bash
az resource show \
  --ids "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME" \
  --query location -o tsv
```

Then compare that location with the feature's availability page before retrying.

### Cause 4: SDK generation mismatch

1. Upgrade the SDK to a version that documents the preview surface.
2. If the SDK still lacks the feature flag switch, call the REST endpoint directly.
3. Pin preview package versions in CI so environments stay aligned.

## Current preview headers and required operations

The following headers are the most common current opt-ins for Foundry preview operations.

| Header | Example value | Operations that require it |
| --- | --- | --- |
| `Foundry-Features` | `HostedAgents=V1Preview` | Hosted agent dedicated endpoints, hosted session lifecycle calls, hosted file and session operations |
| `Foundry-Features` | `AgentEndpoints=V1Preview` | Agent endpoint upgrade and legacy-agent inspection flows that use dedicated agent endpoints |
| `Foundry-Features` | `WorkflowAgents=V1Preview` | Workflow agent create and update operations on `/agents` when `definition.kind=workflow` |
| `Foundry-Features` | `Evaluations=V1Preview` | Evaluation rules create, update, and persisted preview evaluation assets |
| `Foundry-Features` | `Skills=V1Preview` | Skills CRUD operations |
| `Foundry-Features` | `Toolboxes=V1Preview` | Toolbox endpoint and toolbox session calls |
| `aoai-evals` | `preview` | `/openai/v1/evals` and nested evaluation run endpoints |
| `aoai-copy-ft-checkpoints` | `preview` | Fine-tuning checkpoint copy operations |

When troubleshooting, start with the exact operation path instead of guessing. If the docs list a preview header for that path, send it on every request for that operation family.

## Prevention Guidance

- Keep a request fixture for each preview workflow with the exact header and `api-version` that made it work.
- Pin SDK versions in lockfiles and deployment manifests.
- Add a preflight integration test that exercises one preview call per feature family.
- Prefer one code path per operation family. Mixing raw REST, old SDKs, and new SDKs often causes silent header drift.
- Record region requirements next to the feature flag in deployment documentation.
