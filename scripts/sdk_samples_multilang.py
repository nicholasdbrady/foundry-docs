"""cURL, C#, and JavaScript/TypeScript SDK samples for OpenAPI x-codeSamples.

This module provides sample dictionaries parallel to the Python samples
in generate_sdk_samples.py, keyed by the same operationId values.
"""

# ---------------------------------------------------------------------------
# Preamble templates
# ---------------------------------------------------------------------------

CURL_OPENAI_PREAMBLE_ENTRA = """\
# Get a token via Azure CLI
# TOKEN=$(az account get-access-token --scope https://cognitiveservices.azure.com/.default --query accessToken -o tsv)
"""

CURL_OPENAI_PREAMBLE_APIKEY = """\
# Use your API key from the Azure portal
"""

CURL_PROJECTS_PREAMBLE_ENTRA = """\
# Get a token via Azure CLI
# TOKEN=$(az account get-access-token --scope https://cognitiveservices.azure.com/.default --query accessToken -o tsv)
"""

CURL_PROJECTS_PREAMBLE_APIKEY = """\
# Use your API key from the Azure portal
"""

CSHARP_OPENAI_PREAMBLE_ENTRA = """\
using Azure.AI.Projects;
using Azure.AI.Projects.OpenAI;
using Azure.Identity;

var client = new AIProjectClient(
    new Uri("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME"),
    new DefaultAzureCredential());

"""

CSHARP_OPENAI_PREAMBLE_APIKEY = """\
using Azure.AI.Projects;
using Azure.AI.Projects.OpenAI;
using Azure;

var client = new AIProjectClient(
    new Uri("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME"),
    new AzureKeyCredential("YOUR_API_KEY"));

"""

CSHARP_PROJECTS_PREAMBLE_ENTRA = """\
using Azure.AI.Projects;
using Azure.Identity;

var client = new AIProjectClient(
    new Uri("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME"),
    new DefaultAzureCredential());

"""

CSHARP_PROJECTS_PREAMBLE_APIKEY = """\
using Azure.AI.Projects;
using Azure;

var client = new AIProjectClient(
    new Uri("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME"),
    new AzureKeyCredential("YOUR_API_KEY"));

"""

JS_OPENAI_PREAMBLE_ENTRA = """\
import { AIProjectClient } from "@azure/ai-projects";
import { DefaultAzureCredential } from "@azure/identity";

const project = new AIProjectClient(
    "https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME",
    new DefaultAzureCredential(),
);
const openai = await project.getOpenAIClient();

"""

JS_OPENAI_PREAMBLE_APIKEY = """\
import { AIProjectClient } from "@azure/ai-projects";
import { AzureKeyCredential } from "@azure/core-auth";

const project = new AIProjectClient(
    "https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME",
    new AzureKeyCredential("YOUR_API_KEY"),
);
const openai = await project.getOpenAIClient();

"""

JS_PROJECTS_PREAMBLE_ENTRA = """\
import { AIProjectClient } from "@azure/ai-projects";
import { DefaultAzureCredential } from "@azure/identity";

const client = new AIProjectClient(
    "https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME",
    new DefaultAzureCredential(),
);

"""

JS_PROJECTS_PREAMBLE_APIKEY = """\
import { AIProjectClient } from "@azure/ai-projects";
import { AzureKeyCredential } from "@azure/core-auth";

const client = new AIProjectClient(
    "https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME",
    new AzureKeyCredential("YOUR_API_KEY"),
);

"""

# ---------------------------------------------------------------------------
# cURL samples — OpenAI v1 API
# ---------------------------------------------------------------------------

