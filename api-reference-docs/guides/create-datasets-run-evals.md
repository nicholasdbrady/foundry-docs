# Create datasets and run evaluations

Time: 5-10 minutes.

This guide creates a dataset version, stages a JSONL upload, creates an evaluation definition, starts a run, and reads the results.

## Prerequisites

- `YOUR_PROJECT_ENDPOINT`
- `YOUR_OPENAI_ENDPOINT`
- A bearer token for `https://ai.azure.com/.default` or an API key for the OpenAI-compatible surface
- A JSONL file such as `eval-inputs.jsonl`
- A grader deployment name such as `YOUR_GRADER_DEPLOYMENT`

## Happy path

### Step 1: Create the dataset version

**cURL**

```bash
curl -X PATCH "YOUR_PROJECT_ENDPOINT/datasets/hotel-eval/versions/1?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/merge-patch+json"           -d '{"type": "uri_folder", "description": "Hotel evaluation inputs"}'
```

**Python**

```python
dataset = client.datasets.upload_file(
    name="hotel-eval",
    version="1",
    file_path="./eval-inputs.jsonl",
)
print(dataset.id)
```

### Step 2: Start the pending upload when using the raw REST path

**cURL**

```bash
curl -X POST "YOUR_PROJECT_ENDPOINT/datasets/hotel-eval/versions/1/startPendingUpload?api-version=v1"           -H "Authorization: Bearer YOUR_TOKEN"           -H "Content-Type: application/json"           -d '{"pendingUploadType": "BlobReference"}'
```

**Python**

```python
# The SDK upload_file helper already performs the upload.
print("SDK upload completed in step 1")
```

Upload the JSONL payload to the returned storage target before continuing.

### Step 3: Create the evaluation definition

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/evals?api-version=v1"           -H "api-key: YOUR_API_KEY"           -H "Content-Type: application/json"           -d '{
    "name": "hotel-eval",
    "statusCode": 201,
    "data_source_config": {
      "type": "custom",
      "item_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
      },
      "include_sample_schema": true
    },
    "testing_criteria": [
      {
        "type": "score_model",
        "name": "coherence",
        "model": "YOUR_GRADER_DEPLOYMENT",
        "input": "{{item.query}}",
        "reference": "{{sample.output_text}}"
      }
    ]
  }'
```

**Python**

```python
openai_client = client.get_openai_client()
evaluation = openai_client.evals.create(
    name="hotel-eval",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "include_sample_schema": True,
    },
    testing_criteria=[
        {
            "type": "azure_ai_evaluator",
            "name": "coherence",
            "evaluator_name": "builtin.coherence",
            "data_mapping": {
                "query": "{{item.query}}",
                "response": "{{sample.output_text}}",
            },
            "initialization_parameters": {
                "deployment_name": "YOUR_GRADER_DEPLOYMENT"
            },
        }
    ],
)
print(evaluation.id)
```

### Step 4: Start the evaluation run

**cURL**

```bash
curl -X POST "YOUR_OPENAI_ENDPOINT/evals/YOUR_EVAL_ID/runs?api-version=v1"           -H "api-key: YOUR_API_KEY"           -H "Content-Type: application/json"           -d '{
    "name": "hotel-eval-run-001",
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
    name="hotel-eval-run-001",
    data_source={
        "type": "azure_ai_target_completions",
        "source": {"type": "file_id", "id": dataset.id},
        "input_messages": {
            "type": "template",
            "template": [
                {
                    "type": "message",
                    "role": "user",
                    "content": {"type": "input_text", "text": "{{item.query}}"},
                }
            ],
        },
    },
)
print(run.id)
```

### Step 5: Poll and inspect the results

**cURL**

```bash
curl "YOUR_OPENAI_ENDPOINT/evals/YOUR_EVAL_ID/runs/YOUR_RUN_ID/output_items?api-version=v1"           -H "api-key: YOUR_API_KEY"
```

**Python**

```python
output_items = openai_client.evals.runs.output_items.list(
    eval_id=evaluation.id,
    run_id=run.id,
)
for item in output_items.data:
    print(item.status, item.sample.output_text)
```

## Common failure branches

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Evaluation run errors immediately | Uploaded file schema does not match `data_source_config` | Align the JSONL field names and required properties. |
| Grader returns model-not-found | Wrong grader deployment name | Use a deployed model that supports the evaluator. |
| Dataset exists but run cannot see it | Upload not finalized | Complete the pending upload before creating the run. |
| Output items are empty | Run is still in progress | Poll the run until it reaches a terminal state. |

## Exact endpoint reference links

- [`../task-map-v1.md#create-datasets-and-run-evaluations`](../task-map-v1.md#create-datasets-and-run-evaluations)
- `/api-sdk/reference-preview-latest`
