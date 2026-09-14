# Get evaluation results

## 1. One-line purpose statement

**Purpose:** Retrieve aggregate and item-level evaluation results for a completed evaluation run.

## 2. When to use / when not to use

**Use this operation when:**
- You want the scored output for a run that has already completed.
- You need aggregate metrics for dashboards or release gates.
- You want to inspect individual rows to understand why an evaluator passed or failed.

**Do not use this operation when:**
- Use `POST /evaluations` when you need to start a new run rather than read an existing one.
- Use the evaluation get-status operation if you only need lifecycle state and not the scored result set.
- Do not expect complete results before the evaluation reaches a terminal state.

## 3. Method + path + required auth/headers

**HTTP method:** `GET`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/{evaluationId}/results`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to read evaluation results in the project.

**Required headers:**
- `Accept: application/json`
- `Foundry-Features: Evaluations=V1Preview` when the project has not enabled evaluations by default

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |
| `evaluationId` | string | yes | The evaluation identifier returned when the run was created. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |
| `top` | integer | no | Optional number of item-level rows to return per page. |
| `continuationToken` | string | no | Opaque cursor for the next page of item-level results. |

None. This operation does not accept a request body.

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X GET "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/evaluations/eval_01JVQCV4TF35D9Y3PHMAY4W5V8/results?api-version=2025-05-01&top=2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json" \
  -H "Foundry-Features: Evaluations=V1Preview"
```

## 6. Minimal successful response example

```json
{
  "evaluation_id": "eval_01JVQCV4TF35D9Y3PHMAY4W5V8",
  "status": "completed",
  "aggregate_metrics": {
    "coherence": {
      "average_score": 4.2,
      "pass_rate": 0.92
    }
  },
  "items": [
    {
      "item_id": "row-0001",
      "metrics": [
        {
          "name": "coherence",
          "score": 4.0,
          "label": "pass",
          "reason": "The answer follows a clear sequence and addresses the request directly."
        }
      ]
    },
    {
      "item_id": "row-0002",
      "metrics": [
        {
          "name": "coherence",
          "score": 2.0,
          "label": "fail",
          "reason": "The answer omits the refund timeline and mixes two unrelated cases."
        }
      ]
    }
  ],
  "has_more": false
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | Authentication is missing or invalid. | Send a fresh token or valid API key for the same project endpoint. |
| `404 Not Found` | The `evaluationId` does not exist in the project. | Verify the evaluation identifier and project endpoint. |
| `409 Conflict` | The evaluation has not completed or results are still being materialized. | Poll the evaluation status until it reaches a terminal state, then retry the results request. |
| `400 Bad Request` | The continuation token is malformed or incompatible with the current request. | Reuse the exact token from the previous page and keep the rest of the query unchanged. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** PREVIEW
- **Required feature flag or header:** `Foundry-Features: Evaluations=V1Preview`
- **Region or cloud limitations:** Region support depends on evaluator type and project configuration.
- **Behavior differences from GA:** Metric names, row-level payload detail, and pagination fields can change before GA.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Large result sets page through item-level rows. Aggregate metrics are usually returned on the first page.
- **Pagination:** Uses `top` and `continuationToken`.
- **Ordering:** Item rows are returned in dataset order unless otherwise noted by the service.
- **Streaming:** None.
- **Retries and idempotency notes:** GET is safe to retry. If a page fails, resume with the same continuation token instead of restarting the entire scan.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [Cloud evaluation SDK samples](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use `AIProjectClient.beta.evaluations`. |
| JavaScript | [Cloud evaluation SDK samples](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use `client.evaluations` with preview opt-in when required. |
| C# | [Cloud evaluation SDK guidance](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use the `AIProjectClient` evaluation helpers. |
| Java | [Cloud evaluation SDK guidance](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation) — use the `AIProjectClient` evaluation helpers. |