CURL_OPENAI_SAMPLES = {
    # ── Responses ──────────────────────────────────────────────────────
    "createResponse": 'curl -X POST "$ENDPOINT/openai/v1/responses" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o", "input": "What is the capital of France?"}\'',
    "getResponse": 'curl "$ENDPOINT/openai/v1/responses/resp_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "deleteResponse": 'curl -X DELETE "$ENDPOINT/openai/v1/responses/resp_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "cancelResponse": 'curl -X POST "$ENDPOINT/openai/v1/responses/resp_abc123/cancel" \\\n  -H "Authorization: Bearer $TOKEN"',
    "listInputItems": 'curl "$ENDPOINT/openai/v1/responses/resp_abc123/input_items" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Chat ───────────────────────────────────────────────────────────
    "createChatCompletion": 'curl -X POST "$ENDPOINT/openai/v1/chat/completions" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello!"}]}\'',
    "createCompletion": 'curl -X POST "$ENDPOINT/openai/v1/completions" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o", "prompt": "Say hello", "max_tokens": 100}\'',

    # ── Conversations ──────────────────────────────────────────────────
    "createConversation": 'curl -X POST "$ENDPOINT/openai/v1/conversations" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"items": [{"type": "message", "role": "user", "content": "Hello"}]}\'',
    "retrieveConversation": 'curl "$ENDPOINT/openai/v1/conversations/conv_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "updateConversation": 'curl -X POST "$ENDPOINT/openai/v1/conversations/conv_abc123" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"metadata": {"topic": "geography"}}\'',
    "deleteConversation": 'curl -X DELETE "$ENDPOINT/openai/v1/conversations/conv_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "listConversationItems": 'curl "$ENDPOINT/openai/v1/conversations/conv_abc123/items" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createConversationItems": 'curl -X POST "$ENDPOINT/openai/v1/conversations/conv_abc123/items" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"items": [{"type": "message", "role": "user", "content": "Follow-up"}]}\'',
    "retrieveConversationItem": 'curl "$ENDPOINT/openai/v1/conversations/conv_abc123/items/item_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "deleteConversationItem": 'curl -X DELETE "$ENDPOINT/openai/v1/conversations/conv_abc123/items/item_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Embeddings ─────────────────────────────────────────────────────
    "createEmbedding": 'curl -X POST "$ENDPOINT/openai/v1/embeddings" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "text-embedding-3-large", "input": "Sample text"}\'',

    # ── Models ─────────────────────────────────────────────────────────
    "listModels": 'curl "$ENDPOINT/openai/v1/models" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveModel": 'curl "$ENDPOINT/openai/v1/models/gpt-4o" \\\n  -H "Authorization: Bearer $TOKEN"',
    "deleteModel": 'curl -X DELETE "$ENDPOINT/openai/v1/models/ft:gpt-4o:org:suffix:id" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Files ──────────────────────────────────────────────────────────
    "createFile": 'curl -X POST "$ENDPOINT/openai/v1/files" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -F purpose="fine-tune" \\\n  -F file="@data.jsonl"',
    "listFiles": 'curl "$ENDPOINT/openai/v1/files" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveFile": 'curl "$ENDPOINT/openai/v1/files/file-abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "deleteFile": 'curl -X DELETE "$ENDPOINT/openai/v1/files/file-abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "downloadFile": 'curl "$ENDPOINT/openai/v1/files/file-abc123/content" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Batch ──────────────────────────────────────────────────────────
    "createBatch": 'curl -X POST "$ENDPOINT/openai/v1/batches" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"input_file_id": "file-abc123", "endpoint": "/v1/chat/completions", "completion_window": "24h"}\'',
    "listBatches": 'curl "$ENDPOINT/openai/v1/batches" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveBatch": 'curl "$ENDPOINT/openai/v1/batches/batch_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "cancelBatch": 'curl -X POST "$ENDPOINT/openai/v1/batches/batch_abc123/cancel" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Fine-tuning ────────────────────────────────────────────────────
    "createFineTuningJob": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/jobs" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o-mini-2024-07-18", "training_file": "file-abc123"}\'',
    "listPaginatedFineTuningJobs": 'curl "$ENDPOINT/openai/v1/fine_tuning/jobs" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveFineTuningJob": 'curl "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "cancelFineTuningJob": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123/cancel" \\\n  -H "Authorization: Bearer $TOKEN"',
    "listFineTuningJobCheckpoints": 'curl "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123/checkpoints" \\\n  -H "Authorization: Bearer $TOKEN"',
    "listFineTuningEvents": 'curl "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123/events" \\\n  -H "Authorization: Bearer $TOKEN"',
    "pauseFineTuningJob": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123/pause" \\\n  -H "Authorization: Bearer $TOKEN"',
    "resumeFineTuningJob": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123/resume" \\\n  -H "Authorization: Bearer $TOKEN"',
    "FineTuning_CopyCheckpoint": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123/checkpoints/ftckpt-abc123/copy" \\\n  -H "Authorization: Bearer $TOKEN"',
    "FineTuning_GetCheckpoint": 'curl "$ENDPOINT/openai/v1/fine_tuning/jobs/ftjob-abc123/checkpoints/ftckpt-abc123/copy" \\\n  -H "Authorization: Bearer $TOKEN"',
    "listFineTuningCheckpointPermissions": 'curl "$ENDPOINT/openai/v1/fine_tuning/checkpoints/ft:gpt-4o:org:suffix:id/permissions" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createFineTuningCheckpointPermission": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/checkpoints/ft:gpt-4o:org:suffix:id/permissions" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"project_ids": ["proj_abc123"]}\'',
    "deleteFineTuningCheckpointPermission": 'curl -X DELETE "$ENDPOINT/openai/v1/fine_tuning/checkpoints/ft:gpt-4o:org:suffix:id/permissions/perm_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "runGrader": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/alpha/graders/run" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"grader": {"type": "python", "source": "return 1.0"}, "model_sample": "Hello"}\'',
    "validateGrader": 'curl -X POST "$ENDPOINT/openai/v1/fine_tuning/alpha/graders/validate" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"grader": {"type": "python", "source": "return 1.0"}}\'',

    # ── Evals ──────────────────────────────────────────────────────────
    "listEvals": 'curl "$ENDPOINT/openai/v1/evals" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createEval": 'curl -X POST "$ENDPOINT/openai/v1/evals" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"name": "my-eval", "data_source_config": {"type": "custom", "item_schema": {}}, "testing_criteria": []}\'',
    "getEval": 'curl "$ENDPOINT/openai/v1/evals/eval_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "updateEval": 'curl -X POST "$ENDPOINT/openai/v1/evals/eval_abc123" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"name": "updated-name"}\'',
    "deleteEval": 'curl -X DELETE "$ENDPOINT/openai/v1/evals/eval_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "getEvalRuns": 'curl "$ENDPOINT/openai/v1/evals/eval_abc123/runs" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createEvalRun": 'curl -X POST "$ENDPOINT/openai/v1/evals/eval_abc123/runs" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o", "data_source": {"type": "completions"}}\'',
    "getEvalRun": 'curl "$ENDPOINT/openai/v1/evals/eval_abc123/runs/run_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "cancelEvalRun": 'curl -X POST "$ENDPOINT/openai/v1/evals/eval_abc123/runs/run_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "deleteEvalRun": 'curl -X DELETE "$ENDPOINT/openai/v1/evals/eval_abc123/runs/run_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "getEvalRunOutputItems": 'curl "$ENDPOINT/openai/v1/evals/eval_abc123/runs/run_abc123/output_items" \\\n  -H "Authorization: Bearer $TOKEN"',
    "getEvalRunOutputItem": 'curl "$ENDPOINT/openai/v1/evals/eval_abc123/runs/run_abc123/output_items/item_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Realtime ───────────────────────────────────────────────────────
    "createRealtimeSession": 'curl -X POST "$ENDPOINT/openai/v1/realtime/sessions" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o-realtime-preview"}\'',
    "createRealtimeClientSecret": 'curl -X POST "$ENDPOINT/openai/v1/realtime/client_secrets" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o-realtime-preview"}\'',
    "createRealtimeTranscriptionSession": 'curl -X POST "$ENDPOINT/openai/v1/realtime/transcription_sessions" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o-transcribe"}\'',
    "createRealtimeCall": 'curl -X POST "$ENDPOINT/openai/v1/realtime/calls" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o-realtime-preview", "sdp": "YOUR_SDP_OFFER"}\'',
    "acceptRealtimeCall": 'curl -X POST "$ENDPOINT/openai/v1/realtime/calls/call_abc123/accept" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "gpt-4o-realtime-preview"}\'',
    "hangupRealtimeCall": 'curl -X POST "$ENDPOINT/openai/v1/realtime/calls/call_abc123/hangup" \\\n  -H "Authorization: Bearer $TOKEN"',
    "referRealtimeCall": 'curl -X POST "$ENDPOINT/openai/v1/realtime/calls/call_abc123/refer" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"refer_to": "sip:dest@example.com"}\'',
    "rejectRealtimeCall": 'curl -X POST "$ENDPOINT/openai/v1/realtime/calls/call_abc123/reject" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"reason": "busy"}\'',

    # ── Containers ─────────────────────────────────────────────────────
    "listContainers": 'curl "$ENDPOINT/openai/v1/containers" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createContainer": 'curl -X POST "$ENDPOINT/openai/v1/containers" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"name": "my-container"}\'',
    "retrieveContainer": 'curl "$ENDPOINT/openai/v1/containers/container_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "deleteContainer": 'curl -X DELETE "$ENDPOINT/openai/v1/containers/container_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "listContainerFiles": 'curl "$ENDPOINT/openai/v1/containers/container_abc123/files" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createContainerFile": 'curl -X POST "$ENDPOINT/openai/v1/containers/container_abc123/files" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -F file="@data.txt" \\\n  -F file_path="data.txt"',
    "retrieveContainerFile": 'curl "$ENDPOINT/openai/v1/containers/container_abc123/files/file_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "deleteContainerFile": 'curl -X DELETE "$ENDPOINT/openai/v1/containers/container_abc123/files/file_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveContainerFileContent": 'curl "$ENDPOINT/openai/v1/containers/container_abc123/files/file_abc123/content" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Threads (legacy) ───────────────────────────────────────────────
    "createThread": 'curl -X POST "$ENDPOINT/openai/v1/threads" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{}\'',
    "retrieveThread": 'curl "$ENDPOINT/openai/v1/threads/thread_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "modifyThread": 'curl -X POST "$ENDPOINT/openai/v1/threads/thread_abc123" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"metadata": {"topic": "science"}}\'',
    "deleteThread": 'curl -X DELETE "$ENDPOINT/openai/v1/threads/thread_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createMessage": 'curl -X POST "$ENDPOINT/openai/v1/threads/thread_abc123/messages" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"role": "user", "content": "What is the capital of France?"}\'',
    "listMessages": 'curl "$ENDPOINT/openai/v1/threads/thread_abc123/messages" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveMessage": 'curl "$ENDPOINT/openai/v1/threads/thread_abc123/messages/msg_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "modifyMessage": 'curl -X POST "$ENDPOINT/openai/v1/threads/thread_abc123/messages/msg_abc123" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"metadata": {"reviewed": "true"}}\'',
    "deleteMessage": 'curl -X DELETE "$ENDPOINT/openai/v1/threads/thread_abc123/messages/msg_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createRun": 'curl -X POST "$ENDPOINT/openai/v1/threads/thread_abc123/runs" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"assistant_id": "asst_abc123"}\'',
    "createThreadAndRun": 'curl -X POST "$ENDPOINT/openai/v1/threads/runs" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"assistant_id": "asst_abc123", "thread": {"messages": [{"role": "user", "content": "Hello"}]}}\'',
    "listRuns": 'curl "$ENDPOINT/openai/v1/threads/thread_abc123/runs" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveRun": 'curl "$ENDPOINT/openai/v1/threads/thread_abc123/runs/run_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "modifyRun": 'curl -X POST "$ENDPOINT/openai/v1/threads/thread_abc123/runs/run_abc123" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"metadata": {"priority": "high"}}\'',
    "cancelRun": 'curl -X POST "$ENDPOINT/openai/v1/threads/thread_abc123/runs/run_abc123/cancel" \\\n  -H "Authorization: Bearer $TOKEN"',
    "submitToolOutputsToRun": 'curl -X POST "$ENDPOINT/openai/v1/threads/thread_abc123/runs/run_abc123/submit_tool_outputs" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"tool_outputs": [{"tool_call_id": "call_abc123", "output": "result"}]}\'',
    "listRunSteps": 'curl "$ENDPOINT/openai/v1/threads/thread_abc123/runs/run_abc123/steps" \\\n  -H "Authorization: Bearer $TOKEN"',
    "getRunStep": 'curl "$ENDPOINT/openai/v1/threads/thread_abc123/runs/run_abc123/steps/step_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Vector Stores ──────────────────────────────────────────────────
    "listVectorStores": 'curl "$ENDPOINT/openai/v1/vector_stores" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createVectorStore": 'curl -X POST "$ENDPOINT/openai/v1/vector_stores" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"name": "my-vector-store"}\'',
    "getVectorStore": 'curl "$ENDPOINT/openai/v1/vector_stores/vs_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "modifyVectorStore": 'curl -X POST "$ENDPOINT/openai/v1/vector_stores/vs_abc123" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"name": "updated-name"}\'',
    "deleteVectorStore": 'curl -X DELETE "$ENDPOINT/openai/v1/vector_stores/vs_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "searchVectorStore": 'curl -X POST "$ENDPOINT/openai/v1/vector_stores/vs_abc123/search" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"query": "search query"}\'',
    "listVectorStoreFiles": 'curl "$ENDPOINT/openai/v1/vector_stores/vs_abc123/files" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createVectorStoreFile": 'curl -X POST "$ENDPOINT/openai/v1/vector_stores/vs_abc123/files" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"file_id": "file_abc123"}\'',
    "getVectorStoreFile": 'curl "$ENDPOINT/openai/v1/vector_stores/vs_abc123/files/file_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "updateVectorStoreFileAttributes": 'curl -X POST "$ENDPOINT/openai/v1/vector_stores/vs_abc123/files/file_abc123" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"attributes": {"key": "value"}}\'',
    "deleteVectorStoreFile": 'curl -X DELETE "$ENDPOINT/openai/v1/vector_stores/vs_abc123/files/file_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "retrieveVectorStoreFileContent": 'curl "$ENDPOINT/openai/v1/vector_stores/vs_abc123/files/file_abc123/content" \\\n  -H "Authorization: Bearer $TOKEN"',
    "createVectorStoreFileBatch": 'curl -X POST "$ENDPOINT/openai/v1/vector_stores/vs_abc123/file_batches" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"file_ids": ["file_abc123", "file_def456"]}\'',
    "getVectorStoreFileBatch": 'curl "$ENDPOINT/openai/v1/vector_stores/vs_abc123/file_batches/vsfb_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "cancelVectorStoreFileBatch": 'curl -X POST "$ENDPOINT/openai/v1/vector_stores/vs_abc123/file_batches/vsfb_abc123/cancel" \\\n  -H "Authorization: Bearer $TOKEN"',
    "listFilesInVectorStoreBatch": 'curl "$ENDPOINT/openai/v1/vector_stores/vs_abc123/file_batches/vsfb_abc123/files" \\\n  -H "Authorization: Bearer $TOKEN"',

    # ── Preview: Audio ─────────────────────────────────────────────────
    "createSpeech": 'curl -X POST "$ENDPOINT/openai/v1/audio/speech" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "tts-1", "voice": "alloy", "input": "Hello!"}\' \\\n  --output output.mp3',
    "createTranscription": 'curl -X POST "$ENDPOINT/openai/v1/audio/transcriptions" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -F model="whisper-1" \\\n  -F file="@audio.mp3"',
    "createTranslation": 'curl -X POST "$ENDPOINT/openai/v1/audio/translations" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -F model="whisper-1" \\\n  -F file="@audio.mp3"',

    # ── Preview: Images ────────────────────────────────────────────────
    "createImage": 'curl -X POST "$ENDPOINT/openai/v1/images/generations" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "dall-e-3", "prompt": "A white cat on a windowsill", "n": 1, "size": "1024x1024"}\'',
    "createImageEdit": 'curl -X POST "$ENDPOINT/openai/v1/images/edits" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -F image="@image.png" \\\n  -F prompt="Add a sunset" \\\n  -F n=1 \\\n  -F size="1024x1024"',
    "createImageVariation": 'curl -X POST "$ENDPOINT/openai/v1/images/variations" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -F image="@image.png" \\\n  -F n=1 \\\n  -F size="1024x1024"',

    # ── Preview: Video ─────────────────────────────────────────────────
    "Videos_Create": 'curl -X POST "$ENDPOINT/openai/v1/videos" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "sora", "prompt": "A mountain landscape at sunset"}\'',
    "Videos_List": 'curl "$ENDPOINT/openai/v1/videos" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Videos_Get": 'curl "$ENDPOINT/openai/v1/videos/video_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Videos_Delete": 'curl -X DELETE "$ENDPOINT/openai/v1/videos/video_abc123" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Videos_RetrieveContent": 'curl "$ENDPOINT/openai/v1/videos/video_abc123/content" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Videos_Remix": 'curl -X POST "$ENDPOINT/openai/v1/videos/video_abc123/remix" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"prompt": "Make it a night scene"}\'',
}

