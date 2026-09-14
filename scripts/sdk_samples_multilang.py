"""cURL, C#, and JavaScript/TypeScript SDK samples for OpenAPI x-codeSamples.

This module provides sample dictionaries parallel to the Python samples
in generate_sdk_samples.py, keyed by the same operationId values.
"""

# ---------------------------------------------------------------------------
# Preamble templates
# ---------------------------------------------------------------------------

CURL_OPENAI_PREAMBLE_ENTRA = """\
"""

CURL_OPENAI_PREAMBLE_APIKEY = """\
"""

CURL_PROJECTS_PREAMBLE_ENTRA = """\
"""

CURL_PROJECTS_PREAMBLE_APIKEY = """\
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
    # ── Responses ─────────────────────────────────────────────────────
    "createResponse": (
        'var responsesClient = client.OpenAI\n'
        '    .GetProjectResponsesClientForModel("gpt-4o");\n'
        '\n'
        'var response = await responsesClient\n'
        '    .CreateResponseAsync("What is the capital of France?");\n'
        '\n'
        'Console.WriteLine(response.GetOutputText());'
    ),
    "getResponse": (
        'var responsesClient = client.OpenAI\n'
        '    .GetProjectResponsesClientForModel("gpt-4o");\n'
        '\n'
        'var response = await responsesClient\n'
        '    .GetResponseAsync("resp_abc123");\n'
        '\n'
        'Console.WriteLine(response.Value.Status);'
    ),
    "deleteResponse": (
        'var responsesClient = client.OpenAI\n'
        '    .GetProjectResponsesClientForModel("gpt-4o");\n'
        '\n'
        'await responsesClient.DeleteResponseAsync("resp_abc123");'
    ),
    "cancelResponse": (
        'var responsesClient = client.OpenAI\n'
        '    .GetProjectResponsesClientForModel("gpt-4o");\n'
        '\n'
        'await responsesClient.CancelResponseAsync("resp_abc123");'
    ),
    "listInputItems": (
        'var responsesClient = client.OpenAI\n'
        '    .GetProjectResponsesClientForModel("gpt-4o");\n'
        '\n'
        'var items = responsesClient.GetResponseInputItems("resp_abc123");\n'
        '\n'
        'foreach (var item in items)\n'
        '    Console.WriteLine(item.Id);'
    ),

    # ── Chat ──────────────────────────────────────────────────────────
    "createChatCompletion": (
        'var chatClient = client.OpenAI\n'
        '    .GetProjectChatClientForModel("gpt-4o");\n'
        '\n'
        'var response = await chatClient.CompleteChatAsync(\n'
        '    new ChatMessage[] {\n'
        '        new UserChatMessage("Hello!"),\n'
        '    });\n'
        '\n'
        'Console.WriteLine(response.Value.Content[0].Text);'
    ),
    "createCompletion": (
        'var chatClient = client.OpenAI\n'
        '    .GetProjectChatClientForModel("gpt-4o");\n'
        '\n'
        'var response = await chatClient.CompleteChatAsync(\n'
        '    new ChatMessage[] {\n'
        '        new UserChatMessage("Say hello"),\n'
        '    });\n'
        '\n'
        'Console.WriteLine(response.Value.Content[0].Text);'
    ),

    # ── Conversations ─────────────────────────────────────────────────
    "createConversation": (
        'var conversation = client.OpenAI.Conversations\n'
        '    .CreateProjectConversation();\n'
        '\n'
        'Console.WriteLine(conversation.Id);'
    ),
    "retrieveConversation": (
        'var conversation = client.OpenAI.Conversations\n'
        '    .GetConversation("conv_abc123");\n'
        '\n'
        'Console.WriteLine(conversation.Id);'
    ),
    "updateConversation": (
        'var conversation = client.OpenAI.Conversations\n'
        '    .UpdateConversation("conv_abc123",\n'
        '        new { metadata = new { topic = "geography" } });\n'
        '\n'
        'Console.WriteLine(conversation.Id);'
    ),
    "deleteConversation": (
        'client.OpenAI.Conversations\n'
        '    .DeleteConversation("conv_abc123");'
    ),
    "listConversationItems": (
        'var items = client.OpenAI.Conversations\n'
        '    .GetConversationItems("conv_abc123");\n'
        '\n'
        'foreach (var item in items)\n'
        '    Console.WriteLine($"{item.Type} {item.Id}");'
    ),
    "createConversationItems": (
        'client.OpenAI.Conversations\n'
        '    .CreateConversationItems("conv_abc123",\n'
        '        new { items = new[] {\n'
        '            new { type = "message", role = "user", content = "Follow-up" }\n'
        '        }});'
    ),
    "retrieveConversationItem": (
        'var item = client.OpenAI.Conversations\n'
        '    .GetConversationItem("conv_abc123", "item_abc123");\n'
        '\n'
        'Console.WriteLine(item.Type);'
    ),
    "deleteConversationItem": (
        'client.OpenAI.Conversations\n'
        '    .DeleteConversationItem("conv_abc123", "item_abc123");'
    ),

    # ── Embeddings ────────────────────────────────────────────────────
    "createEmbedding": (
        'var embeddingClient = client.OpenAI\n'
        '    .GetProjectEmbeddingClientForModel("text-embedding-3-large");\n'
        '\n'
        'var response = await embeddingClient\n'
        '    .GenerateEmbeddingAsync("Sample text to embed");\n'
        '\n'
        'Console.WriteLine(response.Value.Vector.Length);'
    ),

    # ── Models ────────────────────────────────────────────────────────
    "listModels": (
        'var models = client.OpenAI.GetOpenAIModelClient()\n'
        '    .GetModels();\n'
        '\n'
        'foreach (var model in models.Value)\n'
        '    Console.WriteLine(model.Id);'
    ),
    "retrieveModel": (
        'var model = client.OpenAI.GetOpenAIModelClient()\n'
        '    .GetModel("gpt-4o");\n'
        '\n'
        'Console.WriteLine($"{model.Value.Id} {model.Value.OwnedBy}");'
    ),
    "deleteModel": (
        'client.OpenAI.GetOpenAIModelClient()\n'
        '    .DeleteModel("ft:gpt-4o:your-org:custom-suffix:id");'
    ),

    # ── Files ─────────────────────────────────────────────────────────
    "createFile": (
        'var fileClient = client.OpenAI.GetOpenAIFileClient();\n'
        '\n'
        'var file = await fileClient.UploadFileAsync(\n'
        '    "data.jsonl", FileUploadPurpose.FineTune);\n'
        '\n'
        'Console.WriteLine(file.Value.Id);'
    ),
    "listFiles": (
        'var fileClient = client.OpenAI.GetOpenAIFileClient();\n'
        'var files = await fileClient.GetFilesAsync();\n'
        '\n'
        'foreach (var f in files.Value)\n'
        '    Console.WriteLine($"{f.Id} {f.Filename}");'
    ),
    "retrieveFile": (
        'var fileClient = client.OpenAI.GetOpenAIFileClient();\n'
        'var file = await fileClient.GetFileAsync("file-abc123");\n'
        '\n'
        'Console.WriteLine($"{file.Value.Filename} {file.Value.Status}");'
    ),
    "deleteFile": (
        'var fileClient = client.OpenAI.GetOpenAIFileClient();\n'
        'await fileClient.DeleteFileAsync("file-abc123");'
    ),
    "downloadFile": (
        'var fileClient = client.OpenAI.GetOpenAIFileClient();\n'
        'var content = await fileClient.DownloadFileAsync("file-abc123");\n'
        '\n'
        'Console.WriteLine(content.Value.ToString());'
    ),

    # ── Batch ─────────────────────────────────────────────────────────
    "createBatch": (
        'var batchClient = client.OpenAI.GetBatchClient();\n'
        '\n'
        'var batch = await batchClient.CreateBatchAsync(\n'
        '    "file-abc123", "/v1/chat/completions", "24h");\n'
        '\n'
        'Console.WriteLine(batch.Value.Id);'
    ),
    "listBatches": (
        'var batchClient = client.OpenAI.GetBatchClient();\n'
        'var batches = batchClient.GetBatches();\n'
        '\n'
        'foreach (var b in batches)\n'
        '    Console.WriteLine($"{b.Id} {b.Status}");'
    ),
    "retrieveBatch": (
        'var batchClient = client.OpenAI.GetBatchClient();\n'
        'var batch = await batchClient.GetBatchAsync("batch_abc123");\n'
        '\n'
        'Console.WriteLine($"{batch.Value.Status}");'
    ),
    "cancelBatch": (
        'var batchClient = client.OpenAI.GetBatchClient();\n'
        'await batchClient.CancelBatchAsync("batch_abc123");'
    ),

    # ── Fine-tuning ───────────────────────────────────────────────────
    "createFineTuningJob": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        '\n'
        'var job = await ftClient.CreateJobAsync(\n'
        '    "gpt-4o-mini-2024-07-18", "file-abc123");\n'
        '\n'
        'Console.WriteLine(job.Value.Id);'
    ),
    "listPaginatedFineTuningJobs": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var jobs = ftClient.GetJobs();\n'
        '\n'
        'foreach (var job in jobs)\n'
        '    Console.WriteLine($"{job.Id} {job.Status}");'
    ),
    "retrieveFineTuningJob": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var job = await ftClient.GetJobAsync("ftjob-abc123");\n'
        '\n'
        'Console.WriteLine($"{job.Value.Status}");'
    ),
    "cancelFineTuningJob": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'await ftClient.CancelJobAsync("ftjob-abc123");'
    ),
    "listFineTuningJobCheckpoints": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var checkpoints = ftClient.GetJobCheckpoints("ftjob-abc123");\n'
        '\n'
        'foreach (var cp in checkpoints)\n'
        '    Console.WriteLine($"{cp.Id} step {cp.StepNumber}");'
    ),
    "listFineTuningEvents": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var events = ftClient.GetJobEvents("ftjob-abc123");\n'
        '\n'
        'foreach (var evt in events)\n'
        '    Console.WriteLine(evt.Message);'
    ),
    "pauseFineTuningJob": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'await ftClient.PauseJobAsync("ftjob-abc123");'
    ),
    "resumeFineTuningJob": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'await ftClient.ResumeJobAsync("ftjob-abc123");'
    ),
    "FineTuning_CopyCheckpoint": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'await ftClient.CopyCheckpointAsync(\n'
        '    "ftjob-abc123", "ftckpt-abc123");'
    ),
    "FineTuning_GetCheckpoint": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var checkpoint = await ftClient.GetCheckpointAsync(\n'
        '    "ftjob-abc123", "ftckpt-abc123");\n'
        '\n'
        'Console.WriteLine(checkpoint.Value.Id);'
    ),
    "listFineTuningCheckpointPermissions": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var permissions = ftClient.GetCheckpointPermissions(\n'
        '    "ft:gpt-4o:org:suffix:id");\n'
        '\n'
        'foreach (var p in permissions)\n'
        '    Console.WriteLine(p.Id);'
    ),
    "createFineTuningCheckpointPermission": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'await ftClient.CreateCheckpointPermissionAsync(\n'
        '    "ft:gpt-4o:org:suffix:id",\n'
        '    new[] { "proj_abc123" });'
    ),
    "deleteFineTuningCheckpointPermission": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'await ftClient.DeleteCheckpointPermissionAsync(\n'
        '    "ft:gpt-4o:org:suffix:id", "perm_abc123");'
    ),
    "runGrader": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var result = await ftClient.RunGraderAsync(\n'
        '    new { type = "python", source = "return 1.0" },\n'
        '    "Hello world");\n'
        '\n'
        'Console.WriteLine(result);'
    ),
    "validateGrader": (
        'var ftClient = client.OpenAI.GetFineTuningClient();\n'
        'var result = await ftClient.ValidateGraderAsync(\n'
        '    new { type = "python", source = "return 1.0" });\n'
        '\n'
        'Console.WriteLine(result);'
    ),

    # ── Evals ─────────────────────────────────────────────────────────
    "listEvals": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var evals = evalClient.GetEvals();\n'
        '\n'
        'foreach (var e in evals)\n'
        '    Console.WriteLine($"{e.Id} {e.Name}");'
    ),
    "createEval": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var evaluation = await evalClient.CreateEvalAsync(\n'
        '    "my-eval",\n'
        '    new { type = "custom", item_schema = new { } },\n'
        '    new object[] { });\n'
        '\n'
        'Console.WriteLine(evaluation.Value.Id);'
    ),
    "getEval": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var evaluation = await evalClient.GetEvalAsync("eval_abc123");\n'
        '\n'
        'Console.WriteLine($"{evaluation.Value.Name}");'
    ),
    "updateEval": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var evaluation = await evalClient.UpdateEvalAsync(\n'
        '    "eval_abc123", name: "updated-name");\n'
        '\n'
        'Console.WriteLine(evaluation.Value.Name);'
    ),
    "deleteEval": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'await evalClient.DeleteEvalAsync("eval_abc123");'
    ),
    "getEvalRuns": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var runs = evalClient.GetEvalRuns("eval_abc123");\n'
        '\n'
        'foreach (var run in runs)\n'
        '    Console.WriteLine($"{run.Id} {run.Status}");'
    ),
    "createEvalRun": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var run = await evalClient.CreateEvalRunAsync(\n'
        '    "eval_abc123", "gpt-4o",\n'
        '    new { type = "completions" });\n'
        '\n'
        'Console.WriteLine(run.Value.Id);'
    ),
    "getEvalRun": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var run = await evalClient.GetEvalRunAsync(\n'
        '    "eval_abc123", "run_abc123");\n'
        '\n'
        'Console.WriteLine(run.Value.Status);'
    ),
    "cancelEvalRun": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'await evalClient.CancelEvalRunAsync(\n'
        '    "eval_abc123", "run_abc123");'
    ),
    "deleteEvalRun": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'await evalClient.DeleteEvalRunAsync(\n'
        '    "eval_abc123", "run_abc123");'
    ),
    "getEvalRunOutputItems": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var items = evalClient.GetEvalRunOutputItems(\n'
        '    "eval_abc123", "run_abc123");\n'
        '\n'
        'foreach (var item in items)\n'
        '    Console.WriteLine(item.Id);'
    ),
    "getEvalRunOutputItem": (
        'var evalClient = client.OpenAI.GetEvalClient();\n'
        'var item = await evalClient.GetEvalRunOutputItemAsync(\n'
        '    "eval_abc123", "run_abc123", "item_abc123");\n'
        '\n'
        'Console.WriteLine(item.Value.Id);'
    ),

    # ── Realtime ──────────────────────────────────────────────────────
    "createRealtimeSession": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'var session = await realtimeClient.CreateSessionAsync(\n'
        '    "gpt-4o-realtime-preview");\n'
        '\n'
        'Console.WriteLine(session.Value.Id);'
    ),
    "createRealtimeClientSecret": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'var secret = await realtimeClient.CreateClientSecretAsync(\n'
        '    "gpt-4o-realtime-preview");\n'
        '\n'
        'Console.WriteLine(secret.Value.ClientSecret.Value);'
    ),
    "createRealtimeTranscriptionSession": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'var session = await realtimeClient\n'
        '    .CreateTranscriptionSessionAsync("gpt-4o-transcribe");\n'
        '\n'
        'Console.WriteLine(session.Value.Id);'
    ),
    "createRealtimeCall": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'var call = await realtimeClient.CreateCallAsync(\n'
        '    "gpt-4o-realtime-preview", "YOUR_SDP_OFFER");\n'
        '\n'
        'Console.WriteLine(call.Value.Id);'
    ),
    "acceptRealtimeCall": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'await realtimeClient.AcceptCallAsync(\n'
        '    "call_abc123", "gpt-4o-realtime-preview");'
    ),
    "hangupRealtimeCall": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'await realtimeClient.HangupCallAsync("call_abc123");'
    ),
    "referRealtimeCall": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'await realtimeClient.ReferCallAsync(\n'
        '    "call_abc123", "sip:destination@example.com");'
    ),
    "rejectRealtimeCall": (
        'var realtimeClient = client.OpenAI.GetRealtimeClient();\n'
        'await realtimeClient.RejectCallAsync(\n'
        '    "call_abc123", "busy");'
    ),

    # ── Containers ────────────────────────────────────────────────────
    "listContainers": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'var containers = containerClient.GetContainers();\n'
        '\n'
        'foreach (var c in containers)\n'
        '    Console.WriteLine($"{c.Id} {c.Name}");'
    ),
    "createContainer": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'var container = await containerClient\n'
        '    .CreateContainerAsync("my-container");\n'
        '\n'
        'Console.WriteLine(container.Value.Id);'
    ),
    "retrieveContainer": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'var container = await containerClient\n'
        '    .GetContainerAsync("container_abc123");\n'
        '\n'
        'Console.WriteLine(container.Value.Name);'
    ),
    "deleteContainer": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'await containerClient.DeleteContainerAsync("container_abc123");'
    ),
    "listContainerFiles": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'var files = containerClient\n'
        '    .GetContainerFiles("container_abc123");\n'
        '\n'
        'foreach (var f in files)\n'
        '    Console.WriteLine($"{f.Id} {f.Path}");'
    ),
    "createContainerFile": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'var file = await containerClient.CreateContainerFileAsync(\n'
        '    "container_abc123",\n'
        '    File.OpenRead("data.txt"), "data.txt");\n'
        '\n'
        'Console.WriteLine(file.Value.Id);'
    ),
    "retrieveContainerFile": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'var file = await containerClient.GetContainerFileAsync(\n'
        '    "container_abc123", "file_abc123");\n'
        '\n'
        'Console.WriteLine(file.Value.Path);'
    ),
    "deleteContainerFile": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'await containerClient.DeleteContainerFileAsync(\n'
        '    "container_abc123", "file_abc123");'
    ),
    "retrieveContainerFileContent": (
        'var containerClient = client.OpenAI.GetContainerClient();\n'
        'var content = await containerClient\n'
        '    .GetContainerFileContentAsync(\n'
        '        "container_abc123", "file_abc123");\n'
        '\n'
        'Console.WriteLine(content.Value.ToString());'
    ),

    # ── Threads (legacy) ──────────────────────────────────────────────
    "createThread": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var thread = await threadClient.CreateThreadAsync();\n'
        '\n'
        'Console.WriteLine(thread.Value.Id);'
    ),
    "retrieveThread": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var thread = await threadClient.GetThreadAsync("thread_abc123");\n'
        '\n'
        'Console.WriteLine(thread.Value.Id);'
    ),
    "modifyThread": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'await threadClient.ModifyThreadAsync("thread_abc123",\n'
        '    new ThreadModificationOptions\n'
        '    {\n'
        '        Metadata = { ["topic"] = "science" },\n'
        '    });'
    ),
    "deleteThread": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'await threadClient.DeleteThreadAsync("thread_abc123");'
    ),
    "createMessage": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var message = await threadClient.CreateMessageAsync(\n'
        '    "thread_abc123", MessageRole.User,\n'
        '    new[] { MessageContent.FromText("What is the capital of France?") });\n'
        '\n'
        'Console.WriteLine(message.Value.Id);'
    ),
    "listMessages": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var messages = threadClient.GetMessages("thread_abc123");\n'
        '\n'
        'foreach (var msg in messages)\n'
        '    Console.WriteLine($"{msg.Role} {msg.Content[0].Text}");'
    ),
    "retrieveMessage": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var message = await threadClient.GetMessageAsync(\n'
        '    "thread_abc123", "msg_abc123");\n'
        '\n'
        'Console.WriteLine(message.Value.Content[0].Text);'
    ),
    "modifyMessage": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'await threadClient.ModifyMessageAsync(\n'
        '    "thread_abc123", "msg_abc123",\n'
        '    new MessageModificationOptions\n'
        '    {\n'
        '        Metadata = { ["reviewed"] = "true" },\n'
        '    });'
    ),
    "deleteMessage": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'await threadClient.DeleteMessageAsync(\n'
        '    "thread_abc123", "msg_abc123");'
    ),
    "createRun": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var run = await threadClient.CreateRunAsync(\n'
        '    "thread_abc123", "asst_abc123");\n'
        '\n'
        'Console.WriteLine($"{run.Value.Id} {run.Value.Status}");'
    ),
    "createThreadAndRun": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var run = await threadClient.CreateThreadAndRunAsync(\n'
        '    "asst_abc123",\n'
        '    new ThreadCreationOptions\n'
        '    {\n'
        '        InitialMessages = { new ThreadInitializationMessage(\n'
        '            MessageRole.User, new[] { MessageContent.FromText("Hello") }) },\n'
        '    });\n'
        '\n'
        'Console.WriteLine(run.Value.Id);'
    ),
    "listRuns": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var runs = threadClient.GetRuns("thread_abc123");\n'
        '\n'
        'foreach (var run in runs)\n'
        '    Console.WriteLine($"{run.Id} {run.Status}");'
    ),
    "retrieveRun": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var run = await threadClient.GetRunAsync(\n'
        '    "thread_abc123", "run_abc123");\n'
        '\n'
        'Console.WriteLine(run.Value.Status);'
    ),
    "modifyRun": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'await threadClient.ModifyRunAsync(\n'
        '    "thread_abc123", "run_abc123",\n'
        '    new RunModificationOptions\n'
        '    {\n'
        '        Metadata = { ["priority"] = "high" },\n'
        '    });'
    ),
    "cancelRun": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'await threadClient.CancelRunAsync(\n'
        '    "thread_abc123", "run_abc123");'
    ),
    "submitToolOutputsToRun": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var run = await threadClient.SubmitToolOutputsToRunAsync(\n'
        '    "thread_abc123", "run_abc123",\n'
        '    new[] { new ToolOutput("call_abc123", "result") });\n'
        '\n'
        'Console.WriteLine(run.Value.Status);'
    ),
    "listRunSteps": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var steps = threadClient.GetRunSteps(\n'
        '    "thread_abc123", "run_abc123");\n'
        '\n'
        'foreach (var step in steps)\n'
        '    Console.WriteLine($"{step.Id} {step.Type}");'
    ),
    "getRunStep": (
        'var threadClient = client.OpenAI.GetAssistantClient();\n'
        'var step = await threadClient.GetRunStepAsync(\n'
        '    "thread_abc123", "run_abc123", "step_abc123");\n'
        '\n'
        'Console.WriteLine($"{step.Value.Type} {step.Value.Status}");'
    ),

    # ── Vector Stores ─────────────────────────────────────────────────
    "listVectorStores": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var stores = vsClient.GetVectorStores();\n'
        '\n'
        'foreach (var store in stores)\n'
        '    Console.WriteLine($"{store.Id} {store.Name}");'
    ),
    "createVectorStore": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        '\n'
        'var store = await vsClient.CreateVectorStoreAsync(\n'
        '    new VectorStoreCreationOptions { Name = "my-store" });\n'
        '\n'
        'Console.WriteLine(store.Value.Id);'
    ),
    "getVectorStore": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var store = await vsClient.GetVectorStoreAsync("vs_abc123");\n'
        '\n'
        'Console.WriteLine($"{store.Value.Name}");'
    ),
    "modifyVectorStore": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'await vsClient.ModifyVectorStoreAsync("vs_abc123",\n'
        '    new VectorStoreModificationOptions { Name = "updated-name" });'
    ),
    "deleteVectorStore": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'await vsClient.DeleteVectorStoreAsync("vs_abc123");'
    ),
    "searchVectorStore": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var results = vsClient.SearchVectorStore(\n'
        '    "vs_abc123", "search query");\n'
        '\n'
        'foreach (var result in results)\n'
        '    Console.WriteLine($"{result.Score} {result.Content}");'
    ),
    "listVectorStoreFiles": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var files = vsClient.GetVectorStoreFiles("vs_abc123");\n'
        '\n'
        'foreach (var f in files)\n'
        '    Console.WriteLine($"{f.Id} {f.Status}");'
    ),
    "createVectorStoreFile": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var file = await vsClient.AddFileToVectorStoreAsync(\n'
        '    "vs_abc123", "file_abc123");\n'
        '\n'
        'Console.WriteLine($"{file.Value.Id} {file.Value.Status}");'
    ),
    "getVectorStoreFile": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var file = await vsClient.GetVectorStoreFileAsync(\n'
        '    "vs_abc123", "file_abc123");\n'
        '\n'
        'Console.WriteLine(file.Value.Status);'
    ),
    "updateVectorStoreFileAttributes": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'await vsClient.UpdateVectorStoreFileAttributesAsync(\n'
        '    "vs_abc123", "file_abc123",\n'
        '    new { key = "value" });'
    ),
    "deleteVectorStoreFile": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'await vsClient.RemoveFileFromVectorStoreAsync(\n'
        '    "vs_abc123", "file_abc123");'
    ),
    "retrieveVectorStoreFileContent": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var content = await vsClient\n'
        '    .GetVectorStoreFileContentAsync(\n'
        '        "vs_abc123", "file_abc123");\n'
        '\n'
        'Console.WriteLine(content.Value.ToString());'
    ),
    "createVectorStoreFileBatch": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var batch = await vsClient.CreateBatchFileJobAsync(\n'
        '    "vs_abc123",\n'
        '    new[] { "file_abc123", "file_def456" });\n'
        '\n'
        'Console.WriteLine($"{batch.Value.BatchId} {batch.Value.Status}");'
    ),
    "getVectorStoreFileBatch": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var batch = await vsClient.GetBatchFileJobAsync(\n'
        '    "vs_abc123", "vsfb_abc123");\n'
        '\n'
        'Console.WriteLine(batch.Value.Status);'
    ),
    "cancelVectorStoreFileBatch": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'await vsClient.CancelBatchFileJobAsync(\n'
        '    "vs_abc123", "vsfb_abc123");'
    ),
    "listFilesInVectorStoreBatch": (
        'var vsClient = client.OpenAI.GetVectorStoreClient();\n'
        'var files = vsClient.GetFileAssociations(\n'
        '    "vs_abc123", "vsfb_abc123");\n'
        '\n'
        'foreach (var f in files)\n'
        '    Console.WriteLine($"{f.Id} {f.Status}");'
    ),

    # ── Audio ─────────────────────────────────────────────────────────
    "createSpeech": (
        'var audioClient = client.OpenAI.GetAudioClient("tts-1");\n'
        'var result = await audioClient.GenerateSpeechAsync(\n'
        '    "Hello, how are you today?", GeneratedSpeechVoice.Alloy);\n'
        '\n'
        'await File.WriteAllBytesAsync(\n'
        '    "output.mp3", result.Value.ToArray());'
    ),
    "createTranscription": (
        'var audioClient = client.OpenAI.GetAudioClient("whisper-1");\n'
        'var result = await audioClient.TranscribeAudioAsync(\n'
        '    "audio.mp3");\n'
        '\n'
        'Console.WriteLine(result.Value.Text);'
    ),
    "createTranslation": (
        'var audioClient = client.OpenAI.GetAudioClient("whisper-1");\n'
        'var result = await audioClient.TranslateAudioAsync(\n'
        '    "audio.mp3");\n'
        '\n'
        'Console.WriteLine(result.Value.Text);'
    ),

    # ── Images ────────────────────────────────────────────────────────
    "createImage": (
        'var imageClient = client.OpenAI.GetImageClient("dall-e-3");\n'
        'var result = await imageClient.GenerateImageAsync(\n'
        '    "A white cat sitting on a windowsill",\n'
        '    new ImageGenerationOptions { Size = GeneratedImageSize.W1024xH1024 });\n'
        '\n'
        'Console.WriteLine(result.Value.ImageUri);'
    ),
    "createImageEdit": (
        'var imageClient = client.OpenAI.GetImageClient("dall-e-2");\n'
        'var result = await imageClient.GenerateImageEditAsync(\n'
        '    File.OpenRead("image.png"),\n'
        '    "image.png",\n'
        '    "Add a sunset in the background",\n'
        '    new ImageEditOptions { Size = GeneratedImageSize.W1024xH1024 });\n'
        '\n'
        'Console.WriteLine(result.Value.ImageUri);'
    ),
    "createImageVariation": (
        'var imageClient = client.OpenAI.GetImageClient("dall-e-2");\n'
        'var result = await imageClient.GenerateImageVariationAsync(\n'
        '    File.OpenRead("image.png"),\n'
        '    "image.png",\n'
        '    new ImageVariationOptions { Size = GeneratedImageSize.W1024xH1024 });\n'
        '\n'
        'Console.WriteLine(result.Value.ImageUri);'
    ),

    # ── Video ─────────────────────────────────────────────────────────
    "Videos_Create": (
        'var videoClient = client.OpenAI.GetVideoClient();\n'
        'var job = await videoClient.CreateVideoAsync(\n'
        '    "sora", "A serene mountain landscape at sunset");\n'
        '\n'
        'Console.WriteLine($"{job.Value.Id} {job.Value.Status}");'
    ),
    "Videos_List": (
        'var videoClient = client.OpenAI.GetVideoClient();\n'
        'var videos = videoClient.GetVideos();\n'
        '\n'
        'foreach (var v in videos)\n'
        '    Console.WriteLine($"{v.Id} {v.Status}");'
    ),
    "Videos_Get": (
        'var videoClient = client.OpenAI.GetVideoClient();\n'
        'var video = await videoClient.GetVideoAsync("video_abc123");\n'
        '\n'
        'Console.WriteLine(video.Value.Status);'
    ),
    "Videos_Delete": (
        'var videoClient = client.OpenAI.GetVideoClient();\n'
        'await videoClient.DeleteVideoAsync("video_abc123");'
    ),
    "Videos_RetrieveContent": (
        'var videoClient = client.OpenAI.GetVideoClient();\n'
        'var content = await videoClient\n'
        '    .GetVideoContentAsync("video_abc123");\n'
        '\n'
        'Console.WriteLine(content.Value.Url);'
    ),
    "Videos_Remix": (
        'var videoClient = client.OpenAI.GetVideoClient();\n'
        'var job = await videoClient.RemixVideoAsync(\n'
        '    "video_abc123", "Make it a night scene");\n'
        '\n'
        'Console.WriteLine(job.Value.Id);'
    ),
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
    "Datasets_ListVersions": 'var versions = client.GetDatasetVersions("my-dataset");\n\nforeach (var v in versions)\n    Console.WriteLine($"v{v.Version} {v.CreatedDate}");',
    "Datasets_CreateOrUpdateVersion": 'var dataset = client.CreateOrUpdateDataset(\n    "my-dataset", "1",\n    new DatasetVersionOptions { Description = "Training data" });\n\nConsole.WriteLine(dataset.Name);',
    "Datasets_GetCredentials": 'var creds = client.GetDatasetCredentials("my-dataset", "1");\n\nConsole.WriteLine(creds.CredentialType);',
    "Datasets_StartPendingUploadVersion": 'var upload = client.StartPendingDatasetUpload(\n    "my-dataset", "1",\n    new PendingUploadOptions { PendingUploadType = "temporary_sas" });\n\nConsole.WriteLine(upload.BlobReference);',
    "Indexes_ListVersions": 'var versions = client.GetIndexVersions("my-index");\n\nforeach (var v in versions)\n    Console.WriteLine(v.Version);',
    "Indexes_CreateOrUpdateVersion": 'var index = client.CreateOrUpdateIndex(\n    "my-index", "1",\n    new IndexVersionOptions { Description = "Search index" });\n\nConsole.WriteLine(index.Name);',
    "Evaluations_List": 'var runs = client.GetEvaluations();\n\nforeach (var run in runs)\n    Console.WriteLine($"{run.Name} {run.Status}");',
    "Evaluations_Get": 'var run = client.GetEvaluation("my-eval-run");\n\nConsole.WriteLine($"{run.Name} {run.Status}");',
    "Evaluations_Delete": 'client.DeleteEvaluation("my-eval-run");',
    "Evaluations_Cancel": 'client.CancelEvaluation("my-eval-run");',
    "Evaluations_Create": 'var run = client.CreateEvaluation(new EvaluationOptions\n{\n    DisplayName = "my-eval-run",\n    Evaluators = { ["relevance"] = new EvaluatorConfig("relevance") },\n    Data = new DatasetConfig("my-dataset:1"),\n});\n\nConsole.WriteLine(run.Name);',
    "Evaluations_CreateAgentEvaluation": 'var run = client.CreateAgentEvaluation(\n    new AgentEvaluationOptions\n    {\n        DisplayName = "agent-eval",\n        Evaluators = { ["relevance"] = new EvaluatorConfig("relevance") },\n        Target = new AgentTarget("my-agent:1"),\n    });\n\nConsole.WriteLine(run.Name);',
    "RedTeams_List": 'var runs = client.GetRedTeams();\n\nforeach (var run in runs)\n    Console.WriteLine($"{run.Name} {run.Status}");',
    "RedTeams_Get": 'var run = client.GetRedTeam("my-redteam-run");\n\nConsole.WriteLine($"{run.Name} {run.Status}");',
    "RedTeams_Create": 'var run = client.CreateRedTeam(new RedTeamOptions\n{\n    DisplayName = "my-redteam",\n    Target = new AgentTarget("my-agent:1"),\n    RiskCategories = { "violence", "hate" },\n});\n\nConsole.WriteLine(run.Name);',
}


# ---------------------------------------------------------------------------
# JavaScript/TypeScript samples — OpenAI v1 API (key endpoints)
# ---------------------------------------------------------------------------

JS_OPENAI_SAMPLES = {
    # ── Responses ─────────────────────────────────────────────────────
    "createResponse": (
        'const response = await openai.responses.create({\n'
        '    model: "gpt-4o",\n'
        '    input: "What is the capital of France?",\n'
        '});\n'
        'console.log(response.output_text);'
    ),
    "getResponse": (
        'const response = await openai.responses.retrieve("resp_abc123");\n'
        'console.log(response.status, response.output_text);'
    ),
    "deleteResponse": 'await openai.responses.delete("resp_abc123");',
    "cancelResponse": 'await openai.responses.cancel("resp_abc123");',
    "listInputItems": (
        'const items = await openai.responses.inputItems.list("resp_abc123");\n'
        'for await (const item of items) {\n'
        '    console.log(item.type, item.id);\n'
        '}'
    ),

    # ── Chat ──────────────────────────────────────────────────────────
    "createChatCompletion": (
        'const response = await openai.chat.completions.create({\n'
        '    model: "gpt-4o",\n'
        '    messages: [{ role: "user", content: "Hello!" }],\n'
        '});\n'
        'console.log(response.choices[0].message.content);'
    ),
    "createCompletion": (
        'const response = await openai.completions.create({\n'
        '    model: "gpt-4o",\n'
        '    prompt: "Say hello",\n'
        '    max_tokens: 100,\n'
        '});\n'
        'console.log(response.choices[0].text);'
    ),

    # ── Conversations ─────────────────────────────────────────────────
    "createConversation": (
        'const conversation = await openai.conversations.create({\n'
        '    items: [{ type: "message", role: "user", content: "Hello" }],\n'
        '});\n'
        'console.log(conversation.id);'
    ),
    "retrieveConversation": (
        'const conversation = await openai.conversations.retrieve("conv_abc123");\n'
        'console.log(conversation.id);'
    ),
    "updateConversation": (
        'const conversation = await openai.conversations.update("conv_abc123", {\n'
        '    metadata: { topic: "geography" },\n'
        '});\n'
        'console.log(conversation.id);'
    ),
    "deleteConversation": 'await openai.conversations.delete("conv_abc123");',
    "listConversationItems": (
        'const items = await openai.conversations.items.list("conv_abc123");\n'
        'for await (const item of items) {\n'
        '    console.log(item.type, item.id);\n'
        '}'
    ),
    "createConversationItems": (
        'await openai.conversations.items.create("conv_abc123", {\n'
        '    items: [{ type: "message", role: "user", content: "Follow-up" }],\n'
        '});'
    ),
    "retrieveConversationItem": (
        'const item = await openai.conversations.items.retrieve(\n'
        '    "conv_abc123", "item_abc123"\n'
        ');\n'
        'console.log(item.type);'
    ),
    "deleteConversationItem": (
        'await openai.conversations.items.delete(\n'
        '    "conv_abc123", "item_abc123"\n'
        ');'
    ),

    # ── Embeddings ────────────────────────────────────────────────────
    "createEmbedding": (
        'const response = await openai.embeddings.create({\n'
        '    model: "text-embedding-3-large",\n'
        '    input: "Sample text to embed",\n'
        '});\n'
        'console.log(response.data[0].embedding.slice(0, 5));'
    ),

    # ── Models ────────────────────────────────────────────────────────
    "listModels": (
        'const models = await openai.models.list();\n'
        'for await (const model of models) {\n'
        '    console.log(model.id);\n'
        '}'
    ),
    "retrieveModel": (
        'const model = await openai.models.retrieve("gpt-4o");\n'
        'console.log(model.id, model.owned_by);'
    ),
    "deleteModel": 'await openai.models.delete("ft:gpt-4o:your-org:custom-suffix:id");',

    # ── Files ─────────────────────────────────────────────────────────
    "createFile": (
        'const file = await openai.files.create({\n'
        '    file: fs.createReadStream("data.jsonl"),\n'
        '    purpose: "fine-tune",\n'
        '});\n'
        'console.log(file.id);'
    ),
    "listFiles": (
        'const files = await openai.files.list();\n'
        'for await (const f of files) {\n'
        '    console.log(f.id, f.filename);\n'
        '}'
    ),
    "retrieveFile": (
        'const file = await openai.files.retrieve("file-abc123");\n'
        'console.log(file.filename, file.status);'
    ),
    "deleteFile": 'await openai.files.delete("file-abc123");',
    "downloadFile": (
        'const content = await openai.files.content("file-abc123");\n'
        'console.log(await content.text());'
    ),

    # ── Batch ─────────────────────────────────────────────────────────
    "createBatch": (
        'const batch = await openai.batches.create({\n'
        '    input_file_id: "file-abc123",\n'
        '    endpoint: "/v1/chat/completions",\n'
        '    completion_window: "24h",\n'
        '});\n'
        'console.log(batch.id, batch.status);'
    ),
    "listBatches": (
        'const batches = await openai.batches.list();\n'
        'for await (const b of batches) {\n'
        '    console.log(b.id, b.status);\n'
        '}'
    ),
    "retrieveBatch": (
        'const batch = await openai.batches.retrieve("batch_abc123");\n'
        'console.log(batch.status, batch.request_counts);'
    ),
    "cancelBatch": 'await openai.batches.cancel("batch_abc123");',

    # ── Fine-tuning ───────────────────────────────────────────────────
    "createFineTuningJob": (
        'const job = await openai.fineTuning.jobs.create({\n'
        '    model: "gpt-4o-mini-2024-07-18",\n'
        '    training_file: "file-abc123",\n'
        '});\n'
        'console.log(job.id, job.status);'
    ),
    "listPaginatedFineTuningJobs": (
        'const jobs = await openai.fineTuning.jobs.list();\n'
        'for await (const job of jobs) {\n'
        '    console.log(job.id, job.status);\n'
        '}'
    ),
    "retrieveFineTuningJob": (
        'const job = await openai.fineTuning.jobs.retrieve("ftjob-abc123");\n'
        'console.log(job.status, job.trained_tokens);'
    ),
    "cancelFineTuningJob": 'await openai.fineTuning.jobs.cancel("ftjob-abc123");',
    "listFineTuningJobCheckpoints": (
        'const checkpoints = await openai.fineTuning.jobs.checkpoints\n'
        '    .list("ftjob-abc123");\n'
        'for await (const cp of checkpoints) {\n'
        '    console.log(cp.id, cp.step_number);\n'
        '}'
    ),
    "listFineTuningEvents": (
        'const events = await openai.fineTuning.jobs.listEvents("ftjob-abc123");\n'
        'for await (const event of events) {\n'
        '    console.log(event.message);\n'
        '}'
    ),
    "pauseFineTuningJob": 'await openai.fineTuning.jobs.pause("ftjob-abc123");',
    "resumeFineTuningJob": 'await openai.fineTuning.jobs.resume("ftjob-abc123");',
    "FineTuning_CopyCheckpoint": (
        'await openai.fineTuning.jobs.checkpoints.copy(\n'
        '    "ftjob-abc123", "ftckpt-abc123"\n'
        ');'
    ),
    "FineTuning_GetCheckpoint": (
        'const checkpoint = await openai.fineTuning.jobs.checkpoints\n'
        '    .retrieve("ftjob-abc123", "ftckpt-abc123");\n'
        'console.log(checkpoint.id);'
    ),
    "listFineTuningCheckpointPermissions": (
        'const permissions = await openai.fineTuning.checkpoints\n'
        '    .permissions.list("ft:gpt-4o:org:suffix:id");\n'
        'for await (const p of permissions) {\n'
        '    console.log(p.id);\n'
        '}'
    ),
    "createFineTuningCheckpointPermission": (
        'await openai.fineTuning.checkpoints.permissions.create(\n'
        '    "ft:gpt-4o:org:suffix:id",\n'
        '    { project_ids: ["proj_abc123"] }\n'
        ');'
    ),
    "deleteFineTuningCheckpointPermission": (
        'await openai.fineTuning.checkpoints.permissions.delete(\n'
        '    "ft:gpt-4o:org:suffix:id", "perm_abc123"\n'
        ');'
    ),
    "runGrader": (
        'const result = await openai.fineTuning.alpha.graders.run({\n'
        '    grader: { type: "python", source: "return 1.0" },\n'
        '    model_sample: "Hello world",\n'
        '});\n'
        'console.log(result);'
    ),
    "validateGrader": (
        'const result = await openai.fineTuning.alpha.graders.validate({\n'
        '    grader: { type: "python", source: "return 1.0" },\n'
        '});\n'
        'console.log(result);'
    ),

    # ── Evals ─────────────────────────────────────────────────────────
    "listEvals": (
        'const evals = await openai.evals.list();\n'
        'for await (const e of evals) {\n'
        '    console.log(e.id, e.name);\n'
        '}'
    ),
    "createEval": (
        'const evaluation = await openai.evals.create({\n'
        '    name: "my-eval",\n'
        '    data_source_config: { type: "custom", item_schema: {} },\n'
        '    testing_criteria: [],\n'
        '});\n'
        'console.log(evaluation.id);'
    ),
    "getEval": (
        'const evaluation = await openai.evals.retrieve("eval_abc123");\n'
        'console.log(evaluation.name, evaluation.id);'
    ),
    "updateEval": (
        'const evaluation = await openai.evals.update("eval_abc123", {\n'
        '    name: "updated-name",\n'
        '});\n'
        'console.log(evaluation.name);'
    ),
    "deleteEval": 'await openai.evals.delete("eval_abc123");',
    "getEvalRuns": (
        'const runs = await openai.evals.runs.list("eval_abc123");\n'
        'for await (const run of runs) {\n'
        '    console.log(run.id, run.status);\n'
        '}'
    ),
    "createEvalRun": (
        'const run = await openai.evals.runs.create("eval_abc123", {\n'
        '    model: "gpt-4o",\n'
        '    data_source: { type: "completions" },\n'
        '});\n'
        'console.log(run.id);'
    ),
    "getEvalRun": (
        'const run = await openai.evals.runs.retrieve(\n'
        '    "eval_abc123", "run_abc123"\n'
        ');\n'
        'console.log(run.status);'
    ),
    "cancelEvalRun": 'await openai.evals.runs.cancel("eval_abc123", "run_abc123");',
    "deleteEvalRun": 'await openai.evals.runs.delete("eval_abc123", "run_abc123");',
    "getEvalRunOutputItems": (
        'const items = await openai.evals.runs.outputItems\n'
        '    .list("eval_abc123", "run_abc123");\n'
        'for await (const item of items) {\n'
        '    console.log(item.id);\n'
        '}'
    ),
    "getEvalRunOutputItem": (
        'const item = await openai.evals.runs.outputItems\n'
        '    .retrieve("eval_abc123", "run_abc123", "item_abc123");\n'
        'console.log(item.id);'
    ),

    # ── Realtime ──────────────────────────────────────────────────────
    "createRealtimeSession": (
        'const session = await openai.realtime.sessions.create({\n'
        '    model: "gpt-4o-realtime-preview",\n'
        '});\n'
        'console.log(session.id, session.client_secret.value);'
    ),
    "createRealtimeClientSecret": (
        'const secret = await openai.realtime.clientSecrets.create({\n'
        '    model: "gpt-4o-realtime-preview",\n'
        '});\n'
        'console.log(secret.client_secret.value);'
    ),
    "createRealtimeTranscriptionSession": (
        'const session = await openai.realtime.transcriptionSessions\n'
        '    .create({ model: "gpt-4o-transcribe" });\n'
        'console.log(session.id);'
    ),
    "createRealtimeCall": (
        'const call = await openai.realtime.calls.create({\n'
        '    model: "gpt-4o-realtime-preview",\n'
        '    sdp: "YOUR_SDP_OFFER",\n'
        '});\n'
        'console.log(call.id, call.sdp);'
    ),
    "acceptRealtimeCall": (
        'await openai.realtime.calls.accept("call_abc123", {\n'
        '    model: "gpt-4o-realtime-preview",\n'
        '});'
    ),
    "hangupRealtimeCall": 'await openai.realtime.calls.hangup("call_abc123");',
    "referRealtimeCall": (
        'await openai.realtime.calls.refer("call_abc123", {\n'
        '    refer_to: "sip:destination@example.com",\n'
        '});'
    ),
    "rejectRealtimeCall": (
        'await openai.realtime.calls.reject("call_abc123", {\n'
        '    reason: "busy",\n'
        '});'
    ),

    # ── Containers ────────────────────────────────────────────────────
    "listContainers": (
        'const containers = await openai.containers.list();\n'
        'for await (const c of containers) {\n'
        '    console.log(c.id, c.name);\n'
        '}'
    ),
    "createContainer": (
        'const container = await openai.containers.create({\n'
        '    name: "my-container",\n'
        '});\n'
        'console.log(container.id);'
    ),
    "retrieveContainer": (
        'const container = await openai.containers.retrieve("container_abc123");\n'
        'console.log(container.name);'
    ),
    "deleteContainer": 'await openai.containers.delete("container_abc123");',
    "listContainerFiles": (
        'const files = await openai.containers.files.list("container_abc123");\n'
        'for await (const f of files) {\n'
        '    console.log(f.id, f.path);\n'
        '}'
    ),
    "createContainerFile": (
        'const file = await openai.containers.files.create("container_abc123", {\n'
        '    file: fs.createReadStream("data.txt"),\n'
        '    file_path: "data.txt",\n'
        '});\n'
        'console.log(file.id);'
    ),
    "retrieveContainerFile": (
        'const file = await openai.containers.files.retrieve(\n'
        '    "container_abc123", "file_abc123"\n'
        ');\n'
        'console.log(file.path);'
    ),
    "deleteContainerFile": (
        'await openai.containers.files.delete(\n'
        '    "container_abc123", "file_abc123"\n'
        ');'
    ),
    "retrieveContainerFileContent": (
        'const content = await openai.containers.files.content(\n'
        '    "container_abc123", "file_abc123"\n'
        ');\n'
        'console.log(await content.text());'
    ),

    # ── Threads (legacy) ──────────────────────────────────────────────
    "createThread": (
        'const thread = await openai.beta.threads.create();\n'
        'console.log(thread.id);'
    ),
    "retrieveThread": (
        'const thread = await openai.beta.threads.retrieve("thread_abc123");\n'
        'console.log(thread.id);'
    ),
    "modifyThread": (
        'const thread = await openai.beta.threads.update("thread_abc123", {\n'
        '    metadata: { topic: "science" },\n'
        '});\n'
        'console.log(thread.id);'
    ),
    "deleteThread": 'await openai.beta.threads.delete("thread_abc123");',
    "createMessage": (
        'const message = await openai.beta.threads.messages.create(\n'
        '    "thread_abc123",\n'
        '    { role: "user", content: "What is the capital of France?" }\n'
        ');\n'
        'console.log(message.id);'
    ),
    "listMessages": (
        'const messages = await openai.beta.threads.messages.list("thread_abc123");\n'
        'for await (const msg of messages) {\n'
        '    console.log(msg.role, msg.content[0].text.value);\n'
        '}'
    ),
    "retrieveMessage": (
        'const message = await openai.beta.threads.messages.retrieve(\n'
        '    "thread_abc123", "msg_abc123"\n'
        ');\n'
        'console.log(message.content[0].text.value);'
    ),
    "modifyMessage": (
        'await openai.beta.threads.messages.update(\n'
        '    "thread_abc123", "msg_abc123",\n'
        '    { metadata: { reviewed: "true" } }\n'
        ');'
    ),
    "deleteMessage": (
        'await openai.beta.threads.messages.delete(\n'
        '    "thread_abc123", "msg_abc123"\n'
        ');'
    ),
    "createRun": (
        'const run = await openai.beta.threads.runs.create("thread_abc123", {\n'
        '    assistant_id: "asst_abc123",\n'
        '});\n'
        'console.log(run.id, run.status);'
    ),
    "createThreadAndRun": (
        'const run = await openai.beta.threads.createAndRun({\n'
        '    assistant_id: "asst_abc123",\n'
        '    thread: { messages: [{ role: "user", content: "Hello" }] },\n'
        '});\n'
        'console.log(run.id);'
    ),
    "listRuns": (
        'const runs = await openai.beta.threads.runs.list("thread_abc123");\n'
        'for await (const run of runs) {\n'
        '    console.log(run.id, run.status);\n'
        '}'
    ),
    "retrieveRun": (
        'const run = await openai.beta.threads.runs.retrieve(\n'
        '    "thread_abc123", "run_abc123"\n'
        ');\n'
        'console.log(run.status);'
    ),
    "modifyRun": (
        'await openai.beta.threads.runs.update(\n'
        '    "thread_abc123", "run_abc123",\n'
        '    { metadata: { priority: "high" } }\n'
        ');'
    ),
    "cancelRun": (
        'await openai.beta.threads.runs.cancel(\n'
        '    "thread_abc123", "run_abc123"\n'
        ');'
    ),
    "submitToolOutputsToRun": (
        'const run = await openai.beta.threads.runs.submitToolOutputs(\n'
        '    "thread_abc123", "run_abc123",\n'
        '    { tool_outputs: [{ tool_call_id: "call_abc123", output: "result" }] }\n'
        ');\n'
        'console.log(run.status);'
    ),
    "listRunSteps": (
        'const steps = await openai.beta.threads.runs.steps.list(\n'
        '    "thread_abc123", "run_abc123"\n'
        ');\n'
        'for await (const step of steps) {\n'
        '    console.log(step.id, step.type);\n'
        '}'
    ),
    "getRunStep": (
        'const step = await openai.beta.threads.runs.steps.retrieve(\n'
        '    "thread_abc123", "run_abc123", "step_abc123"\n'
        ');\n'
        'console.log(step.type, step.status);'
    ),

    # ── Vector Stores ─────────────────────────────────────────────────
    "listVectorStores": (
        'const stores = await openai.vectorStores.list();\n'
        'for await (const store of stores) {\n'
        '    console.log(store.id, store.name);\n'
        '}'
    ),
    "createVectorStore": (
        'const store = await openai.vectorStores.create({\n'
        '    name: "my-vector-store",\n'
        '});\n'
        'console.log(store.id);'
    ),
    "getVectorStore": (
        'const store = await openai.vectorStores.retrieve("vs_abc123");\n'
        'console.log(store.name, store.file_counts);'
    ),
    "modifyVectorStore": (
        'const store = await openai.vectorStores.update("vs_abc123", {\n'
        '    name: "updated-name",\n'
        '});\n'
        'console.log(store.name);'
    ),
    "deleteVectorStore": 'await openai.vectorStores.delete("vs_abc123");',
    "searchVectorStore": (
        'const results = await openai.vectorStores.search("vs_abc123", {\n'
        '    query: "search query",\n'
        '});\n'
        'for await (const result of results) {\n'
        '    console.log(result.score, result.content);\n'
        '}'
    ),
    "listVectorStoreFiles": (
        'const files = await openai.vectorStores.files.list("vs_abc123");\n'
        'for await (const f of files) {\n'
        '    console.log(f.id, f.status);\n'
        '}'
    ),
    "createVectorStoreFile": (
        'const file = await openai.vectorStores.files.create("vs_abc123", {\n'
        '    file_id: "file_abc123",\n'
        '});\n'
        'console.log(file.id, file.status);'
    ),
    "getVectorStoreFile": (
        'const file = await openai.vectorStores.files.retrieve(\n'
        '    "vs_abc123", "file_abc123"\n'
        ');\n'
        'console.log(file.status);'
    ),
    "updateVectorStoreFileAttributes": (
        'await openai.vectorStores.files.update(\n'
        '    "vs_abc123", "file_abc123",\n'
        '    { attributes: { key: "value" } }\n'
        ');'
    ),
    "deleteVectorStoreFile": (
        'await openai.vectorStores.files.delete(\n'
        '    "vs_abc123", "file_abc123"\n'
        ');'
    ),
    "retrieveVectorStoreFileContent": (
        'const content = await openai.vectorStores.files.content(\n'
        '    "vs_abc123", "file_abc123"\n'
        ');\n'
        'console.log(await content.text());'
    ),
    "createVectorStoreFileBatch": (
        'const batch = await openai.vectorStores.fileBatches.create(\n'
        '    "vs_abc123",\n'
        '    { file_ids: ["file_abc123", "file_def456"] }\n'
        ');\n'
        'console.log(batch.id, batch.status);'
    ),
    "getVectorStoreFileBatch": (
        'const batch = await openai.vectorStores.fileBatches.retrieve(\n'
        '    "vs_abc123", "vsfb_abc123"\n'
        ');\n'
        'console.log(batch.status, batch.file_counts);'
    ),
    "cancelVectorStoreFileBatch": (
        'await openai.vectorStores.fileBatches.cancel(\n'
        '    "vs_abc123", "vsfb_abc123"\n'
        ');'
    ),
    "listFilesInVectorStoreBatch": (
        'const files = await openai.vectorStores.fileBatches.listFiles(\n'
        '    "vs_abc123", "vsfb_abc123"\n'
        ');\n'
        'for await (const f of files) {\n'
        '    console.log(f.id, f.status);\n'
        '}'
    ),

    # ── Audio ─────────────────────────────────────────────────────────
    "createSpeech": (
        'const response = await openai.audio.speech.create({\n'
        '    model: "tts-1",\n'
        '    voice: "alloy",\n'
        '    input: "Hello, how are you today?",\n'
        '});\n'
        'const buffer = Buffer.from(await response.arrayBuffer());\n'
        'fs.writeFileSync("output.mp3", buffer);'
    ),
    "createTranscription": (
        'const transcription = await openai.audio.transcriptions.create({\n'
        '    model: "whisper-1",\n'
        '    file: fs.createReadStream("audio.mp3"),\n'
        '});\n'
        'console.log(transcription.text);'
    ),
    "createTranslation": (
        'const translation = await openai.audio.translations.create({\n'
        '    model: "whisper-1",\n'
        '    file: fs.createReadStream("audio.mp3"),\n'
        '});\n'
        'console.log(translation.text);'
    ),

    # ── Images ────────────────────────────────────────────────────────
    "createImage": (
        'const response = await openai.images.generate({\n'
        '    model: "dall-e-3",\n'
        '    prompt: "A white cat sitting on a windowsill",\n'
        '    n: 1,\n'
        '    size: "1024x1024",\n'
        '});\n'
        'console.log(response.data[0].url);'
    ),
    "createImageEdit": (
        'const response = await openai.images.edit({\n'
        '    image: fs.createReadStream("image.png"),\n'
        '    prompt: "Add a sunset in the background",\n'
        '    n: 1,\n'
        '    size: "1024x1024",\n'
        '});\n'
        'console.log(response.data[0].url);'
    ),
    "createImageVariation": (
        'const response = await openai.images.createVariation({\n'
        '    image: fs.createReadStream("image.png"),\n'
        '    n: 1,\n'
        '    size: "1024x1024",\n'
        '});\n'
        'console.log(response.data[0].url);'
    ),

    # ── Video ─────────────────────────────────────────────────────────
    "Videos_Create": (
        'const job = await openai.videos.create({\n'
        '    model: "sora",\n'
        '    prompt: "A serene mountain landscape at sunset",\n'
        '});\n'
        'console.log(job.id, job.status);'
    ),
    "Videos_List": (
        'const videos = await openai.videos.list();\n'
        'for await (const v of videos) {\n'
        '    console.log(v.id, v.status);\n'
        '}'
    ),
    "Videos_Get": (
        'const video = await openai.videos.retrieve("video_abc123");\n'
        'console.log(video.status);'
    ),
    "Videos_Delete": 'await openai.videos.delete("video_abc123");',
    "Videos_RetrieveContent": (
        'const content = await openai.videos.content("video_abc123");\n'
        'console.log(content.url);'
    ),
    "Videos_Remix": (
        'const job = await openai.videos.remix("video_abc123", {\n'
        '    prompt: "Make it a night scene",\n'
        '});\n'
        'console.log(job.id);'
    ),
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
    "Connections_GetWithCredentials": 'const connection = await client.connections.getWithCredentials("my-connection");\nconsole.log(connection.name, connection.credentials);',
    "Datasets_ListVersions": 'const versions = await client.datasets.listVersions("my-dataset");\nfor await (const v of versions) {\n    console.log(v.version, v.createdDate);\n}',
    "Datasets_CreateOrUpdateVersion": 'const dataset = await client.datasets.createOrUpdate(\n    "my-dataset", "1",\n    { description: "Training data" },\n);\nconsole.log(dataset.name);',
    "Datasets_GetCredentials": 'const creds = await client.datasets.getCredentials("my-dataset", "1");\nconsole.log(creds.credentialType);',
    "Datasets_StartPendingUploadVersion": 'const upload = await client.datasets.startPendingUpload(\n    "my-dataset", "1",\n    { pendingUploadType: "temporary_sas" },\n);\nconsole.log(upload.blobReference);',
    "Indexes_ListVersions": 'const versions = await client.indexes.listVersions("my-index");\nfor await (const v of versions) {\n    console.log(v.version);\n}',
    "Indexes_CreateOrUpdateVersion": 'const index = await client.indexes.createOrUpdate(\n    "my-index", "1",\n    { description: "Search index" },\n);\nconsole.log(index.name);',
    "Evaluations_List": 'const runs = await client.evaluations.list();\nfor await (const run of runs) {\n    console.log(run.name, run.status);\n}',
    "Evaluations_Get": 'const run = await client.evaluations.get("my-eval-run");\nconsole.log(run.name, run.status);',
    "Evaluations_Delete": 'await client.evaluations.delete("my-eval-run");',
    "Evaluations_Cancel": 'await client.evaluations.cancel("my-eval-run");',
    "Evaluations_Create": 'const run = await client.evaluations.create({\n    displayName: "my-eval-run",\n    evaluators: { relevance: { id: "relevance" } },\n    data: { type: "dataset", id: "my-dataset:1" },\n});\nconsole.log(run.name);',
    "Evaluations_CreateAgentEvaluation": 'const run = await client.evaluations.createAgent({\n    displayName: "agent-eval",\n    evaluators: { relevance: { id: "relevance" } },\n    target: { agentId: "my-agent:1" },\n});\nconsole.log(run.name);',
    "RedTeams_List": 'const runs = await client.redTeams.list();\nfor await (const run of runs) {\n    console.log(run.name, run.status);\n}',
    "RedTeams_Get": 'const run = await client.redTeams.get("my-redteam-run");\nconsole.log(run.name, run.status);',
    "RedTeams_Create": 'const run = await client.redTeams.create({\n    displayName: "my-redteam",\n    target: { agentId: "my-agent:1" },\n    riskCategories: ["violence", "hate"],\n});\nconsole.log(run.name);',
}


# ---------------------------------------------------------------------------
# Java preambles — Projects API
# ---------------------------------------------------------------------------

JAVA_PROJECTS_PREAMBLE_ENTRA = """\
import com.azure.ai.projects.AIProjectClient;
import com.azure.ai.projects.AIProjectClientBuilder;
import com.azure.identity.DefaultAzureCredentialBuilder;

