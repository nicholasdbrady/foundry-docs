# Create response

## 1. One-line purpose statement

**Purpose:** Create a model response in a Foundry project by sending input to a deployed model.

## 2. When to use / when not to use

**Use this operation when:**
- You need a single request-response interaction against a model deployment.
- You want to use the Responses API shape for text, tool, or multimodal generation.
- You need a buffered result or want to turn on streaming with a single request flag.

**Do not use this operation when:**
- Use an agent thread run when you need persistent agent instructions, tools, and thread state.
- Use `GET /responses/{responseId}` or an events endpoint if you already have a response ID and only need status or stream history.
- Do not send the model catalog name when the project expects a deployment name.

## 3. Method + path + required auth/headers

**HTTP method:** `POST`

**Path:** `https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/responses`

**Required authentication:**
- `Authorization: Bearer YOUR_ACCESS_TOKEN` **or** `api-key: YOUR_API_KEY`
- The caller must have permission to invoke the target deployment in the project.

**Required headers:**
- `Content-Type: application/json`
- `Accept: application/json`

## 4. Required query parameters and path parameters

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | string | yes | The Foundry project name segment in the project endpoint URL. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | Must be `2025-05-01`. |

### Request body fields

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `model` | string | yes | Deployment name of the model to invoke. |
| `input` | string | array<object> | yes | User input payload. A string is the smallest valid text request. |
| `instructions` | string | no | Additional system-level instructions for this response. |
| `stream` | boolean | no | Set to `true` to receive streamed events instead of a buffered JSON response. |
| `max_output_tokens` | integer | no | Upper bound on generated output tokens. |
| `metadata` | object | no | Application-defined tags or routing metadata. |

## 5. Minimal request example (copy-run-edit ready, using cURL)

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/responses?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "model": "gpt-4.1-mini",
    "input": "Summarize the latest refund request in one paragraph.",
    "stream": false
  }'
```

Use the deployment name from the project, not the model catalog family name, in the `model` field.

## 6. Minimal successful response example

```json
{
  "id": "resp_01JVQCD3Q37MFJS1BBX1CY8Z49",
  "object": "response",
  "created_at": "2025-05-10T10:02:51Z",
  "status": "completed",
  "model": "gpt-4.1-mini",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "The customer asked for a refund because the hotel double charged the booking and wants confirmation that the charge will be reversed within five business days."
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 24,
    "output_tokens": 34,
    "total_tokens": 58
  }
}
```

## 7. Common error responses with likely causes and fixes

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `400 Bad Request` | The `model` or `input` field is missing, or the payload shape is invalid. | Supply a deployment name in `model` and a valid `input` value that matches the Responses API schema. |
| `401 Unauthorized` | Authentication headers are missing or invalid. | Refresh the token or API key and retry. |
| `404 Not Found` | The requested deployment name is not visible in the project. | Verify that the deployment exists and that the request targets the correct project endpoint. |
| `429 Too Many Requests` | The deployment quota or rate limit has been exceeded. | Retry with exponential backoff, reduce concurrency, or scale the deployment. |

## 8. Preview/feature-flag notes (if applicable)

- **Availability:** GA
- **Required feature flag or header:** `NONE`
- **Region or cloud limitations:** Model availability still depends on region and project configuration.
- **Behavior differences from GA:** If `stream` is set to `true`, the operation returns an event stream instead of the buffered JSON example shown here.

## 9. Limits, pagination, and streaming behavior notes

- **Limits:** Token limits and supported modalities depend on the selected deployment.
- **Pagination:** None.
- **Ordering:** Not applicable.
- **Streaming:** Optional SSE when `stream=true`.
- **Retries and idempotency notes:** For safe retries, use an idempotency strategy in the client application and avoid replaying the same prompt blindly after a timeout.

## 10. SDK parity links (Python/JavaScript/C#/Java)

| Language | SDK parity |
| --- | --- |
| Python | [`openai.OpenAI().responses.create()` with a Foundry project endpoint](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses#use-the-responses-api-to-generate-text). |
| JavaScript | [`client.responses.create()` in the OpenAI JavaScript SDK](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses#use-the-responses-api-to-generate-text). |
| C# | [`ResponseClient` or equivalent OpenAI .NET responses helper](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses#use-the-responses-api-to-generate-text). |
| Java | [`responses().create()` in the OpenAI Java SDK against the project route](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses#use-the-responses-api-to-generate-text). |