# ---------------------------------------------------------------------------
# cURL samples — Projects API
# ---------------------------------------------------------------------------

CURL_PROJECTS_SAMPLES = {
    "Connections_List": 'curl "$ENDPOINT/connections?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Connections_Get": 'curl "$ENDPOINT/connections/my-connection?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Connections_GetWithCredentials": 'curl -X POST "$ENDPOINT/connections/my-connection/getConnectionWithCredentials?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Datasets_ListLatest": 'curl "$ENDPOINT/datasets?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Datasets_ListVersions": 'curl "$ENDPOINT/datasets/my-dataset/versions?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Datasets_GetVersion": 'curl "$ENDPOINT/datasets/my-dataset/versions/1?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Datasets_CreateOrUpdateVersion": 'curl -X PATCH "$ENDPOINT/datasets/my-dataset/versions/1?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"description": "Training data"}\'',
    "Datasets_DeleteVersion": 'curl -X DELETE "$ENDPOINT/datasets/my-dataset/versions/1?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Datasets_GetCredentials": 'curl -X POST "$ENDPOINT/datasets/my-dataset/versions/1/credentials?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Datasets_StartPendingUploadVersion": 'curl -X POST "$ENDPOINT/datasets/my-dataset/versions/1/startPendingUpload?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"pending_upload_type": "temporary_sas"}\'',
    "Deployments_List": 'curl "$ENDPOINT/deployments?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Deployments_Get": 'curl "$ENDPOINT/deployments/gpt-4o?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Indexes_ListLatest": 'curl "$ENDPOINT/indexes?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Indexes_ListVersions": 'curl "$ENDPOINT/indexes/my-index/versions?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Indexes_GetVersion": 'curl "$ENDPOINT/indexes/my-index/versions/1?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Indexes_CreateOrUpdateVersion": 'curl -X PATCH "$ENDPOINT/indexes/my-index/versions/1?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"description": "Search index"}\'',
    "Indexes_DeleteVersion": 'curl -X DELETE "$ENDPOINT/indexes/my-index/versions/1?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    # Preview-only
    "Evaluations_List": 'curl "$ENDPOINT/evaluations/runs?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Evaluations_Get": 'curl "$ENDPOINT/evaluations/runs/my-eval-run?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Evaluations_Delete": 'curl -X DELETE "$ENDPOINT/evaluations/runs/my-eval-run?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Evaluations_Cancel": 'curl -X POST "$ENDPOINT/evaluations/runs/my-eval-run:cancel?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "Evaluations_Create": 'curl -X POST "$ENDPOINT/evaluations/runs:run?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"display_name": "my-eval", "evaluators": {}, "data": {}}\'',
    "Evaluations_CreateAgentEvaluation": 'curl -X POST "$ENDPOINT/evaluations/runs:runAgent?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"display_name": "agent-eval", "evaluators": {}, "target": {"agent_id": "my-agent:1"}}\'',
    "RedTeams_List": 'curl "$ENDPOINT/redTeams/runs?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "RedTeams_Get": 'curl "$ENDPOINT/redTeams/runs/my-run?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN"',
    "RedTeams_Create": 'curl -X POST "$ENDPOINT/redTeams/runs:run?api-version=v1" \\\n  -H "Authorization: Bearer $TOKEN" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"display_name": "my-redteam", "target": {"agent_id": "my-agent:1"}, "risk_categories": ["violence"]}\'',
}