AIProjectClient client = new AIProjectClientBuilder()
    .endpoint("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME")
    .credential(new DefaultAzureCredentialBuilder().build())
    .buildClient();

"""

JAVA_PROJECTS_PREAMBLE_APIKEY = """\
import com.azure.ai.projects.AIProjectClient;
import com.azure.ai.projects.AIProjectClientBuilder;
import com.azure.core.credential.AzureKeyCredential;

AIProjectClient client = new AIProjectClientBuilder()
    .endpoint("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME")
    .credential(new AzureKeyCredential("YOUR_API_KEY"))
    .buildClient();

"""


# ---------------------------------------------------------------------------
# Java samples — Projects API
# ---------------------------------------------------------------------------

JAVA_PROJECTS_SAMPLES = {
    # ── Connections ────────────────────────────────────────────────────
    "Connections_List": 'PagedIterable<Connection> connections = client.getConnections();\n\nfor (Connection conn : connections) {\n    System.out.printf("%s %s%n", conn.getName(), conn.getConnectionType());\n}',
    "Connections_Get": 'Connection connection = client.getConnection("my-connection");\n\nSystem.out.printf("%s %s%n", connection.getName(), connection.getConnectionType());',
    "Connections_GetWithCredentials": 'Connection connection = client.getConnectionWithCredentials(\n    "my-connection");\n\nSystem.out.println(connection.getCredentials());',

    # ── Datasets ───────────────────────────────────────────────────────
    "Datasets_ListLatest": 'PagedIterable<Dataset> datasets = client.getDatasets();\n\nfor (Dataset ds : datasets) {\n    System.out.printf("%s v%s%n", ds.getName(), ds.getVersion());\n}',
    "Datasets_ListVersions": 'PagedIterable<Dataset> versions = client.getDatasetVersions("my-dataset");\n\nfor (Dataset v : versions) {\n    System.out.printf("v%s %s%n", v.getVersion(), v.getCreatedDate());\n}',
    "Datasets_GetVersion": 'Dataset dataset = client.getDataset("my-dataset", "1");\n\nSystem.out.printf("%s v%s%n", dataset.getName(), dataset.getVersion());',
    "Datasets_CreateOrUpdateVersion": 'Dataset dataset = client.createOrUpdateDataset(\n    "my-dataset", "1",\n    new DatasetVersionOptions().setDescription("Training data"));\n\nSystem.out.println(dataset.getName());',
    "Datasets_DeleteVersion": 'client.deleteDataset("my-dataset", "1");',
    "Datasets_GetCredentials": 'DatasetCredentials creds = client.getDatasetCredentials(\n    "my-dataset", "1");\n\nSystem.out.println(creds.getCredentialType());',
    "Datasets_StartPendingUploadVersion": 'PendingUpload upload = client.startPendingDatasetUpload(\n    "my-dataset", "1",\n    new PendingUploadOptions().setPendingUploadType("temporary_sas"));\n\nSystem.out.println(upload.getBlobReference());',

    # ── Deployments ────────────────────────────────────────────────────
    "Deployments_List": 'PagedIterable<Deployment> deployments = client.getDeployments();\n\nfor (Deployment d : deployments) {\n    System.out.printf("%s %s%n", d.getName(), d.getModel());\n}',
    "Deployments_Get": 'Deployment deployment = client.getDeployment("gpt-4o");\n\nSystem.out.printf("%s %s%n", deployment.getName(), deployment.getModel());',

    # ── Indexes ────────────────────────────────────────────────────────
    "Indexes_ListLatest": 'PagedIterable<Index> indexes = client.getIndexes();\n\nfor (Index idx : indexes) {\n    System.out.printf("%s v%s%n", idx.getName(), idx.getVersion());\n}',
    "Indexes_ListVersions": 'PagedIterable<Index> versions = client.getIndexVersions("my-index");\n\nfor (Index v : versions) {\n    System.out.println(v.getVersion());\n}',
    "Indexes_GetVersion": 'Index index = client.getIndex("my-index", "1");\n\nSystem.out.println(index.getName());',
    "Indexes_CreateOrUpdateVersion": 'Index index = client.createOrUpdateIndex(\n    "my-index", "1",\n    new IndexVersionOptions().setDescription("Search index"));\n\nSystem.out.println(index.getName());',
    "Indexes_DeleteVersion": 'client.deleteIndex("my-index", "1");',

    # ── Evaluations (preview) ──────────────────────────────────────────
    "Evaluations_List": 'PagedIterable<EvaluationRun> runs = client.getEvaluations();\n\nfor (EvaluationRun run : runs) {\n    System.out.printf("%s %s%n", run.getName(), run.getStatus());\n}',
    "Evaluations_Get": 'EvaluationRun run = client.getEvaluation("my-eval-run");\n\nSystem.out.printf("%s %s%n", run.getName(), run.getStatus());',
    "Evaluations_Delete": 'client.deleteEvaluation("my-eval-run");',
    "Evaluations_Cancel": 'client.cancelEvaluation("my-eval-run");',
    "Evaluations_Create": 'EvaluationRun run = client.createEvaluation(\n    new EvaluationOptions()\n        .setDisplayName("my-eval-run")\n        .setEvaluators(Map.of("relevance",\n            new EvaluatorConfig("relevance")))\n        .setData(new DatasetConfig("my-dataset:1")));\n\nSystem.out.println(run.getName());',
    "Evaluations_CreateAgentEvaluation": 'EvaluationRun run = client.createAgentEvaluation(\n    new AgentEvaluationOptions()\n        .setDisplayName("agent-eval")\n        .setEvaluators(Map.of("relevance",\n            new EvaluatorConfig("relevance")))\n        .setTarget(new AgentTarget("my-agent:1")));\n\nSystem.out.println(run.getName());',

    # ── RedTeams (preview) ─────────────────────────────────────────────
    "RedTeams_List": 'PagedIterable<RedTeamRun> runs = client.getRedTeams();\n\nfor (RedTeamRun run : runs) {\n    System.out.printf("%s %s%n", run.getName(), run.getStatus());\n}',
    "RedTeams_Get": 'RedTeamRun run = client.getRedTeam("my-redteam-run");\n\nSystem.out.printf("%s %s%n", run.getName(), run.getStatus());',
    "RedTeams_Create": 'RedTeamRun run = client.createRedTeam(\n    new RedTeamOptions()\n        .setDisplayName("my-redteam")\n        .setTarget(new AgentTarget("my-agent:1"))\n        .setRiskCategories(List.of("violence", "hate")));\n\nSystem.out.println(run.getName());',
}

# ---------------------------------------------------------------------------
# Java preamble templates
# ---------------------------------------------------------------------------

JAVA_OPENAI_PREAMBLE_ENTRA = """import com.azure.ai.projects.AIProjectClient;
import com.azure.ai.projects.AIProjectClientBuilder;
import com.azure.identity.DefaultAzureCredentialBuilder;

