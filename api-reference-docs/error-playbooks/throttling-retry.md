# Throttling and retry strategy (429 and rate limiting)

## Symptom

Common signals include:

- `429 Too Many Requests`
- a `Retry-After` response header
- intermittent success during low traffic and repeated failure during bursts
- run creation succeeds but the underlying model call slows down or stalls
- healthy latency at low concurrency and degraded performance at scale

## Probable Cause(s)

1. **Burst traffic** — the workload sends too many requests in a short one-second or ten-second window.
2. **Per-resource limits** — the underlying model deployment has insufficient requests-per-minute (RPM) or tokens-per-minute (TPM).
3. **Per-subscription or per-region capacity constraints** — hosted agent sessions or quota units are exhausted.
4. **Retry storm** — clients retry immediately without backoff, making the throttle window worse.

## Validation Commands

### 1. Capture the response headers from a throttled request

```bash
curl -sS -D response-headers.txt \
  -o response-body.json \
  "https://YOUR_ENDPOINT" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @request.json

cat response-headers.txt
```

Inspect these headers first:

- `Retry-After`
- `x-ms-error-code`
- `x-request-id` or other request correlation headers

### 2. Check whether traffic is bursty rather than just high volume

If a deployment is set to 600 RPM, a burst of more than about 10 requests in one second can still produce `429` responses even when the full-minute total seems acceptable.

### 3. Review deployment quota and usage

Use the Foundry or Azure portal quota views for the target deployment and compare:

- assigned TPM
- derived RPM
- observed peak concurrency
- average and p95 latency during the throttle window

## Resolution Steps

### Step 1: Honor `Retry-After` exactly when present

If the service sends `Retry-After`, wait that long before retrying. Do not apply a shorter client-side delay.

### Step 2: Use exponential backoff with jitter

If `Retry-After` is absent, use exponential backoff with randomness so many clients do not re-fire at the same moment.

Python example:

```python
import random
import time
import requests


def post_with_retry(url: str, headers: dict, payload: dict, max_attempts: int = 6):
    delay = 1.0

    for attempt in range(1, max_attempts + 1):
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code != 429:
            response.raise_for_status()
            return response.json()

        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            sleep_seconds = float(retry_after)
        else:
            sleep_seconds = delay + random.uniform(0, delay * 0.25)
            delay = min(delay * 2, 30)

        print(f"attempt={attempt} status=429 sleeping={sleep_seconds:.2f}s")
        time.sleep(sleep_seconds)

    raise RuntimeError("Request stayed throttled after all retry attempts")
```

### Step 3: Avoid immediate fan-out

When a workflow needs to create many runs, messages, or eval jobs:

1. queue work locally
2. dispatch at a fixed concurrency
3. batch where the API supports it
4. separate low-priority background work from interactive traffic

### Step 4: Batch requests where possible

Request batching strategies that usually help:

- coalesce many tiny prompts into one evaluation batch when latency is not user-facing
- avoid creating one thread per small message if a single thread can safely hold the context
- upload files once and reuse file IDs instead of re-uploading the same payload repeatedly
- prefetch metadata such as deployments and connections instead of calling those endpoints on every request

### Step 5: Scale quota or distribute traffic

If the retry logic is correct and traffic is steady, move to a capacity fix:

- assign more TPM to the busiest deployment
- spread traffic across multiple model deployments
- route non-urgent work to background queues
- consider provisioned throughput for stable high-volume traffic

## cURL retry example

This example honors `Retry-After` when present and otherwise falls back to exponential backoff.

```bash
DELAY=1

for ATTEMPT in 1 2 3 4 5 6; do
  STATUS=$(curl -sS \
    -D response-headers.txt \
    -o response-body.json \
    -w "%{http_code}" \
    "https://YOUR_ENDPOINT" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    --data @request.json)

  if [ "$STATUS" != "429" ]; then
    cat response-body.json
    break
  fi

  RETRY_AFTER=$(awk 'BEGIN{IGNORECASE=1} /^Retry-After:/ {print $2}' response-headers.txt | tr -d '\r')
  if [ -n "$RETRY_AFTER" ]; then
    SLEEP_SECS="$RETRY_AFTER"
  else
    SLEEP_SECS="$DELAY"
    DELAY=$(( DELAY * 2 ))
    if [ "$DELAY" -gt 30 ]; then DELAY=30; fi
  fi

  echo "attempt=$ATTEMPT status=429 sleeping=$SLEEP_SECS s"
  sleep "$SLEEP_SECS"
done
```

## Known limits by resource type

The service limits below are the most useful first checks when diagnosing throttling.

| Resource type | Known limit or behavior | Scope |
| --- | --- | --- |
| Foundry Agent Service API surface | No separate API request rate limit; throttling comes from the underlying model deployment | per deployment |
| Files per agent or thread | 10,000 | per agent or thread |
| File size for agents | 512 MB | per file |
| Aggregate uploaded files | 300 GB | per agent workload |
| Vector-store attachment size | 2,000,000 tokens | per file |
| Messages per thread | 100,000 | per thread |
| Text content size | 1,500,000 characters | per message |
| Tools registered | 128 | per agent |
| Hosted agent active sessions | 50 | per subscription per region |
| Azure OpenAI older chat models | 6 RPM and 1,000 TPM per quota unit | per deployment unit |
| `o1` and `o1-preview` | 1 RPM and 6,000 TPM per quota unit | per deployment unit |
| `o3` and `o4-mini` | 1 RPM and 1,000 TPM per quota unit | per deployment unit |
| `o3-mini`, `o1-mini`, `o3-pro` | 1 RPM and 10,000 TPM per quota unit | per deployment unit |

The model values are quota-derived defaults and can change as quota is reassigned. Always verify the live numbers for the exact deployment that is returning `429`.

## Prevention Guidance

- Treat `429` as a normal operating condition and design for it.
- Use bounded concurrency instead of unbounded async fan-out.
- Honor `Retry-After` before any custom retry formula.
- Add jitter to every retry path.
- Keep interactive and batch workloads on separate queues or deployments.
- Monitor retry count, queue depth, p95 latency, and per-deployment saturation so scaling decisions happen before users notice degradation.