# ---------------------------------------------------------------------------
# C# samples — OpenAI v1 API (key endpoints)
# ---------------------------------------------------------------------------

CSHARP_OPENAI_SAMPLES = {
    "createResponse": 'var responsesClient = client.OpenAI\n    .GetProjectResponsesClientForModel("gpt-4o");\n\nvar response = await responsesClient\n    .CreateResponseAsync("What is the capital of France?");\n\nConsole.WriteLine(response.GetOutputText());',
    "createChatCompletion": 'var chatClient = client.OpenAI\n    .GetProjectChatClientForModel("gpt-4o");\n\nvar response = await chatClient.CompleteChatAsync(\n    new ChatMessage[] {\n        new UserChatMessage("Hello!"),\n    });\n\nConsole.WriteLine(response.Value.Content[0].Text);',
    "createEmbedding": 'var embeddingClient = client.OpenAI\n    .GetProjectEmbeddingClientForModel("text-embedding-3-large");\n\nvar response = await embeddingClient\n    .GenerateEmbeddingAsync("Sample text to embed");\n\nConsole.WriteLine(response.Value.Vector.Length);',
    "createConversation": 'var conversation = client.OpenAI.Conversations\n    .CreateProjectConversation();\n\nConsole.WriteLine(conversation.Id);',
    "listModels": 'var models = client.OpenAI.GetOpenAIModelClient()\n    .GetModels();\n\nforeach (var model in models.Value)\n    Console.WriteLine(model.Id);',
    "createFile": 'var fileClient = client.OpenAI.GetOpenAIFileClient();\n\nvar file = await fileClient.UploadFileAsync(\n    "data.jsonl", FileUploadPurpose.FineTune);\n\nConsole.WriteLine(file.Value.Id);',
    "listFiles": 'var fileClient = client.OpenAI.GetOpenAIFileClient();\nvar files = await fileClient.GetFilesAsync();\n\nforeach (var f in files.Value)\n    Console.WriteLine($"{f.Id} {f.Filename}");',
    "createBatch": 'var batchClient = client.OpenAI.GetBatchClient();\n\nvar batch = await batchClient.CreateBatchAsync(\n    "file-abc123", "/v1/chat/completions", "24h");\n\nConsole.WriteLine(batch.Value.Id);',
    "createFineTuningJob": 'var ftClient = client.OpenAI.GetFineTuningClient();\n\nvar job = await ftClient.CreateJobAsync(\n    "gpt-4o-mini-2024-07-18", "file-abc123");\n\nConsole.WriteLine(job.Value.Id);',
    "createVectorStore": 'var vsClient = client.OpenAI.GetVectorStoreClient();\n\nvar store = await vsClient.CreateVectorStoreAsync(\n    new VectorStoreCreationOptions { Name = "my-store" });\n\nConsole.WriteLine(store.Value.Id);',
}

