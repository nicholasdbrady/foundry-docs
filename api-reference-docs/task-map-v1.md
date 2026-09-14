# Task map v1

This document maps common Microsoft Foundry developer tasks to the exact API endpoints used today.

## Base URLs used in this map

- `PROJECT_ENDPOINT` = `https://YOUR_RESOURCE.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME`
- `OPENAI_ENDPOINT` = `https://YOUR_OPENAI_RESOURCE.openai.azure.com/openai/v1`
- `ARM_ENDPOINT` = `https://management.azure.com/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/YOUR_ACCOUNT_NAME`

## 1. Create and run a hosted agent

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `PROJECT_ENDPOINT/agents?api-version=v1` | Create the agent record. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions?api-version=v1` | Create a hosted or prompt version explicitly. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default:start?api-version=v1` | Start the hosted container. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/endpoint/protocols/openai/conversations?api-version=v1` | Create the hosted-agent conversation context. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/endpoint/protocols/openai/responses?api-version=v1` | Run the agent and return output. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default:logstream?api-version=v1` | Stream container logs while testing. |
| `GET` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default?api-version=v1` | Check container state before invoking. |

### Typical call sequence

1. Create the agent or create a new version.
2. Start the container for the target version.
3. Create a conversation.
4. Send a `responses` request that references the conversation.
5. If the response stalls or fails, stream container logs and inspect container state.

### Dependency notes

- Hosted agent create, version, container start, and log streaming are preview operations. Send `Foundry-Features: HostedAgents=V1Preview` on those requests.
- Conversation and response calls depend on an active agent version.
- Tool-backed runs can add dependencies on `/connections`, `/files`, and `/vector_stores`.

### Reference pages

- Official REST reference: `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
- Internal guide: [`guides/create-and-run-agent.md`](guides/create-and-run-agent.md)

## 2. Update and version an agent safely

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `PROJECT_ENDPOINT/agents/{agent_name}?api-version=v1` | Read the current logical agent. |
| `GET` | `PROJECT_ENDPOINT/agents/{agent_name}/versions?api-version=v1` | List all versions before changing anything. |
| `GET` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}?api-version=v1` | Capture the last known good version definition. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}?api-version=v1` | Apply a versioned update when the definition changes. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions?api-version=v1` | Create a new explicit version. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default:start?api-version=v1` | Start the new hosted version. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default:update?api-version=v1` | Change replica limits on a running hosted version. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default:stop?api-version=v1` | Stop a bad version during rollback. |
| `DELETE` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}?api-version=v1` | Remove a failed or retired version. |

### Typical call sequence

1. Read the current agent and list its versions.
2. Save the version identifier used in production.
3. Create a new version.
4. Start and smoke-test the new version.
5. Switch callers to the new version identifier only after validation.
6. Roll back by reusing the previous version identifier or restarting the previous hosted container.

### Dependency notes

- Safe rollout depends on version pinning. Do not let production callers float to a new version until the new version passes a smoke test.
- Container replica changes are runtime-only; definition changes should create a fresh version.
- Deleting a version should be the last step, not the rollback mechanism.

### Reference pages

- Official REST reference: `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
- Internal guide: [`guides/update-and-version-agent.md`](guides/update-and-version-agent.md)

## 3. Stream and troubleshoot session logs (SSE)

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/endpoint/protocols/openai/responses?api-version=v1` | Start an SSE response stream with `"stream": true`. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default:logstream?api-version=v1` | Stream console or system logs from the hosted container. |
| `GET` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default?api-version=v1` | Check current container status and replica metadata. |
| `GET` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default/operations?api-version=v1` | List recent container operations. |
| `GET` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default/operations/{operation_id}?api-version=v1` | Inspect a specific failed start, stop, or update operation. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}/versions/{agent_version}/containers/default:start?api-version=v1` | Restart the container after a crash or timeout. |

### Typical call sequence

1. Send a `responses` request with `stream=true`.
2. If the stream drops or stalls, open `:logstream` in parallel.
3. Read container state and recent operations.
4. Restart the container if the failure is runtime-related.
5. Re-run the SSE request and confirm a clean completion.

### Dependency notes

- SSE response streaming and container log streaming solve different problems. Use the response stream for turn-level progress and `:logstream` for runtime diagnosis.
- If the service returns a session identifier, reuse it to reproduce the failure against the same sandbox.
- `kind=system` on `:logstream` is useful when console logs are empty.

### Reference pages

- Official REST reference: `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
- Internal guide: [`guides/stream-session-logs.md`](guides/stream-session-logs.md)

