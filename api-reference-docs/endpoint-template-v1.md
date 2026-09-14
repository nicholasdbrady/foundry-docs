# Endpoint page template v1

> Use this template for every API operation page. Replace placeholders, keep the section order unchanged, and remove comments before publication.

## 1. One-line purpose statement

<!-- State exactly what the operation does in one sentence. Use active voice. Name the resource and outcome. Example pattern: "Create an agent that can run tool-enabled conversations in a project." -->

**Purpose:** [DESCRIBE THE SINGLE PRIMARY OUTCOME OF THIS OPERATION].

## 2. When to use / when not to use

<!-- Give readers a quick decision point. Keep each list short and practical. Focus on neighboring operations readers might confuse with this one. -->

**Use this operation when:**
- [CONDITION 1: SPECIFIC SCENARIO WHERE THIS OPERATION IS THE RIGHT CHOICE]
- [CONDITION 2: SPECIFIC SCENARIO WHERE THIS OPERATION IS THE RIGHT CHOICE]
- [OPTIONAL CONDITION 3]

**Do not use this operation when:**
- [USE ANOTHER OPERATION FOR A DIFFERENT LIFECYCLE ACTION, SUCH AS LIST, UPDATE, DELETE, OR RUN]
- [CALL OUT A COMMON MISUSE, SUCH AS USING A COLLECTION ENDPOINT WHEN A RESOURCE ID IS REQUIRED]
- [OPTIONAL MISUSE 3]

## 3. Method + path + required auth/headers

<!-- Show the canonical request shape first. Include the exact HTTP method, production path, API version behavior if required, and only the headers that matter for a successful call. -->

**HTTP method:** `HTTP_METHOD`

**Path:** `YOUR_ENDPOINT/RESOURCE_PATH`

**Required authentication:**
- `Authorization: Bearer YOUR_TOKEN` **or** `api-key: YOUR_API_KEY`
- [ADD SCOPES, ROLE REQUIREMENTS, OR PROJECT-LEVEL ACCESS REQUIREMENTS IF NEEDED]

**Required headers:**
- `Content-Type: application/json` [REMOVE IF NOT REQUIRED]
- `Accept: application/json` [REMOVE IF NOT REQUIRED]
- `[HEADER_NAME]: [WHEN AND WHY IT IS REQUIRED]`

<!-- If the endpoint requires a preview header or feature flag, mention it briefly here and fully explain it in section 8. -->

## 4. Required query parameters and path parameters

<!-- Document only required parameters here. Put optional parameters in a separate reference table elsewhere if needed. For each parameter, explain what value format is accepted and why the parameter matters. -->

### Required path parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `RESOURCE_ID` | string | yes | [WHAT THE IDENTIFIER POINTS TO AND WHERE TO GET IT]. |
| `PROJECT_NAME` | string | yes | [IF APPLICABLE]. |

### Required query parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `api-version` | string | yes | [EXACT VERSION STRING OR VERSION FAMILY REQUIRED FOR THIS OPERATION]. |
| `FILTER_NAME` | string | yes | [ONLY INCLUDE IF THIS OPERATION REQUIRES IT]. |

<!-- If there are no required query parameters other than api-version, say so explicitly. If there are no required path parameters, say "None." -->

## 5. Minimal request example (copy-run-edit ready, using cURL)

<!-- Keep this example runnable with the fewest possible fields. Use realistic placeholder values, not pseudo-code. Only include required headers, required query parameters, and the smallest valid body. If the body can be empty, show an empty body or omit it. -->

```bash
curl -X HTTP_METHOD "YOUR_ENDPOINT/RESOURCE_PATH?api-version=API_VERSION" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "REQUIRED_FIELD": "REPLACE_ME"
  }'
```

<!-- Add one sentence after the example if readers typically need to edit a specific field before the command will work. -->

## 6. Minimal successful response example

<!-- Show the smallest representative 2xx response. Keep only fields readers need to recognize success, resource identity, lifecycle state, pagination cursor, or streaming contract. Use valid JSON. -->

```json
{
  "id": "RESOURCE_ID",
  "object": "RESOURCE_TYPE",
  "status": "succeeded"
}
```

<!-- If the endpoint returns 201, include the created resource shape. If it returns 202, show the operation state readers should poll. If it streams, show the first event envelope instead of a full buffered response. -->