CSHARP_PROJECTS_SAMPLES = {
    "Connections_List": 'var connections = client.GetConnections();\n\nforeach (var conn in connections)\n    Console.WriteLine($"{conn.Name} {conn.ConnectionType}");',
    "Connections_Get": 'var connection = client.GetConnection("my-connection");\n\nConsole.WriteLine($"{connection.Name} {connection.ConnectionType}");',
    "Connections_GetWithCredentials": 'var connection = client.GetConnectionWithCredentials(\n    "my-connection");\n\nConsole.WriteLine(connection.Credentials);',
    "Datasets_ListLatest": 'var datasets = client.GetDatasets();\n\nforeach (var ds in datasets)\n    Console.WriteLine($"{ds.Name} v{ds.Version}");',
    "Datasets_GetVersion": 'var dataset = client.GetDataset("my-dataset", "1");\n\nConsole.WriteLine($"{dataset.Name} v{dataset.Version}");',
    "Datasets_DeleteVersion": 'client.DeleteDataset("my-dataset", "1");',
    "Deployments_List": 'var deployments = client.GetDeployments();\n\nforeach (var d in deployments)\n    Console.WriteLine($"{d.Name} {d.Model}");',
    "Deployments_Get": 'var deployment = client.GetDeployment("gpt-4o");\n\nConsole.WriteLine($"{deployment.Name} {deployment.Model}");',
    "Indexes_ListLatest": 'var indexes = client.GetIndexes();\n\nforeach (var idx in indexes)\n    Console.WriteLine($"{idx.Name} v{idx.Version}");',
    "Indexes_GetVersion": 'var index = client.GetIndex("my-index", "1");\n\nConsole.WriteLine(index.Name);',
    "Indexes_DeleteVersion": 'client.DeleteIndex("my-index", "1");',
}