## 4. Create datasets and run evaluations

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `PATCH` | `PROJECT_ENDPOINT/datasets/{name}/versions/{version}?api-version=v1` | Create the dataset version shell. |
| `POST` | `PROJECT_ENDPOINT/datasets/{name}/versions/{version}/startPendingUpload?api-version=v1` | Start a pending upload and receive the upload target. |
| `POST` | `PROJECT_ENDPOINT/datasets/{name}/versions/{version}/credentials?api-version=v1` | Get storage credentials for dataset upload. |
| `POST` | `OPENAI_ENDPOINT/evals?api-version=v1` | Create the evaluation definition and graders. |
| `POST` | `OPENAI_ENDPOINT/evals/{eval_id}/runs?api-version=v1` | Start an evaluation run. |
| `GET` | `OPENAI_ENDPOINT/evals/{eval_id}/runs/{run_id}?api-version=v1` | Poll run status. |
| `GET` | `OPENAI_ENDPOINT/evals/{eval_id}/runs/{run_id}/output_items?api-version=v1` | Inspect row-level results. |

### Typical call sequence

1. Create the dataset version.
2. Start pending upload and upload the JSONL payload to the returned storage target.
3. Create the evaluation definition with `data_source_config` and `testing_criteria`.
4. Create an evaluation run that points at the dataset.
5. Poll until completion.
6. Read output items and aggregate metrics.

### Dependency notes

- Dataset upload is a prerequisite for evaluation runs that use project-managed assets.
- The evaluation definition and the run use different API surfaces: project data plane for datasets, OpenAI-compatible eval endpoints for graders and runs.
- Batch evaluation jobs often need a model deployment name in grader initialization parameters.

### Reference pages

- Official project REST reference: `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
- Internal guide: [`guides/create-datasets-run-evals.md`](guides/create-datasets-run-evals.md)

## 5. Manage deployments and model routing

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `OPENAI_ENDPOINT/models?api-version=v1` | List available model identifiers. |
| `GET` | `PROJECT_ENDPOINT/deployments?api-version=v1` | List project-visible deployments. |
| `GET` | `PROJECT_ENDPOINT/deployments/{name}?api-version=v1` | Inspect one deployment. |
| `PUT` | `ARM_ENDPOINT/deployments/{deployment_name}?api-version=2024-10-01` | Create or update a deployment. |
| `GET` | `ARM_ENDPOINT/deployments?api-version=2024-10-01` | List control-plane deployments for the account. |
| `GET` | `ARM_ENDPOINT/deployments/{deployment_name}?api-version=2024-10-01` | Read control-plane deployment state. |

### Typical call sequence

1. List models to choose a target model family.
2. Create or update the deployment with ARM.
3. Poll the ARM deployment until provisioning succeeds.
4. Confirm the project can see the deployment through `GET /deployments`.
5. Route traffic by using the deployment name in the agent definition or model field.
6. Scale by sending another `PUT` with updated SKU capacity.

### Dependency notes

- Deployment creation is a control-plane operation; project `/deployments` is read-only discovery.
- Routing is usually a naming problem, not a separate runtime endpoint. The agent or response payload must reference the deployment name selected here.
- Keep deployment creation and runtime rollout separate so scale or quota issues do not block existing traffic.

### Reference pages

- ARM deployment create/update: `https://learn.microsoft.com/en-us/rest/api/cognitiveservices/accountmanagement/deployments/create-or-update`
- Internal guide: [`guides/manage-deployments.md`](guides/manage-deployments.md)

