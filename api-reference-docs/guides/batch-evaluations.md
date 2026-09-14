# Run batch evaluations

Time: 5-10 minutes.

This guide scores a saved JSONL file of agent outputs in one evaluation run, monitors the job, and drills into failing samples.

## Prerequisites

- `YOUR_OPENAI_ENDPOINT`
- An evaluation definition or the inputs needed to create one
- A JSONL file that already contains agent outputs
- An API key or bearer token for the OpenAI-compatible endpoint

## Happy path

### Step 1: Upload the batch input file

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/files?api-version=v1"           -H "api-key: YOUR_API_KEY"           -F "purpose=assistants"           -F "file=@agent-outputs.jsonl"
```

**Python**

```python
openai_client = client.get_openai_client()
batch_file = openai_client.files.create(
    file=open("agent-outputs.jsonl", "rb"),
    purpose="assistants",
)
print(batch_file.id)
```

### Step 2: Create or reuse the evaluation definition

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/evals?api-version=v1"           -H "api-key: YOUR_API_KEY"           -H "Content-Type: application/json"           -d '{
    "name": "agent-output-batch-eval",
    "statusCode": 201,
    "data_source_config": {
      "type": "custom",
      "item_schema": {
        "type": "object",
        "properties": {
          "input": {"type": "string"},
          "output": {"type": "string"}
        },
        "required": ["input", "output"]
      },
      "include_sample_schema": true
    },
    "testing_criteria": []
  }'
```

**Python**

```python
evaluation = openai_client.evals.create(
    name="agent-output-batch-eval",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
            },
            "required": ["input", "output"],
        },
        "include_sample_schema": True,
    },
    testing_criteria=[],
)
print(evaluation.id)
```

### Step 3: Start the batch run

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/evals/YOUR_EVAL_ID/runs?api-version=v1"           -H "api-key: YOUR_API_KEY"           -H "Content-Type: application/json"           -d '{
    "name": "agent-output-batch-run-001",
    "data_source": {
      "type": "jsonl",
      "source": {"type": "file_id", "id": "YOUR_FILE_ID"}
    }
  }'
```

**Python**

```python
run = openai_client.evals.runs.create(
    eval_id=evaluation.id,
    name="agent-output-batch-run-001",
    data_source={
        "type": "jsonl",
        "source": {"type": "file_id", "id": batch_file.id},
    },
)
print(run.id)
```

### Step 4: Monitor the job and read row-level output

**cURL**

```bash
curl "YOUR_OPENAI_ENDPOINT/evals/YOUR_EVAL_ID/runs/YOUR_RUN_ID?api-version=v1"           -H "api-key: YOUR_API_KEY"

curl "YOUR_OPENAI_ENDPOINT/evals/YOUR_EVAL_ID/runs/YOUR_RUN_ID/output_items?api-version=v1"           -H "api-key: YOUR_API_KEY"
```

**Python**

```python
run = openai_client.evals.runs.retrieve(
    eval_id=evaluation.id,
    run_id=run.id,
)
print(run.status)

output_items = openai_client.evals.runs.output_items.list(
    eval_id=evaluation.id,
    run_id=run.id,
)
for item in output_items.data:
    print(item.status)
```

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Run never leaves `queued` | File upload not visible yet | Wait for file processing and retry the run. |
| Every row errors | JSONL fields do not match the evaluation schema | Rebuild the file to match the declared fields. |
| A few rows fail only | Input-specific formatter problem | Inspect `output_items/{output_item_id}` for the failing sample. |
| Scores look wrong | Grader mapping is incorrect | Recheck `{{item...}}` and `{{sample...}}` expressions. |

## Exact endpoint reference links

- [`../task-map-v1.md#run-batch-evaluations-on-agent-outputs`](../task-map-v1.md#run-batch-evaluations-on-agent-outputs)
- `/api-sdk/reference-preview-latest`