# ---------------------------------------------------------------------------
# JavaScript/TypeScript samples — OpenAI v1 API (key endpoints)
# ---------------------------------------------------------------------------

JS_OPENAI_SAMPLES = {
    "createResponse": 'const response = await openai.responses.create({\n    model: "gpt-4o",\n    input: "What is the capital of France?",\n});\nconsole.log(response.output_text);',
    "createChatCompletion": 'const response = await openai.chat.completions.create({\n    model: "gpt-4o",\n    messages: [{ role: "user", content: "Hello!" }],\n});\nconsole.log(response.choices[0].message.content);',
    "createCompletion": 'const response = await openai.completions.create({\n    model: "gpt-4o",\n    prompt: "Say hello",\n    max_tokens: 100,\n});\nconsole.log(response.choices[0].text);',
    "createConversation": 'const conversation = await openai.conversations.create({\n    items: [{ type: "message", role: "user", content: "Hello" }],\n});\nconsole.log(conversation.id);',
    "retrieveConversation": 'const conversation = await openai.conversations.retrieve("conv_abc123");\nconsole.log(conversation.id);',
    "deleteConversation": 'await openai.conversations.delete("conv_abc123");',
    "listConversationItems": 'const items = await openai.conversations.items.list("conv_abc123");\nfor await (const item of items) {\n    console.log(item.type, item.id);\n}',
    "createConversationItems": 'await openai.conversations.items.create("conv_abc123", {\n    items: [{ type: "message", role: "user", content: "Follow-up" }],\n});',
    "createEmbedding": 'const response = await openai.embeddings.create({\n    model: "text-embedding-3-large",\n    input: "Sample text to embed",\n});\nconsole.log(response.data[0].embedding.slice(0, 5));',
    "listModels": 'const models = await openai.models.list();\nfor await (const model of models) {\n    console.log(model.id);\n}',
    "retrieveModel": 'const model = await openai.models.retrieve("gpt-4o");\nconsole.log(model.id, model.owned_by);',
    "createFile": 'const file = await openai.files.create({\n    file: fs.createReadStream("data.jsonl"),\n    purpose: "fine-tune",\n});\nconsole.log(file.id);',
    "listFiles": 'const files = await openai.files.list();\nfor await (const f of files) {\n    console.log(f.id, f.filename);\n}',
    "createBatch": 'const batch = await openai.batches.create({\n    input_file_id: "file-abc123",\n    endpoint: "/v1/chat/completions",\n    completion_window: "24h",\n});\nconsole.log(batch.id, batch.status);',
    "listBatches": 'const batches = await openai.batches.list();\nfor await (const b of batches) {\n    console.log(b.id, b.status);\n}',
    "createFineTuningJob": 'const job = await openai.fineTuning.jobs.create({\n    model: "gpt-4o-mini-2024-07-18",\n    training_file: "file-abc123",\n});\nconsole.log(job.id, job.status);',
    "listEvals": 'const evals = await openai.evals.list();\nfor await (const e of evals) {\n    console.log(e.id, e.name);\n}',
    "createRealtimeSession": 'const session = await openai.realtime.sessions.create({\n    model: "gpt-4o-realtime-preview",\n});\nconsole.log(session.id, session.client_secret.value);',
    "listVectorStores": 'const stores = await openai.vectorStores.list();\nfor await (const store of stores) {\n    console.log(store.id, store.name);\n}',
    "createVectorStore": 'const store = await openai.vectorStores.create({\n    name: "my-vector-store",\n});\nconsole.log(store.id);',
    "searchVectorStore": 'const results = await openai.vectorStores.search("vs_abc123", {\n    query: "search query",\n});\nfor await (const result of results) {\n    console.log(result.score, result.content);\n}',
}