## 6. Configure agent tools

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `OPENAI_ENDPOINT/files?api-version=v1` | Upload tool input files. |
| `POST` | `OPENAI_ENDPOINT/vector_stores?api-version=v1` | Create a vector store for file search. |
| `POST` | `OPENAI_ENDPOINT/vector_stores/{vector_store_id}/files?api-version=v1` | Attach a file to file search. |
| `POST` | `PROJECT_ENDPOINT/agents?api-version=v1` | Create an agent with tools. |
| `POST` | `PROJECT_ENDPOINT/agents/{agent_name}?api-version=v1` | Update tool definitions on an existing agent. |
| `GET` | `PROJECT_ENDPOINT/connections?api-version=v1` | Discover reusable connections for Azure AI Search, OpenAPI, or remote tools. |
| `POST` | `PROJECT_ENDPOINT/connections/{name}/getConnectionWithCredentials?api-version=v1` | Inspect a connection before wiring it into a tool. |

### Typical call sequence

1. Upload any files needed by Code Interpreter or File Search.
2. Create a vector store and attach the uploaded files if file search is required.
3. Resolve connection names and credentials for Azure AI Search or OpenAPI-backed tools.
4. Create or update the agent definition with the `tools` and `tool_resources` fields.
5. Run a smoke test that forces at least one tool call.

### Dependency notes

- File Search depends on files and vector stores; Azure AI Search and OpenAPI tools depend on project connections.
- Tools are defined on the agent version. Changing the tool list should create or return a new versioned agent definition.
- Uploaded files and vector stores live on the OpenAI-compatible data plane, not the project connection surface.

### Reference pages

- Official project REST reference: `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
- Internal guide: [`guides/configure-agent-tools.md`](guides/configure-agent-tools.md)

## 7. Manage connections and linked resources

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `PROJECT_ENDPOINT/connections?api-version=v1` | List project connections. |
| `GET` | `PROJECT_ENDPOINT/connections/{name}?api-version=v1` | Read one connection without secrets. |
| `POST` | `PROJECT_ENDPOINT/connections/{name}/getConnectionWithCredentials?api-version=v1` | Retrieve connection credentials when a workflow needs them. |
| `GET` | `PROJECT_ENDPOINT/deployments?api-version=v1` | Validate linked Azure OpenAI deployments referenced by a connection. |

### Typical call sequence

1. List the available connections.
2. Read the target connection by name.
3. Retrieve scoped credentials only when needed.
4. Validate the downstream linked resource, such as an Azure OpenAI deployment.
5. Store only the connection name or resource identifier in agent configuration.

### Dependency notes

- The current public project data-plane spec exposes list, get, and credential retrieval for connections. Connection create, update, and delete are typically handled by provisioning workflows, portal operations, or SDK helpers outside this REST surface.
- Avoid hard-coding raw secrets into agent definitions when a project connection already exists.

### Reference pages

- Official REST reference: `https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject/?view=rest-aifoundry-aiproject-2025-05-15-preview`
- Internal guide: [`guides/manage-connections.md`](guides/manage-connections.md)

## 8. Run batch evaluations on agent outputs

### Required endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `OPENAI_ENDPOINT/files?api-version=v1` | Upload the JSONL file that contains captured agent outputs. |
| `POST` | `OPENAI_ENDPOINT/evals?api-version=v1` | Create or reuse the evaluation definition. |
| `POST` | `OPENAI_ENDPOINT/evals/{eval_id}/runs?api-version=v1` | Start the batch evaluation run. |
| `GET` | `OPENAI_ENDPOINT/evals/{eval_id}/runs/{run_id}?api-version=v1` | Poll job status. |
| `GET` | `OPENAI_ENDPOINT/evals/{eval_id}/runs/{run_id}/output_items?api-version=v1` | Review row-level scores and failures. |
| `GET` | `OPENAI_ENDPOINT/evals/{eval_id}/runs/{run_id}/output_items/{output_item_id}?api-version=v1` | Drill into one failing sample. |

### Typical call sequence

1. Export agent outputs to JSONL.
2. Upload the JSONL file.
3. Create or reuse the evaluation definition.
4. Create the evaluation run that points at the uploaded outputs.
5. Poll until the run reaches a terminal state.
6. Read output items and triage failures.

### Dependency notes

- Batch evaluation is easiest when generation and evaluation are decoupled. Capture outputs first, then score them.
- The evaluation schema must match the fields available in the uploaded JSONL.
- Use row-level output items for debugging prompt regressions and grader misconfiguration.

### Reference pages

- OpenAI-compatible eval reference: `/api-sdk/reference-preview-latest`
- Internal guide: [`guides/batch-evaluations.md`](guides/batch-evaluations.md)