AIProjectClient project = new AIProjectClientBuilder()
    .endpoint("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME")
    .credential(new DefaultAzureCredentialBuilder().build())
    .buildClient();

"""

JAVA_OPENAI_PREAMBLE_APIKEY = """import com.azure.ai.projects.AIProjectClient;
import com.azure.ai.projects.AIProjectClientBuilder;
import com.azure.core.credential.AzureKeyCredential;

AIProjectClient project = new AIProjectClientBuilder()
    .endpoint("https://RESOURCE_NAME.services.ai.azure.com/api/projects/PROJECT_NAME")
    .credential(new AzureKeyCredential("YOUR_API_KEY"))
    .buildClient();

"""


# ---------------------------------------------------------------------------
# Java samples — OpenAI v1 API
# ---------------------------------------------------------------------------

JAVA_OPENAI_SAMPLES = {
    # ── Responses ─────────────────────────────────────────────────────
    "createResponse": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.responses()\n'
        '    .create("gpt-4o", "What is the capital of France?");\n'
        '\n'
        'System.out.println(response.getOutputText());'
    ),
    "getResponse": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.responses().retrieve("resp_abc123");\n'
        '\n'
        'System.out.println(response.getStatus());'
    ),
    "deleteResponse": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.responses().delete("resp_abc123");'
    ),
    "cancelResponse": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.responses().cancel("resp_abc123");'
    ),
    "listInputItems": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var items = openai.responses().inputItems()\n'
        '    .list("resp_abc123");\n'
        '\n'
        'for (var item : items) {\n'
        '    System.out.println(item.getType() + " " + item.getId());\n'
        '}'
    ),

    # ── Chat ──────────────────────────────────────────────────────────
    "createChatCompletion": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.chat().completions().create(\n'
        '    "gpt-4o",\n'
        '    List.of(Map.of("role", "user", "content", "Hello!")));\n'
        '\n'
        'System.out.println(\n'
        '    response.getChoices().get(0).getMessage().getContent());'
    ),
    "createCompletion": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.completions().create(\n'
        '    "gpt-4o", "Say hello", 100);\n'
        '\n'
        'System.out.println(response.getChoices().get(0).getText());'
    ),

    # ── Conversations ─────────────────────────────────────────────────
    "createConversation": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var conversation = openai.conversations().create(\n'
        '    List.of(Map.of("type", "message", "role", "user",\n'
        '        "content", "Hello")));\n'
        '\n'
        'System.out.println(conversation.getId());'
    ),
    "retrieveConversation": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var conversation = openai.conversations()\n'
        '    .retrieve("conv_abc123");\n'
        '\n'
        'System.out.println(conversation.getId());'
    ),
    "updateConversation": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var conversation = openai.conversations()\n'
        '    .update("conv_abc123",\n'
        '        Map.of("metadata", Map.of("topic", "geography")));\n'
        '\n'
        'System.out.println(conversation.getId());'
    ),
    "deleteConversation": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.conversations().delete("conv_abc123");'
    ),
    "listConversationItems": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var items = openai.conversations().items()\n'
        '    .list("conv_abc123");\n'
        '\n'
        'for (var item : items) {\n'
        '    System.out.println(item.getType() + " " + item.getId());\n'
        '}'
    ),
    "createConversationItems": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.conversations().items().create("conv_abc123",\n'
        '    List.of(Map.of("type", "message", "role", "user",\n'
        '        "content", "Follow-up")));'
    ),
    "retrieveConversationItem": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var item = openai.conversations().items()\n'
        '    .retrieve("conv_abc123", "item_abc123");\n'
        '\n'
        'System.out.println(item.getType());'
    ),
    "deleteConversationItem": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.conversations().items()\n'
        '    .delete("conv_abc123", "item_abc123");'
    ),

    # ── Embeddings ────────────────────────────────────────────────────
    "createEmbedding": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.embeddings().create(\n'
        '    "text-embedding-3-large", "Sample text to embed");\n'
        '\n'
        'System.out.println(\n'
        '    response.getData().get(0).getEmbedding().size());'
    ),

    # ── Models ────────────────────────────────────────────────────────
    "listModels": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var models = openai.models().list();\n'
        '\n'
        'for (var model : models) {\n'
        '    System.out.println(model.getId());\n'
        '}'
    ),
    "retrieveModel": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var model = openai.models().retrieve("gpt-4o");\n'
        '\n'
        'System.out.println(model.getId() + " " + model.getOwnedBy());'
    ),
    "deleteModel": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.models()\n'
        '    .delete("ft:gpt-4o:your-org:custom-suffix:id");'
    ),

    # ── Files ─────────────────────────────────────────────────────────
    "createFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var file = openai.files().create(\n'
        '    Path.of("data.jsonl"), "fine-tune");\n'
        '\n'
        'System.out.println(file.getId());'
    ),
    "listFiles": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var files = openai.files().list();\n'
        '\n'
        'for (var f : files) {\n'
        '    System.out.println(f.getId() + " " + f.getFilename());\n'
        '}'
    ),
    "retrieveFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var file = openai.files().retrieve("file-abc123");\n'
        '\n'
        'System.out.println(file.getFilename() + " " + file.getStatus());'
    ),
    "deleteFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.files().delete("file-abc123");'
    ),
    "downloadFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var content = openai.files().content("file-abc123");\n'
        '\n'
        'System.out.println(new String(content));'
    ),

    # ── Batch ─────────────────────────────────────────────────────────
    "createBatch": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var batch = openai.batches().create(\n'
        '    "file-abc123", "/v1/chat/completions", "24h");\n'
        '\n'
        'System.out.println(batch.getId() + " " + batch.getStatus());'
    ),
    "listBatches": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var batches = openai.batches().list();\n'
        '\n'
        'for (var b : batches) {\n'
        '    System.out.println(b.getId() + " " + b.getStatus());\n'
        '}'
    ),
    "retrieveBatch": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var batch = openai.batches().retrieve("batch_abc123");\n'
        '\n'
        'System.out.println(batch.getStatus());'
    ),
    "cancelBatch": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.batches().cancel("batch_abc123");'
    ),

    # ── Fine-tuning ───────────────────────────────────────────────────
    "createFineTuningJob": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var job = openai.fineTuning().jobs().create(\n'
        '    "gpt-4o-mini-2024-07-18", "file-abc123");\n'
        '\n'
        'System.out.println(job.getId() + " " + job.getStatus());'
    ),
    "listPaginatedFineTuningJobs": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var jobs = openai.fineTuning().jobs().list();\n'
        '\n'
        'for (var job : jobs) {\n'
        '    System.out.println(job.getId() + " " + job.getStatus());\n'
        '}'
    ),
    "retrieveFineTuningJob": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var job = openai.fineTuning().jobs()\n'
        '    .retrieve("ftjob-abc123");\n'
        '\n'
        'System.out.println(job.getStatus());'
    ),
    "cancelFineTuningJob": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.fineTuning().jobs().cancel("ftjob-abc123");'
    ),
    "listFineTuningJobCheckpoints": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var checkpoints = openai.fineTuning().jobs()\n'
        '    .checkpoints().list("ftjob-abc123");\n'
        '\n'
        'for (var cp : checkpoints) {\n'
        '    System.out.println(cp.getId() + " step " + cp.getStepNumber());\n'
        '}'
    ),
    "listFineTuningEvents": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var events = openai.fineTuning().jobs()\n'
        '    .listEvents("ftjob-abc123");\n'
        '\n'
        'for (var event : events) {\n'
        '    System.out.println(event.getMessage());\n'
        '}'
    ),
    "pauseFineTuningJob": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.fineTuning().jobs().pause("ftjob-abc123");'
    ),
    "resumeFineTuningJob": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.fineTuning().jobs().resume("ftjob-abc123");'
    ),
    "FineTuning_CopyCheckpoint": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.fineTuning().jobs().checkpoints()\n'
        '    .copy("ftjob-abc123", "ftckpt-abc123");'
    ),
    "FineTuning_GetCheckpoint": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var checkpoint = openai.fineTuning().jobs()\n'
        '    .checkpoints().retrieve("ftjob-abc123", "ftckpt-abc123");\n'
        '\n'
        'System.out.println(checkpoint.getId());'
    ),
    "listFineTuningCheckpointPermissions": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var permissions = openai.fineTuning().checkpoints()\n'
        '    .permissions().list("ft:gpt-4o:org:suffix:id");\n'
        '\n'
        'for (var p : permissions) {\n'
        '    System.out.println(p.getId());\n'
        '}'
    ),
    "createFineTuningCheckpointPermission": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.fineTuning().checkpoints().permissions()\n'
        '    .create("ft:gpt-4o:org:suffix:id",\n'
        '        List.of("proj_abc123"));'
    ),
    "deleteFineTuningCheckpointPermission": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.fineTuning().checkpoints().permissions()\n'
        '    .delete("ft:gpt-4o:org:suffix:id", "perm_abc123");'
    ),
    "runGrader": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var result = openai.fineTuning().alpha().graders()\n'
        '    .run(Map.of("type", "python", "source", "return 1.0"),\n'
        '        "Hello world");\n'
        '\n'
        'System.out.println(result);'
    ),
    "validateGrader": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var result = openai.fineTuning().alpha().graders()\n'
        '    .validate(Map.of("type", "python",\n'
        '        "source", "return 1.0"));\n'
        '\n'
        'System.out.println(result);'
    ),

    # ── Evals ─────────────────────────────────────────────────────────
    "listEvals": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var evals = openai.evals().list();\n'
        '\n'
        'for (var e : evals) {\n'
        '    System.out.println(e.getId() + " " + e.getName());\n'
        '}'
    ),
    "createEval": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var evaluation = openai.evals().create(\n'
        '    "my-eval",\n'
        '    Map.of("type", "custom", "item_schema", Map.of()),\n'
        '    List.of());\n'
        '\n'
        'System.out.println(evaluation.getId());'
    ),
    "getEval": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var evaluation = openai.evals()\n'
        '    .retrieve("eval_abc123");\n'
        '\n'
        'System.out.println(evaluation.getName());'
    ),
    "updateEval": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var evaluation = openai.evals()\n'
        '    .update("eval_abc123", Map.of("name", "updated-name"));\n'
        '\n'
        'System.out.println(evaluation.getName());'
    ),
    "deleteEval": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.evals().delete("eval_abc123");'
    ),
    "getEvalRuns": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var runs = openai.evals().runs().list("eval_abc123");\n'
        '\n'
        'for (var run : runs) {\n'
        '    System.out.println(run.getId() + " " + run.getStatus());\n'
        '}'
    ),
    "createEvalRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var run = openai.evals().runs().create(\n'
        '    "eval_abc123", "gpt-4o",\n'
        '    Map.of("type", "completions"));\n'
        '\n'
        'System.out.println(run.getId());'
    ),
    "getEvalRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var run = openai.evals().runs()\n'
        '    .retrieve("eval_abc123", "run_abc123");\n'
        '\n'
        'System.out.println(run.getStatus());'
    ),
    "cancelEvalRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.evals().runs()\n'
        '    .cancel("eval_abc123", "run_abc123");'
    ),
    "deleteEvalRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.evals().runs()\n'
        '    .delete("eval_abc123", "run_abc123");'
    ),
    "getEvalRunOutputItems": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var items = openai.evals().runs().outputItems()\n'
        '    .list("eval_abc123", "run_abc123");\n'
        '\n'
        'for (var item : items) {\n'
        '    System.out.println(item.getId());\n'
        '}'
    ),
    "getEvalRunOutputItem": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var item = openai.evals().runs().outputItems()\n'
        '    .retrieve("eval_abc123", "run_abc123",\n'
        '        "item_abc123");\n'
        '\n'
        'System.out.println(item.getId());'
    ),

    # ── Realtime ──────────────────────────────────────────────────────
    "createRealtimeSession": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var session = openai.realtime().sessions()\n'
        '    .create("gpt-4o-realtime-preview");\n'
        '\n'
        'System.out.println(session.getId());'
    ),
    "createRealtimeClientSecret": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var secret = openai.realtime().clientSecrets()\n'
        '    .create("gpt-4o-realtime-preview");\n'
        '\n'
        'System.out.println(secret.getClientSecret().getValue());'
    ),
    "createRealtimeTranscriptionSession": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var session = openai.realtime().transcriptionSessions()\n'
        '    .create("gpt-4o-transcribe");\n'
        '\n'
        'System.out.println(session.getId());'
    ),
    "createRealtimeCall": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var call = openai.realtime().calls().create(\n'
        '    "gpt-4o-realtime-preview", "YOUR_SDP_OFFER");\n'
        '\n'
        'System.out.println(call.getId() + " " + call.getSdp());'
    ),
    "acceptRealtimeCall": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.realtime().calls()\n'
        '    .accept("call_abc123", "gpt-4o-realtime-preview");'
    ),
    "hangupRealtimeCall": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.realtime().calls().hangup("call_abc123");'
    ),
    "referRealtimeCall": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.realtime().calls()\n'
        '    .refer("call_abc123", "sip:destination@example.com");'
    ),
    "rejectRealtimeCall": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.realtime().calls()\n'
        '    .reject("call_abc123", "busy");'
    ),

    # ── Containers ────────────────────────────────────────────────────
    "listContainers": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var containers = openai.containers().list();\n'
        '\n'
        'for (var c : containers) {\n'
        '    System.out.println(c.getId() + " " + c.getName());\n'
        '}'
    ),
    "createContainer": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var container = openai.containers()\n'
        '    .create("my-container");\n'
        '\n'
        'System.out.println(container.getId());'
    ),
    "retrieveContainer": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var container = openai.containers()\n'
        '    .retrieve("container_abc123");\n'
        '\n'
        'System.out.println(container.getName());'
    ),
    "deleteContainer": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.containers().delete("container_abc123");'
    ),
    "listContainerFiles": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var files = openai.containers().files()\n'
        '    .list("container_abc123");\n'
        '\n'
        'for (var f : files) {\n'
        '    System.out.println(f.getId() + " " + f.getPath());\n'
        '}'
    ),
    "createContainerFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var file = openai.containers().files()\n'
        '    .create("container_abc123",\n'
        '        Path.of("data.txt"), "data.txt");\n'
        '\n'
        'System.out.println(file.getId());'
    ),
    "retrieveContainerFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var file = openai.containers().files()\n'
        '    .retrieve("container_abc123", "file_abc123");\n'
        '\n'
        'System.out.println(file.getPath());'
    ),
    "deleteContainerFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.containers().files()\n'
        '    .delete("container_abc123", "file_abc123");'
    ),
    "retrieveContainerFileContent": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var content = openai.containers().files()\n'
        '    .content("container_abc123", "file_abc123");\n'
        '\n'
        'System.out.println(new String(content));'
    ),

    # ── Threads (legacy) ──────────────────────────────────────────────
    "createThread": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var thread = openai.beta().threads().create();\n'
        '\n'
        'System.out.println(thread.getId());'
    ),
    "retrieveThread": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var thread = openai.beta().threads()\n'
        '    .retrieve("thread_abc123");\n'
        '\n'
        'System.out.println(thread.getId());'
    ),
    "modifyThread": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.beta().threads().update("thread_abc123",\n'
        '    Map.of("metadata", Map.of("topic", "science")));'
    ),
    "deleteThread": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.beta().threads().delete("thread_abc123");'
    ),
    "createMessage": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var message = openai.beta().threads().messages()\n'
        '    .create("thread_abc123", "user",\n'
        '        "What is the capital of France?");\n'
        '\n'
        'System.out.println(message.getId());'
    ),
    "listMessages": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var messages = openai.beta().threads().messages()\n'
        '    .list("thread_abc123");\n'
        '\n'
        'for (var msg : messages) {\n'
        '    System.out.println(msg.getRole() + " "\n'
        '        + msg.getContent().get(0).getText().getValue());\n'
        '}'
    ),
    "retrieveMessage": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var message = openai.beta().threads().messages()\n'
        '    .retrieve("thread_abc123", "msg_abc123");\n'
        '\n'
        'System.out.println(\n'
        '    message.getContent().get(0).getText().getValue());'
    ),
    "modifyMessage": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.beta().threads().messages()\n'
        '    .update("thread_abc123", "msg_abc123",\n'
        '        Map.of("metadata", Map.of("reviewed", "true")));'
    ),
    "deleteMessage": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.beta().threads().messages()\n'
        '    .delete("thread_abc123", "msg_abc123");'
    ),
    "createRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var run = openai.beta().threads().runs()\n'
        '    .create("thread_abc123", "asst_abc123");\n'
        '\n'
        'System.out.println(run.getId() + " " + run.getStatus());'
    ),
    "createThreadAndRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var run = openai.beta().threads().createAndRun(\n'
        '    "asst_abc123",\n'
        '    Map.of("messages", List.of(\n'
        '        Map.of("role", "user", "content", "Hello"))));\n'
        '\n'
        'System.out.println(run.getId());'
    ),
    "listRuns": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var runs = openai.beta().threads().runs()\n'
        '    .list("thread_abc123");\n'
        '\n'
        'for (var run : runs) {\n'
        '    System.out.println(run.getId() + " " + run.getStatus());\n'
        '}'
    ),
    "retrieveRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var run = openai.beta().threads().runs()\n'
        '    .retrieve("thread_abc123", "run_abc123");\n'
        '\n'
        'System.out.println(run.getStatus());'
    ),
    "modifyRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.beta().threads().runs()\n'
        '    .update("thread_abc123", "run_abc123",\n'
        '        Map.of("metadata", Map.of("priority", "high")));'
    ),
    "cancelRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.beta().threads().runs()\n'
        '    .cancel("thread_abc123", "run_abc123");'
    ),
    "submitToolOutputsToRun": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var run = openai.beta().threads().runs()\n'
        '    .submitToolOutputs("thread_abc123", "run_abc123",\n'
        '        List.of(Map.of("tool_call_id", "call_abc123",\n'
        '            "output", "result")));\n'
        '\n'
        'System.out.println(run.getStatus());'
    ),
    "listRunSteps": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var steps = openai.beta().threads().runs().steps()\n'
        '    .list("thread_abc123", "run_abc123");\n'
        '\n'
        'for (var step : steps) {\n'
        '    System.out.println(step.getId() + " " + step.getType());\n'
        '}'
    ),
    "getRunStep": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var step = openai.beta().threads().runs().steps()\n'
        '    .retrieve("thread_abc123", "run_abc123",\n'
        '        "step_abc123");\n'
        '\n'
        'System.out.println(step.getType() + " " + step.getStatus());'
    ),

    # ── Vector Stores ─────────────────────────────────────────────────
    "listVectorStores": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var stores = openai.vectorStores().list();\n'
        '\n'
        'for (var store : stores) {\n'
        '    System.out.println(store.getId() + " " + store.getName());\n'
        '}'
    ),
    "createVectorStore": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var store = openai.vectorStores()\n'
        '    .create("my-vector-store");\n'
        '\n'
        'System.out.println(store.getId());'
    ),
    "getVectorStore": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var store = openai.vectorStores()\n'
        '    .retrieve("vs_abc123");\n'
        '\n'
        'System.out.println(store.getName());'
    ),
    "modifyVectorStore": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.vectorStores().update("vs_abc123",\n'
        '    Map.of("name", "updated-name"));'
    ),
    "deleteVectorStore": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.vectorStores().delete("vs_abc123");'
    ),
    "searchVectorStore": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var results = openai.vectorStores()\n'
        '    .search("vs_abc123", "search query");\n'
        '\n'
        'for (var result : results) {\n'
        '    System.out.println(result.getScore()\n'
        '        + " " + result.getContent());\n'
        '}'
    ),
    "listVectorStoreFiles": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var files = openai.vectorStores().files()\n'
        '    .list("vs_abc123");\n'
        '\n'
        'for (var f : files) {\n'
        '    System.out.println(f.getId() + " " + f.getStatus());\n'
        '}'
    ),
    "createVectorStoreFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var file = openai.vectorStores().files()\n'
        '    .create("vs_abc123", "file_abc123");\n'
        '\n'
        'System.out.println(file.getId() + " " + file.getStatus());'
    ),
    "getVectorStoreFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var file = openai.vectorStores().files()\n'
        '    .retrieve("vs_abc123", "file_abc123");\n'
        '\n'
        'System.out.println(file.getStatus());'
    ),
    "updateVectorStoreFileAttributes": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.vectorStores().files().update(\n'
        '    "vs_abc123", "file_abc123",\n'
        '    Map.of("key", "value"));'
    ),
    "deleteVectorStoreFile": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.vectorStores().files()\n'
        '    .delete("vs_abc123", "file_abc123");'
    ),
    "retrieveVectorStoreFileContent": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var content = openai.vectorStores().files()\n'
        '    .content("vs_abc123", "file_abc123");\n'
        '\n'
        'System.out.println(new String(content));'
    ),
    "createVectorStoreFileBatch": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var batch = openai.vectorStores().fileBatches()\n'
        '    .create("vs_abc123",\n'
        '        List.of("file_abc123", "file_def456"));\n'
        '\n'
        'System.out.println(batch.getId() + " " + batch.getStatus());'
    ),
    "getVectorStoreFileBatch": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var batch = openai.vectorStores().fileBatches()\n'
        '    .retrieve("vs_abc123", "vsfb_abc123");\n'
        '\n'
        'System.out.println(batch.getStatus());'
    ),
    "cancelVectorStoreFileBatch": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.vectorStores().fileBatches()\n'
        '    .cancel("vs_abc123", "vsfb_abc123");'
    ),
    "listFilesInVectorStoreBatch": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var files = openai.vectorStores().fileBatches()\n'
        '    .listFiles("vs_abc123", "vsfb_abc123");\n'
        '\n'
        'for (var f : files) {\n'
        '    System.out.println(f.getId() + " " + f.getStatus());\n'
        '}'
    ),

    # ── Audio ─────────────────────────────────────────────────────────
    "createSpeech": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.audio().speech().create(\n'
        '    "tts-1", "alloy",\n'
        '    "Hello, how are you today?");\n'
        '\n'
        'Files.write(Path.of("output.mp3"), response);'
    ),
    "createTranscription": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var transcription = openai.audio().transcriptions()\n'
        '    .create("whisper-1", Path.of("audio.mp3"));\n'
        '\n'
        'System.out.println(transcription.getText());'
    ),
    "createTranslation": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var translation = openai.audio().translations()\n'
        '    .create("whisper-1", Path.of("audio.mp3"));\n'
        '\n'
        'System.out.println(translation.getText());'
    ),

    # ── Images ────────────────────────────────────────────────────────
    "createImage": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.images().generate(\n'
        '    "dall-e-3",\n'
        '    "A white cat sitting on a windowsill",\n'
        '    1, "1024x1024");\n'
        '\n'
        'System.out.println(response.getData().get(0).getUrl());'
    ),
    "createImageEdit": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.images().edit(\n'
        '    Path.of("image.png"),\n'
        '    "Add a sunset in the background",\n'
        '    1, "1024x1024");\n'
        '\n'
        'System.out.println(response.getData().get(0).getUrl());'
    ),
    "createImageVariation": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var response = openai.images().createVariation(\n'
        '    Path.of("image.png"), 1, "1024x1024");\n'
        '\n'
        'System.out.println(response.getData().get(0).getUrl());'
    ),

    # ── Video ─────────────────────────────────────────────────────────
    "Videos_Create": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var job = openai.videos().create(\n'
        '    "sora", "A serene mountain landscape at sunset");\n'
        '\n'
        'System.out.println(job.getId() + " " + job.getStatus());'
    ),
    "Videos_List": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var videos = openai.videos().list();\n'
        '\n'
        'for (var v : videos) {\n'
        '    System.out.println(v.getId() + " " + v.getStatus());\n'
        '}'
    ),
    "Videos_Get": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var video = openai.videos().retrieve("video_abc123");\n'
        '\n'
        'System.out.println(video.getStatus());'
    ),
    "Videos_Delete": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'openai.videos().delete("video_abc123");'
    ),
    "Videos_RetrieveContent": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var content = openai.videos()\n'
        '    .content("video_abc123");\n'
        '\n'
        'System.out.println(content.getUrl());'
    ),
    "Videos_Remix": (
        'var openai = project.getOpenAIClient();\n'
        '\n'
        'var job = openai.videos().remix(\n'
        '    "video_abc123", "Make it a night scene");\n'
        '\n'
        'System.out.println(job.getId());'
    ),
}
