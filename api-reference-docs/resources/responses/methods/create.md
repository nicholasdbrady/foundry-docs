# Create a response

Create a model response directly from a Foundry project endpoint.

## Request

`POST /responses`

### Path parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| None. |  |  | This operation uses the project-scoped base URL. |

### Query parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | Required | API version. Use `2025-05-01`. |

### Headers

| Header | Type | Required | Description |
| --- | --- | --- | --- |
| `Authorization` | string | Conditional | Bearer access token. Use this header or `api-key`. |
| `api-key` | string | Conditional | Project API key. Use this header or `Authorization`. |
| `Content-Type` | string | Required | Use `application/json`. |
| `Accept` | string | Required | Use `application/json` for buffered responses or `text/event-stream` for streaming. |

### Request body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `model` | string | Required | Deployment name to invoke in the project. |
| `input` | string or array | Required | Input text, or an array of structured input items and content parts. |
| `instructions` | string | Optional | Additional instructions applied to this response. |
| `tools` | array | Optional | Tools available during generation, such as code interpreter, file search, web search, or function calling. |
| `temperature` | number | Optional | Sampling temperature for generated output. |
| `max_tokens` | integer | Optional | Maximum number of tokens to generate in the output. |
| `stream` | boolean | Optional | When `true`, the service returns server-sent events instead of a buffered JSON response. |
| `response_format` | object | Optional | Output format configuration, such as text or JSON schema mode. |

### Example request

```bash
curl -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/responses?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "model": "gpt-4.1-mini",
    "input": [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": "Summarize the invoice and return valid JSON with amount, due_date, and status."
          }
        ]
      }
    ],
    "instructions": "Return concise output.",
    "temperature": 0.2,
    "max_tokens": 300,
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "invoice_summary",
        "schema": {
          "type": "object",
          "properties": {
            "amount": {"type": "string"},
            "due_date": {"type": "string"},
            "status": {"type": "string"}
          },
          "required": ["amount", "due_date", "status"]
        }
      }
    }
  }'
```

### Example request (streaming)

```bash
curl -N -X POST "https://YOUR_ENDPOINT/api/projects/YOUR_PROJECT_NAME/responses?api-version=2025-05-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "gpt-4.1-mini",
    "input": "Write a three-bullet summary of the attached incident report.",
    "stream": true,
    "tools": [
      {"type": "file_search"}
    ]
  }'
```

## Response

### Response body

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Unique identifier for the response. |
| `object` | string | Object type. This value is `response`. |
| `status` | string | Lifecycle state such as `queued`, `in_progress`, `completed`, `failed`, or `cancelled`. |
| `model` | string | Deployment name used for generation. |
| `output` | array | Generated output items. |
| `usage` | object | Token usage for the request. |
| `usage.input_tokens` | integer | Number of input tokens processed. |
| `usage.output_tokens` | integer | Number of output tokens generated. |
| `usage.total_tokens` | integer | Total tokens used by the request. |

### Example response

```json
{
  "id": "resp_01JX8V6C4FQ2R6P4Z5W8N9K7M1",
  "object": "response",
  "status": "completed",
  "model": "gpt-4.1-mini",
  "output": [
    {
      "id": "msg_01JX8V6D0S4H2T6H6EW4P2Q4ME",
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "{\"amount\":\"$4,250.00\",\"due_date\":\"2025-05-31\",\"status\":\"pending\"}"
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 118,
    "output_tokens": 42,
    "total_tokens": 160
  }
}
```

## Errors

| Status | Code | Description |
| --- | --- | --- |
| `400` | `invalid_request_error` | The request body is missing `model` or `input`, or contains an unsupported content-part shape. |
| `401` | `unauthorized` | The bearer token or API key is missing, expired, or invalid. |
| `404` | `not_found` | The specified deployment is not available in the project. |
| `429` | `rate_limit_exceeded` | The deployment or project rate limit was exceeded. |
