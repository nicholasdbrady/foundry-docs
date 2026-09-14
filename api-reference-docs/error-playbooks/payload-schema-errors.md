# Payload and schema errors (400 and 422)

## Symptom

Typical responses include:

- `400 Bad Request`
- `422 Unprocessable Entity`
- `schema validation failed`
- `field is required`
- `invalid type`
- `unknown field` or `additional properties are not allowed`

These failures usually happen before the request reaches model execution.

## Probable Cause(s)

1. **Missing required fields** such as `name`, `definition`, or `agent_id`.
2. **Wrong JSON types** such as strings where arrays or objects are expected.
3. **Invalid enum values** such as `role: "human"` instead of a supported role.
4. **Extra fields in strict mode** when the endpoint or SDK model class rejects unknown properties.
5. **Path and body mismatch** such as sending `thread_id` in the body while also targeting `/threads/YOUR_THREAD_ID` in the URL.

## Validation Commands

### 1. Validate JSON syntax before sending

```bash
python -m json.tool payload.json > /dev/null
```

### 2. Inspect top-level types with `jq`

```bash
jq 'to_entries[] | {key: .key, type: (.value | type)}' payload.json
```

### 3. Validate against a local schema when available

```bash
npx ajv-cli validate -s schema.json -d payload.json
```

or:

```bash
python -m pip install check-jsonschema
check-jsonschema --schemafile schema.json payload.json
```

### 4. Capture the exact service error details

```bash
curl -sS -D response-headers.txt \
  -o response-body.json \
  "https://YOUR_ENDPOINT" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  --data @payload.json

cat response-body.json
```

Look for the field path that the service returns first. The first failing field is usually the fastest fix.

## Resolution Steps

### Common field mismatches to check first

| Pattern | Incorrect example | Correct example |
| --- | --- | --- |
| Required object missing | `"definition": null` | `"definition": { ... }` |
| Array sent as string | `"tools": "file_search"` | `"tools": [{"type": "file_search"}]` |
| Boolean sent as string | `"stream": "true"` | `"stream": true` |
| Wrong enum | `"role": "human"` | `"role": "user"` |
| Unknown field in strict mode | `"debug": true` | remove the field |

### Create agent: field-by-field troubleshooting

Check these fields in order:

1. `name` — required, unique, and usually limited to alphanumeric characters plus internal hyphens.
2. `definition` — required object.
3. `definition.kind` — must match a supported kind such as `prompt`, `hosted`, or `workflow` for the selected API surface.
4. `definition.model` — must reference an existing deployment name when the definition type requires it.
5. `definition.tools` — must be an array of tool objects, not a single string.

Correct example:

```json
{
  "name": "support-agent",
  "description": "Handles support ticket triage.",
  "definition": {
    "kind": "prompt",
    "model": "gpt-4.1",
    "instructions": "Classify incoming tickets and return a short triage plan.",
    "tools": [
      { "type": "file_search" }
    ]
  }
}
```

Incorrect example:

```json
{
  "name": "support agent",
  "definition": "prompt",
  "model": "gpt-4.1",
  "tools": "file_search",
  "debug": true
}
```

Why it fails:

- `name` contains a space in a field that usually expects a slug-like identifier.
- `definition` is a string instead of an object.
- `model` is in the wrong place.
- `tools` is a string instead of an array.
- `debug` is likely rejected in strict mode.

### Create thread: field-by-field troubleshooting

Check these fields next:

1. `messages` — when supplied, must be an array.
2. `messages[].role` — must be a supported enum value.
3. `messages[].content` — must follow the endpoint's content shape.
4. `metadata` — must be an object of string values when metadata is supported.

Correct example:

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Summarize the deployment checklist."
        }
      ]
    }
  ],
  "metadata": {
    "ticket_id": "INC-1042"
  }
}
```

Incorrect example:

```json
{
  "messages": {
    "role": "human",
    "content": "Summarize the deployment checklist."
  },
  "metadata": ["INC-1042"]
}
```

Why it fails:

- `messages` is an object instead of an array.
- `role` uses an unsupported value.
- `content` shape does not match a structured content array.
- `metadata` is an array instead of an object.

### Create run: field-by-field troubleshooting

Check these fields next:

1. `agent_id` — required for run creation and must reference an existing agent or agent version according to the endpoint contract.
2. `stream` — must be a boolean when supported.
3. `instructions` or `additional_instructions` — must be strings, not nested objects.
4. Tool output submissions must use the exact field names expected by the run status response.

Correct example:

```json
{
  "agent_id": "support-agent:3",
  "instructions": "Return a numbered remediation checklist.",
  "stream": false
}
```

Incorrect example:

```json
{
  "agent": "support-agent",
  "instructions": {
    "text": "Return a numbered remediation checklist."
  },
  "stream": "false",
  "unknownFlag": true
}
```

Why it fails:

- `agent` is not the expected field name.
- `instructions` is an object instead of a string.
- `stream` is a string instead of a boolean.
- `unknownFlag` is not part of the contract.

### If strict-mode extra fields are the problem

1. Remove every non-documented field from the body.
2. Retry with the smallest payload that can still reproduce the operation.
3. Add optional fields back one at a time until the failure returns.

Minimal-payload debugging pattern:

```json
{
  "agent_id": "support-agent:3"
}
```

If the minimal payload works, the failure is in an optional field rather than the operation itself.

## Prevention Guidance

- Generate request bodies from typed SDK models whenever possible.
- Keep one known-good payload per operation in source control as a contract test fixture.
- Validate JSON before sending it from CI pipelines and automation jobs.
- Prefer additive rollout: start with the smallest valid request, then add optional fields.
- Log the response field path for every `400` or `422` so recurrent schema drifts are easy to spot.