## 7. Common error responses with likely causes and fixes

<!-- Include at least three high-frequency failure patterns. Prioritize errors users can act on quickly: auth failures, missing parameters, resource state conflicts, unsupported preview flags, quota limits, or invalid body shape. -->

| Status / error | Likely cause | Recommended fix |
| --- | --- | --- |
| `401 Unauthorized` | [TOKEN, API KEY, OR SCOPE IS MISSING, EXPIRED, OR INVALID]. | [REFRESH CREDENTIALS, VERIFY HEADER NAME, VERIFY PROJECT OR RESOURCE SCOPE]. |
| `404 Not Found` | [RESOURCE ID, SESSION ID, DEPLOYMENT NAME, OR PARENT PROJECT DOES NOT EXIST IN THIS SCOPE]. | [VERIFY IDENTIFIER, REGION, PROJECT, AND API VERSION]. |
| `429 Too Many Requests` | [REQUEST RATE, CONCURRENT RUNS, OR TOKEN USAGE EXCEEDED A LIMIT]. | [RETRY WITH BACKOFF, REDUCE CONCURRENCY, OR REQUEST HIGHER QUOTA]. |
| `400 Bad Request` | [REQUIRED FIELD, PARAMETER, OR BODY SHAPE IS INVALID]. | [COMPARE THE REQUEST TO THE MINIMAL EXAMPLE AND FIX FIELD NAMES OR VALUE TYPES]. |

<!-- Replace with the three to five errors most likely for this operation. Prefer operation-specific guidance over generic HTTP definitions. -->

## 8. Preview/feature-flag notes (if applicable)

<!-- Use this section only when the operation is preview-only, gated by a header, restricted to selected regions, or available behind a project or tenant feature switch. If none apply, state "Not applicable." -->

- **Availability:** [GA | PREVIEW | PRIVATE PREVIEW | NOT APPLICABLE]
- **Required feature flag or header:** `[HEADER_OR_FLAG_NAME]` [OR "NONE"]
- **Region or cloud limitations:** [LIST ANY REGION, TENANT, OR CLOUD RESTRICTIONS]
- **Behavior differences from GA:** [STATE WHAT MAY CHANGE, SUCH AS RESPONSE SHAPE, RATE LIMITS, OR SDK SUPPORT]

## 9. Limits, pagination, and streaming behavior notes

<!-- Tell readers what happens at scale. Document default page size, max page size, continuation token behavior, ordering guarantees, timeout expectations, streaming media type, event framing, or known payload limits. If a behavior does not apply, say so explicitly. -->

- **Limits:** [REQUEST SIZE, ITEM COUNT, TOKEN LIMIT, FILE SIZE, OR CONCURRENCY LIMIT]
- **Pagination:** [NONE | USES `top` AND `skipToken` | USES `nextLink` | OTHER]
- **Ordering:** [STATE WHETHER RESULTS ARE STABLE, MOST-RECENT-FIRST, OR UNSPECIFIED]
- **Streaming:** [NONE | SERVER-SENT EVENTS | CHUNKED JSON | WEBHOOK CALLBACK]
- **Retries and idempotency notes:** [IF SAFE TO RETRY, AND WHICH CLIENT-SUPPLIED IDS OR HEADERS HELP AVOID DUPLICATE WORK]

## 10. SDK parity links (Python/JavaScript/C#/Java)

<!-- Link to the closest SDK method or package page for each language. If an SDK does not yet expose this operation, say "Not yet available" and, if useful, point to the raw REST fallback guidance. -->

| Language | SDK parity |
| --- | --- |
| Python | [PYTHON SDK METHOD OR PACKAGE LINK] |
| JavaScript | [JAVASCRIPT SDK METHOD OR PACKAGE LINK] |
| C# | [C_SHARP SDK METHOD OR PACKAGE LINK] |
| Java | [JAVA SDK METHOD OR PACKAGE LINK] |

<!-- Final author check before publishing:
1. Confirm the cURL example runs after replacing placeholders.
2. Confirm every required parameter appears in both the parameter table and the request example.
3. Confirm at least three operation-specific error patterns are documented.
4. Confirm preview, limits, pagination, and streaming notes are explicit, even when the answer is "Not applicable" or "None."
5. Confirm SDK parity reflects current shipped support, not planned support.
-->