JS_PROJECTS_SAMPLES = {
    "Connections_List": 'const connections = await client.connections.list();\nfor await (const conn of connections) {\n    console.log(conn.name, conn.type);\n}',
    "Connections_Get": 'const connection = await client.connections.get("my-connection");\nconsole.log(connection.name, connection.type);',
    "Datasets_ListLatest": 'const datasets = await client.datasets.list();\nfor await (const ds of datasets) {\n    console.log(ds.name, ds.version);\n}',
    "Datasets_GetVersion": 'const dataset = await client.datasets.get("my-dataset", "1");\nconsole.log(dataset.name, dataset.version);',
    "Datasets_DeleteVersion": 'await client.datasets.delete("my-dataset", "1");',
    "Deployments_List": 'const deployments = await client.deployments.list();\nfor await (const d of deployments) {\n    console.log(d.name, d.model);\n}',
    "Deployments_Get": 'const deployment = await client.deployments.get("gpt-4o");\nconsole.log(deployment.name, deployment.model);',
    "Indexes_ListLatest": 'const indexes = await client.indexes.list();\nfor await (const idx of indexes) {\n    console.log(idx.name, idx.version);\n}',
    "Indexes_GetVersion": 'const index = await client.indexes.get("my-index", "1");\nconsole.log(index.name);',
    "Indexes_DeleteVersion": 'await client.indexes.delete("my-index", "1");',
}
