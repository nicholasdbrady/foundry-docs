# Create evaluation

## 1. One-line purpose statement

**Purpose:** Create an evaluation run definition so the service can score model or agent outputs against a dataset or target.

## 2. When to use / when not to use

**Use this operation when:**
- You want to score prompts, responses, or agent behavior at scale in the cloud.
- You need an asynchronous evaluation job that can be polled and reviewed later.
- You are integrating quality or safety checks into a release workflow.

**Do not use this operation when:**
- Use regular model inference or agent run APIs when you need one live answer instead of scored evaluation output.
- Use `GET /evaluations/{evaluationId}/results` after the job exists and you only need the results.
- Do not start an evaluation before confirming the dataset schema and evaluator mappings are valid.

## 3. Method + path + required auth/headers

**HTTP method:** `POST`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to create evaluation runs in the project.

**Required headers:**
- `Content-Type: application/json`
- `Accept: application/json`
- `Foundry-Features: Evaluations=V1Preview` when the project has not enabled evaluations by default

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01` for this reference surface. |

### Request body fields

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `display_name` | string | yes | Friendly name for the evaluation run. |
| `data_source_config` | object | yes | Input data configuration, such as a dataset ID or inline file content plus schema mapping. |
| `evaluators` | array<object> | yes | One or more evaluators and their field mappings. |
| `target` | object | no | Target model or agent definition when the service must generate outputs before evaluating them. |
| `tags` | object | no | Application-defined metadata such as environment or release train. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Foundry-Features: Evaluations=V1Preview" \
  -d '{
    "display_name": "refund-coherence-eval",
    "data_source_config": {
      "type": "file_id",
      "file_id": "file_01JVQCB4H8WX7Z43JZ8WDTK4K1"
    },
    "evaluators": [
      {
        "name": "coherence",
        "data_mapping": {
          "query": "{{item.query}}",
          "response": "{{item.response}}"
        }
      }
    ]
  }'
```

## 6. Minimal successful response example

```json
{
  "id": "eval_01JVQCV4TF35D9Y3PHMAY4W5V8",
  "object": "evaluation",
  "display_name": "refund-coherence-eval",
  "status": "queued",
  "created_at": "2025-05-10T10:21:07Z",
  "tags": {},
  "target": null
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `400 Bad Request` | The data source config, evaluator mapping, or required fields are invalid. | Validate the dataset schema, use the required evaluator inputs, and confirm each mapping references an existing field. |
| `401 Unauthorized` | Authentication is missing or invalid. | Use a fresh bearer token or valid project API key. |
| `404 Not Found` | The referenced dataset, uploaded file, model deployment, or agent target does not exist. | Verify every referenced resource ID in the same project before submitting the evaluation. |
| `409 Conflict` | The service rejected the evaluation because the requested target or dataset is locked or another conflicting operation is in progress. | Wait for the conflicting operation to finish and resubmit the evaluation. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** PREVIEW
- **Required feature flag or header:** `Foundry-Features: Evaluations=V1Preview`
- **Region or cloud limitations:** Evaluation support can vary by region, evaluator type, and cloud.
- **Behavior differences from GA:** Field names, evaluator availability, and result payload details can change before GA.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Dataset size, evaluator count, and concurrent evaluation-run quotas are project-scoped and can vary by region.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** None.
- **Retries and idempotency notes:** Creation is asynchronous. If the request times out before an ID is returned, check recent evaluations before replaying the same job.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [Cloud evaluation SDK samples](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use `AIProjectClient.beta.evaluations`. |
| JavaScript | [Cloud evaluation SDK samples](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use `client.evaluations` with preview opt-in when required. |
| C# | [Cloud evaluation SDK guidance](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use the `AIProjectClient` evaluation helpers. |
| Java | [Cloud evaluation SDK guidance](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use the `AIProjectClient` evaluation helpers. |
