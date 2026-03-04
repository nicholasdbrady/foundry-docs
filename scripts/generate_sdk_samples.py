#!/usr/bin/env python3
"""Generate multi-language SDK x-codeSamples for OpenAPI specs.

Injects minimal, idiomatic code snippets (Python, cURL, C#, JS/TS)
into each OpenAPI operation's x-codeSamples extension for Mintlify.

Usage:
    python scripts/generate_sdk_samples.py [--spec-dir docs-vnext/openapi]
"""

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Preamble templates
# ---------------------------------------------------------------------------

OPENAI_PREAMBLE = """\
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    endpoint="YOUR_ENDPOINT",
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client()

"""

PROJECTS_PREAMBLE = """\
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    endpoint="YOUR_ENDPOINT",
    credential=DefaultAzureCredential(),
)

"""

# ---------------------------------------------------------------------------
# OpenAI v1 API samples — keyed by operationId
# ---------------------------------------------------------------------------

OPENAI_SAMPLES = {
    # ── Responses ──────────────────────────────────────────────────────
    "createResponse": (
        'response = openai.responses.create(\n'
        '    model="gpt-4o",\n'
        '    input="What is the capital of France?",\n'
        ')\n'
        'print(response.output_text)'
    ),
    "getResponse": (
        'response = openai.responses.retrieve("resp_abc123")\n'
        'print(response.status, response.output_text)'
    ),
    "deleteResponse": (
        'openai.responses.delete("resp_abc123")'
    ),
    "cancelResponse": (
        'openai.responses.cancel("resp_abc123")'
    ),
    "listInputItems": (
        'items = openai.responses.input_items.list("resp_abc123")\n'
        'for item in items:\n'
        '    print(item.type, item.id)'
    ),

    # ── Chat Completions ───────────────────────────────────────────────
    "createChatCompletion": (
        'response = openai.chat.completions.create(\n'
        '    model="gpt-4o",\n'
        '    messages=[{"role": "user", "content": "Hello!"}],\n'
        ')\n'
        'print(response.choices[0].message.content)'
    ),

    # ── Completions (legacy) ───────────────────────────────────────────
    "createCompletion": (
        'response = openai.completions.create(\n'
        '    model="gpt-4o",\n'
        '    prompt="Say hello",\n'
        '    max_tokens=100,\n'
        ')\n'
        'print(response.choices[0].text)'
    ),

    # ── Conversations ──────────────────────────────────────────────────
    "createConversation": (
        'conversation = openai.conversations.create(\n'
        '    items=[{"type": "message", "role": "user", "content": "Hello"}],\n'
        ')\n'
        'print(conversation.id)'
    ),
    "retrieveConversation": (
        'conversation = openai.conversations.retrieve("conv_abc123")\n'
        'print(conversation.id)'
    ),
    "updateConversation": (
        'conversation = openai.conversations.update(\n'
        '    "conv_abc123",\n'
        '    metadata={"topic": "geography"},\n'
        ')\n'
        'print(conversation.id)'
    ),
    "deleteConversation": (
        'openai.conversations.delete("conv_abc123")'
    ),
    "listConversationItems": (
        'items = openai.conversations.items.list("conv_abc123")\n'
        'for item in items:\n'
        '    print(item.type, item.id)'
    ),
    "createConversationItems": (
        'openai.conversations.items.create(\n'
        '    conversation_id="conv_abc123",\n'
        '    items=[{"type": "message", "role": "user", "content": "Follow-up question"}],\n'
        ')'
    ),
    "retrieveConversationItem": (
        'item = openai.conversations.items.retrieve(\n'
        '    conversation_id="conv_abc123",\n'
        '    item_id="item_abc123",\n'
        ')\n'
        'print(item.type)'
    ),
    "deleteConversationItem": (
        'openai.conversations.items.delete(\n'
        '    conversation_id="conv_abc123",\n'
        '    item_id="item_abc123",\n'
        ')'
    ),

    # ── Embeddings ─────────────────────────────────────────────────────
    "createEmbedding": (
        'response = openai.embeddings.create(\n'
        '    model="text-embedding-3-large",\n'
        '    input="Sample text to embed",\n'
        ')\n'
        'print(response.data[0].embedding[:5])'
    ),

    # ── Models ─────────────────────────────────────────────────────────
    "listModels": (
        'models = openai.models.list()\n'
        'for model in models:\n'
        '    print(model.id)'
    ),
    "retrieveModel": (
        'model = openai.models.retrieve("gpt-4o")\n'
        'print(model.id, model.owned_by)'
    ),
    "deleteModel": (
        'openai.models.delete("ft:gpt-4o:your-org:custom-suffix:id")'
    ),

    # ── Files ──────────────────────────────────────────────────────────
    "createFile": (
        'file = openai.files.create(\n'
        '    file=open("data.jsonl", "rb"),\n'
        '    purpose="fine-tune",\n'
        ')\n'
        'print(file.id)'
    ),
    "listFiles": (
        'files = openai.files.list()\n'
        'for f in files:\n'
        '    print(f.id, f.filename, f.purpose)'
    ),
    "retrieveFile": (
        'file = openai.files.retrieve("file-abc123")\n'
        'print(file.filename, file.status)'
    ),
    "deleteFile": (
        'openai.files.delete("file-abc123")'
    ),
    "downloadFile": (
        'content = openai.files.content("file-abc123")\n'
        'print(content.text)'
    ),

    # ── Batch ──────────────────────────────────────────────────────────
    "createBatch": (
        'batch = openai.batches.create(\n'
        '    input_file_id="file-abc123",\n'
        '    endpoint="/v1/chat/completions",\n'
        '    completion_window="24h",\n'
        ')\n'
        'print(batch.id, batch.status)'
    ),
    "listBatches": (
        'batches = openai.batches.list()\n'
        'for b in batches:\n'
        '    print(b.id, b.status)'
    ),
    "retrieveBatch": (
        'batch = openai.batches.retrieve("batch_abc123")\n'
        'print(batch.status, batch.request_counts)'
    ),
    "cancelBatch": (
        'openai.batches.cancel("batch_abc123")'
    ),

    # ── Fine-tuning ────────────────────────────────────────────────────
    "createFineTuningJob": (
        'job = openai.fine_tuning.jobs.create(\n'
        '    model="gpt-4o-mini-2024-07-18",\n'
        '    training_file="file-abc123",\n'
        ')\n'
        'print(job.id, job.status)'
    ),
    "listPaginatedFineTuningJobs": (
        'jobs = openai.fine_tuning.jobs.list()\n'
        'for job in jobs:\n'
        '    print(job.id, job.status)'
    ),
    "retrieveFineTuningJob": (
        'job = openai.fine_tuning.jobs.retrieve("ftjob-abc123")\n'
        'print(job.status, job.trained_tokens)'
    ),
    "cancelFineTuningJob": (
        'openai.fine_tuning.jobs.cancel("ftjob-abc123")'
    ),
    "listFineTuningJobCheckpoints": (
        'checkpoints = openai.fine_tuning.jobs.checkpoints.list("ftjob-abc123")\n'
        'for cp in checkpoints:\n'
        '    print(cp.id, cp.step_number)'
    ),
    "listFineTuningEvents": (
        'events = openai.fine_tuning.jobs.list_events("ftjob-abc123")\n'
        'for event in events:\n'
        '    print(event.message)'
    ),
    "pauseFineTuningJob": (
        'openai.fine_tuning.jobs.pause("ftjob-abc123")'
    ),
    "resumeFineTuningJob": (
        'openai.fine_tuning.jobs.resume("ftjob-abc123")'
    ),
    "FineTuning_CopyCheckpoint": (
        'openai.fine_tuning.jobs.checkpoints.copy(\n'
        '    fine_tuning_job_id="ftjob-abc123",\n'
        '    fine_tuning_checkpoint_id="ftckpt-abc123",\n'
        ')'
    ),
    "FineTuning_GetCheckpoint": (
        'checkpoint = openai.fine_tuning.jobs.checkpoints.retrieve(\n'
        '    fine_tuning_job_id="ftjob-abc123",\n'
        '    fine_tuning_checkpoint_id="ftckpt-abc123",\n'
        ')\n'
        'print(checkpoint.id)'
    ),
    "listFineTuningCheckpointPermissions": (
        'permissions = openai.fine_tuning.checkpoints.permissions.list(\n'
        '    "ft:gpt-4o:org:suffix:id",\n'
        ')\n'
        'for p in permissions:\n'
        '    print(p.id)'
    ),
    "createFineTuningCheckpointPermission": (
        'openai.fine_tuning.checkpoints.permissions.create(\n'
        '    "ft:gpt-4o:org:suffix:id",\n'
        '    project_ids=["proj_abc123"],\n'
        ')'
    ),
    "deleteFineTuningCheckpointPermission": (
        'openai.fine_tuning.checkpoints.permissions.delete(\n'
        '    "ft:gpt-4o:org:suffix:id",\n'
        '    "perm_abc123",\n'
        ')'
    ),
    "runGrader": (
        'result = openai.fine_tuning.alpha.graders.run(\n'
        '    grader={"type": "python", "source": "return 1.0"},\n'
        '    model_sample="Hello world",\n'
        ')\n'
        'print(result)'
    ),
    "validateGrader": (
        'result = openai.fine_tuning.alpha.graders.validate(\n'
        '    grader={"type": "python", "source": "return 1.0"},\n'
        ')\n'
        'print(result)'
    ),

    # ── Evals ──────────────────────────────────────────────────────────
    "listEvals": (
        'evals = openai.evals.list()\n'
        'for e in evals:\n'
        '    print(e.id, e.name)'
    ),
    "createEval": (
        'evaluation = openai.evals.create(\n'
        '    name="my-eval",\n'
        '    data_source_config={"type": "custom", "item_schema": {}},\n'
        '    testing_criteria=[],\n'
        ')\n'
        'print(evaluation.id)'
    ),
    "getEval": (
        'evaluation = openai.evals.retrieve("eval_abc123")\n'
        'print(evaluation.name, evaluation.id)'
    ),
    "updateEval": (
        'evaluation = openai.evals.update(\n'
        '    "eval_abc123",\n'
        '    name="updated-name",\n'
        ')\n'
        'print(evaluation.name)'
    ),
    "deleteEval": (
        'openai.evals.delete("eval_abc123")'
    ),
    "getEvalRuns": (
        'runs = openai.evals.runs.list("eval_abc123")\n'
        'for run in runs:\n'
        '    print(run.id, run.status)'
    ),
    "createEvalRun": (
        'run = openai.evals.runs.create(\n'
        '    eval_id="eval_abc123",\n'
        '    model="gpt-4o",\n'
        '    data_source={"type": "completions"},\n'
        ')\n'
        'print(run.id)'
    ),
    "getEvalRun": (
        'run = openai.evals.runs.retrieve(\n'
        '    eval_id="eval_abc123",\n'
        '    run_id="run_abc123",\n'
        ')\n'
        'print(run.status)'
    ),
    "cancelEvalRun": (
        'openai.evals.runs.cancel(\n'
        '    eval_id="eval_abc123",\n'
        '    run_id="run_abc123",\n'
        ')'
    ),
    "deleteEvalRun": (
        'openai.evals.runs.delete(\n'
        '    eval_id="eval_abc123",\n'
        '    run_id="run_abc123",\n'
        ')'
    ),
    "getEvalRunOutputItems": (
        'items = openai.evals.runs.output_items.list(\n'
        '    eval_id="eval_abc123",\n'
        '    run_id="run_abc123",\n'
        ')\n'
        'for item in items:\n'
        '    print(item.id)'
    ),
    "getEvalRunOutputItem": (
        'item = openai.evals.runs.output_items.retrieve(\n'
        '    eval_id="eval_abc123",\n'
        '    run_id="run_abc123",\n'
        '    output_item_id="item_abc123",\n'
        ')\n'
        'print(item.id)'
    ),

    # ── Realtime ───────────────────────────────────────────────────────
    "createRealtimeSession": (
        'session = openai.realtime.sessions.create(\n'
        '    model="gpt-4o-realtime-preview",\n'
        ')\n'
        'print(session.id, session.client_secret.value)'
    ),
    "createRealtimeClientSecret": (
        'secret = openai.realtime.client_secrets.create(\n'
        '    model="gpt-4o-realtime-preview",\n'
        ')\n'
        'print(secret.client_secret.value)'
    ),
    "createRealtimeTranscriptionSession": (
        'session = openai.realtime.transcription_sessions.create(\n'
        '    model="gpt-4o-transcribe",\n'
        ')\n'
        'print(session.id)'
    ),
    "createRealtimeCall": (
        'call = openai.realtime.calls.create(\n'
        '    model="gpt-4o-realtime-preview",\n'
        '    sdp="YOUR_SDP_OFFER",\n'
        ')\n'
        'print(call.id, call.sdp)'
    ),
    "acceptRealtimeCall": (
        'openai.realtime.calls.accept(\n'
        '    call_id="call_abc123",\n'
        '    model="gpt-4o-realtime-preview",\n'
        ')'
    ),
    "hangupRealtimeCall": (
        'openai.realtime.calls.hangup("call_abc123")'
    ),
    "referRealtimeCall": (
        'openai.realtime.calls.refer(\n'
        '    call_id="call_abc123",\n'
        '    refer_to="sip:destination@example.com",\n'
        ')'
    ),
    "rejectRealtimeCall": (
        'openai.realtime.calls.reject(\n'
        '    call_id="call_abc123",\n'
        '    reason="busy",\n'
        ')'
    ),

    # ── Containers ─────────────────────────────────────────────────────
    "listContainers": (
        'containers = openai.containers.list()\n'
        'for c in containers:\n'
        '    print(c.id, c.name)'
    ),
    "createContainer": (
        'container = openai.containers.create(\n'
        '    name="my-container",\n'
        ')\n'
        'print(container.id)'
    ),
    "retrieveContainer": (
        'container = openai.containers.retrieve("container_abc123")\n'
        'print(container.name)'
    ),
    "deleteContainer": (
        'openai.containers.delete("container_abc123")'
    ),
    "listContainerFiles": (
        'files = openai.containers.files.list("container_abc123")\n'
        'for f in files:\n'
        '    print(f.id, f.path)'
    ),
    "createContainerFile": (
        'file = openai.containers.files.create(\n'
        '    container_id="container_abc123",\n'
        '    file=open("data.txt", "rb"),\n'
        '    file_path="data.txt",\n'
        ')\n'
        'print(file.id)'
    ),
    "retrieveContainerFile": (
        'file = openai.containers.files.retrieve(\n'
        '    container_id="container_abc123",\n'
        '    file_id="file_abc123",\n'
        ')\n'
        'print(file.path)'
    ),
    "deleteContainerFile": (
        'openai.containers.files.delete(\n'
        '    container_id="container_abc123",\n'
        '    file_id="file_abc123",\n'
        ')'
    ),
    "retrieveContainerFileContent": (
        'content = openai.containers.files.content(\n'
        '    container_id="container_abc123",\n'
        '    file_id="file_abc123",\n'
        ')\n'
        'print(content.text)'
    ),

    # ── Threads (legacy assistants API) ────────────────────────────────
    "createThread": (
        'thread = openai.beta.threads.create()\n'
        'print(thread.id)'
    ),
    "retrieveThread": (
        'thread = openai.beta.threads.retrieve("thread_abc123")\n'
        'print(thread.id)'
    ),
    "modifyThread": (
        'thread = openai.beta.threads.update(\n'
        '    "thread_abc123",\n'
        '    metadata={"topic": "science"},\n'
        ')\n'
        'print(thread.id)'
    ),
    "deleteThread": (
        'openai.beta.threads.delete("thread_abc123")'
    ),
    "createMessage": (
        'message = openai.beta.threads.messages.create(\n'
        '    thread_id="thread_abc123",\n'
        '    role="user",\n'
        '    content="What is the capital of France?",\n'
        ')\n'
        'print(message.id)'
    ),
    "listMessages": (
        'messages = openai.beta.threads.messages.list("thread_abc123")\n'
        'for msg in messages:\n'
        '    print(msg.role, msg.content[0].text.value)'
    ),
    "retrieveMessage": (
        'message = openai.beta.threads.messages.retrieve(\n'
        '    thread_id="thread_abc123",\n'
        '    message_id="msg_abc123",\n'
        ')\n'
        'print(message.content[0].text.value)'
    ),
    "modifyMessage": (
        'message = openai.beta.threads.messages.update(\n'
        '    thread_id="thread_abc123",\n'
        '    message_id="msg_abc123",\n'
        '    metadata={"reviewed": "true"},\n'
        ')'
    ),
    "deleteMessage": (
        'openai.beta.threads.messages.delete(\n'
        '    thread_id="thread_abc123",\n'
        '    message_id="msg_abc123",\n'
        ')'
    ),
    "createRun": (
        'run = openai.beta.threads.runs.create(\n'
        '    thread_id="thread_abc123",\n'
        '    assistant_id="asst_abc123",\n'
        ')\n'
        'print(run.id, run.status)'
    ),
    "createThreadAndRun": (
        'run = openai.beta.threads.create_and_run(\n'
        '    assistant_id="asst_abc123",\n'
        '    thread={"messages": [{"role": "user", "content": "Hello"}]},\n'
        ')\n'
        'print(run.id)'
    ),
    "listRuns": (
        'runs = openai.beta.threads.runs.list("thread_abc123")\n'
        'for run in runs:\n'
        '    print(run.id, run.status)'
    ),
    "retrieveRun": (
        'run = openai.beta.threads.runs.retrieve(\n'
        '    thread_id="thread_abc123",\n'
        '    run_id="run_abc123",\n'
        ')\n'
        'print(run.status)'
    ),
    "modifyRun": (
        'run = openai.beta.threads.runs.update(\n'
        '    thread_id="thread_abc123",\n'
        '    run_id="run_abc123",\n'
        '    metadata={"priority": "high"},\n'
        ')'
    ),
    "cancelRun": (
        'openai.beta.threads.runs.cancel(\n'
        '    thread_id="thread_abc123",\n'
        '    run_id="run_abc123",\n'
        ')'
    ),
    "submitToolOutputsToRun": (
        'run = openai.beta.threads.runs.submit_tool_outputs(\n'
        '    thread_id="thread_abc123",\n'
        '    run_id="run_abc123",\n'
        '    tool_outputs=[{"tool_call_id": "call_abc123", "output": "result"}],\n'
        ')\n'
        'print(run.status)'
    ),
    "listRunSteps": (
        'steps = openai.beta.threads.runs.steps.list(\n'
        '    thread_id="thread_abc123",\n'
        '    run_id="run_abc123",\n'
        ')\n'
        'for step in steps:\n'
        '    print(step.id, step.type)'
    ),
    "getRunStep": (
        'step = openai.beta.threads.runs.steps.retrieve(\n'
        '    thread_id="thread_abc123",\n'
        '    run_id="run_abc123",\n'
        '    step_id="step_abc123",\n'
        ')\n'
        'print(step.type, step.status)'
    ),

    # ── Vector Stores ──────────────────────────────────────────────────
    "listVectorStores": (
        'stores = openai.vector_stores.list()\n'
        'for store in stores:\n'
        '    print(store.id, store.name)'
    ),
    "createVectorStore": (
        'store = openai.vector_stores.create(\n'
        '    name="my-vector-store",\n'
        ')\n'
        'print(store.id)'
    ),
    "getVectorStore": (
        'store = openai.vector_stores.retrieve("vs_abc123")\n'
        'print(store.name, store.file_counts)'
    ),
    "modifyVectorStore": (
        'store = openai.vector_stores.update(\n'
        '    "vs_abc123",\n'
        '    name="updated-name",\n'
        ')\n'
        'print(store.name)'
    ),
    "deleteVectorStore": (
        'openai.vector_stores.delete("vs_abc123")'
    ),
    "searchVectorStore": (
        'results = openai.vector_stores.search(\n'
        '    vector_store_id="vs_abc123",\n'
        '    query="search query",\n'
        ')\n'
        'for result in results:\n'
        '    print(result.score, result.content)'
    ),
    "listVectorStoreFiles": (
        'files = openai.vector_stores.files.list("vs_abc123")\n'
        'for f in files:\n'
        '    print(f.id, f.status)'
    ),
    "createVectorStoreFile": (
        'file = openai.vector_stores.files.create(\n'
        '    vector_store_id="vs_abc123",\n'
        '    file_id="file_abc123",\n'
        ')\n'
        'print(file.id, file.status)'
    ),
    "getVectorStoreFile": (
        'file = openai.vector_stores.files.retrieve(\n'
        '    vector_store_id="vs_abc123",\n'
        '    file_id="file_abc123",\n'
        ')\n'
        'print(file.status)'
    ),
    "updateVectorStoreFileAttributes": (
        'file = openai.vector_stores.files.update(\n'
        '    vector_store_id="vs_abc123",\n'
        '    file_id="file_abc123",\n'
        '    attributes={"key": "value"},\n'
        ')'
    ),
    "deleteVectorStoreFile": (
        'openai.vector_stores.files.delete(\n'
        '    vector_store_id="vs_abc123",\n'
        '    file_id="file_abc123",\n'
        ')'
    ),
    "retrieveVectorStoreFileContent": (
        'content = openai.vector_stores.files.content(\n'
        '    vector_store_id="vs_abc123",\n'
        '    file_id="file_abc123",\n'
        ')\n'
        'print(content.text)'
    ),
    "createVectorStoreFileBatch": (
        'batch = openai.vector_stores.file_batches.create(\n'
        '    vector_store_id="vs_abc123",\n'
        '    file_ids=["file_abc123", "file_def456"],\n'
        ')\n'
        'print(batch.id, batch.status)'
    ),
    "getVectorStoreFileBatch": (
        'batch = openai.vector_stores.file_batches.retrieve(\n'
        '    vector_store_id="vs_abc123",\n'
        '    batch_id="vsfb_abc123",\n'
        ')\n'
        'print(batch.status, batch.file_counts)'
    ),
    "cancelVectorStoreFileBatch": (
        'openai.vector_stores.file_batches.cancel(\n'
        '    vector_store_id="vs_abc123",\n'
        '    batch_id="vsfb_abc123",\n'
        ')'
    ),
    "listFilesInVectorStoreBatch": (
        'files = openai.vector_stores.file_batches.list_files(\n'
        '    vector_store_id="vs_abc123",\n'
        '    batch_id="vsfb_abc123",\n'
        ')\n'
        'for f in files:\n'
        '    print(f.id, f.status)'
    ),

    # ── Preview-only: Audio ────────────────────────────────────────────
    "createSpeech": (
        'response = openai.audio.speech.create(\n'
        '    model="tts-1",\n'
        '    voice="alloy",\n'
        '    input="Hello, how are you today?",\n'
        ')\n'
        'response.stream_to_file("output.mp3")'
    ),
    "createTranscription": (
        'transcription = openai.audio.transcriptions.create(\n'
        '    model="whisper-1",\n'
        '    file=open("audio.mp3", "rb"),\n'
        ')\n'
        'print(transcription.text)'
    ),
    "createTranslation": (
        'translation = openai.audio.translations.create(\n'
        '    model="whisper-1",\n'
        '    file=open("audio_foreign.mp3", "rb"),\n'
        ')\n'
        'print(translation.text)'
    ),

    # ── Preview-only: Images ───────────────────────────────────────────
    "createImage": (
        'response = openai.images.generate(\n'
        '    model="dall-e-3",\n'
        '    prompt="A white cat sitting on a windowsill",\n'
        '    n=1,\n'
        '    size="1024x1024",\n'
        ')\n'
        'print(response.data[0].url)'
    ),
    "createImageEdit": (
        'response = openai.images.edit(\n'
        '    image=open("image.png", "rb"),\n'
        '    prompt="Add a sunset in the background",\n'
        '    n=1,\n'
        '    size="1024x1024",\n'
        ')\n'
        'print(response.data[0].url)'
    ),
    "createImageVariation": (
        'response = openai.images.create_variation(\n'
        '    image=open("image.png", "rb"),\n'
        '    n=1,\n'
        '    size="1024x1024",\n'
        ')\n'
        'print(response.data[0].url)'
    ),

    # ── Preview-only: Video ────────────────────────────────────────────
    "Videos_Create": (
        'job = openai.videos.create(\n'
        '    model="sora",\n'
        '    prompt="A serene mountain landscape at sunset",\n'
        ')\n'
        'print(job.id, job.status)'
    ),
    "Videos_List": (
        'jobs = openai.videos.list()\n'
        'for job in jobs:\n'
        '    print(job.id, job.status)'
    ),
    "Videos_Get": (
        'job = openai.videos.retrieve("video_abc123")\n'
        'print(job.status)'
    ),
    "Videos_Delete": (
        'openai.videos.delete("video_abc123")'
    ),
    "Videos_RetrieveContent": (
        'content = openai.videos.content("video_abc123")\n'
        'print(content.url)'
    ),
    "Videos_Remix": (
        'job = openai.videos.remix(\n'
        '    video_id="video_abc123",\n'
        '    prompt="Make it a night scene",\n'
        ')\n'
        'print(job.id)'
    ),
}


# ---------------------------------------------------------------------------
# Projects API samples — keyed by operationId
# ---------------------------------------------------------------------------

PROJECTS_SAMPLES = {
    # ── Connections ────────────────────────────────────────────────────
    "Connections_List": (
        'connections = client.connections.list()\n'
        'for conn in connections:\n'
        '    print(conn.name, conn.type)'
    ),
    "Connections_Get": (
        'connection = client.connections.get("my-connection")\n'
        'print(connection.name, connection.type)'
    ),
    "Connections_GetWithCredentials": (
        'connection = client.connections.get(\n'
        '    "my-connection",\n'
        '    include_credentials=True,\n'
        ')\n'
        'print(connection.name, connection.credentials)'
    ),

    # ── Datasets ───────────────────────────────────────────────────────
    "Datasets_ListLatest": (
        'datasets = client.datasets.list()\n'
        'for ds in datasets:\n'
        '    print(ds.name, ds.version)'
    ),
    "Datasets_ListVersions": (
        'versions = client.datasets.list_versions("my-dataset")\n'
        'for v in versions:\n'
        '    print(v.version, v.created_date)'
    ),
    "Datasets_GetVersion": (
        'dataset = client.datasets.get(\n'
        '    name="my-dataset",\n'
        '    version="1",\n'
        ')\n'
        'print(dataset.name, dataset.version)'
    ),
    "Datasets_CreateOrUpdateVersion": (
        'dataset = client.datasets.create_or_update(\n'
        '    name="my-dataset",\n'
        '    version="1",\n'
        '    body={"description": "Training data"},\n'
        ')\n'
        'print(dataset.name)'
    ),
    "Datasets_DeleteVersion": (
        'client.datasets.delete(\n'
        '    name="my-dataset",\n'
        '    version="1",\n'
        ')'
    ),
    "Datasets_GetCredentials": (
        'creds = client.datasets.get_credentials(\n'
        '    name="my-dataset",\n'
        '    version="1",\n'
        ')\n'
        'print(creds.credential_type)'
    ),
    "Datasets_StartPendingUploadVersion": (
        'upload = client.datasets.start_pending_upload(\n'
        '    name="my-dataset",\n'
        '    version="1",\n'
        '    body={"pending_upload_type": "temporary_sas"},\n'
        ')\n'
        'print(upload.blob_reference)'
    ),

    # ── Deployments ────────────────────────────────────────────────────
    "Deployments_List": (
        'deployments = client.deployments.list()\n'
        'for d in deployments:\n'
        '    print(d.name, d.model)'
    ),
    "Deployments_Get": (
        'deployment = client.deployments.get("gpt-4o")\n'
        'print(deployment.name, deployment.model)'
    ),

    # ── Indexes ────────────────────────────────────────────────────────
    "Indexes_ListLatest": (
        'indexes = client.indexes.list()\n'
        'for idx in indexes:\n'
        '    print(idx.name, idx.version)'
    ),
    "Indexes_ListVersions": (
        'versions = client.indexes.list_versions("my-index")\n'
        'for v in versions:\n'
        '    print(v.version)'
    ),
    "Indexes_GetVersion": (
        'index = client.indexes.get(\n'
        '    name="my-index",\n'
        '    version="1",\n'
        ')\n'
        'print(index.name)'
    ),
    "Indexes_CreateOrUpdateVersion": (
        'index = client.indexes.create_or_update(\n'
        '    name="my-index",\n'
        '    version="1",\n'
        '    body={"description": "Search index"},\n'
        ')\n'
        'print(index.name)'
    ),
    "Indexes_DeleteVersion": (
        'client.indexes.delete(\n'
        '    name="my-index",\n'
        '    version="1",\n'
        ')'
    ),

    # ── Evaluations (preview) ──────────────────────────────────────────
    "Evaluations_List": (
        'runs = client.beta.evaluations.list()\n'
        'for run in runs:\n'
        '    print(run.name, run.status)'
    ),
    "Evaluations_Get": (
        'run = client.beta.evaluations.get("my-eval-run")\n'
        'print(run.name, run.status)'
    ),
    "Evaluations_Delete": (
        'client.beta.evaluations.delete("my-eval-run")'
    ),
    "Evaluations_Cancel": (
        'client.beta.evaluations.cancel("my-eval-run")'
    ),
    "Evaluations_Create": (
        'run = client.beta.evaluations.create(\n'
        '    body={\n'
        '        "display_name": "my-eval-run",\n'
        '        "evaluators": {"relevance": {"id": "relevance"}},\n'
        '        "data": {"type": "dataset", "id": "my-dataset:1"},\n'
        '    },\n'
        ')\n'
        'print(run.name)'
    ),
    "Evaluations_CreateAgentEvaluation": (
        'run = client.beta.evaluations.create_agent(\n'
        '    body={\n'
        '        "display_name": "agent-eval",\n'
        '        "evaluators": {"relevance": {"id": "relevance"}},\n'
        '        "target": {"agent_id": "my-agent:1"},\n'
        '    },\n'
        ')\n'
        'print(run.name)'
    ),

    # ── RedTeams (preview) ─────────────────────────────────────────────
    "RedTeams_List": (
        'runs = client.beta.red_teams.list()\n'
        'for run in runs:\n'
        '    print(run.name, run.status)'
    ),
    "RedTeams_Get": (
        'run = client.beta.red_teams.get("my-redteam-run")\n'
        'print(run.name, run.status)'
    ),
    "RedTeams_Create": (
        'run = client.beta.red_teams.create(\n'
        '    body={\n'
        '        "display_name": "my-redteam",\n'
        '        "target": {"agent_id": "my-agent:1"},\n'
        '        "risk_categories": ["violence", "hate"],\n'
        '    },\n'
        ')\n'
        'print(run.name)'
    ),
}


# ---------------------------------------------------------------------------
# Injection logic
# ---------------------------------------------------------------------------

def _build_code_samples(
    op_id: str,
    lang_configs: list[tuple[str, str, dict[str, str], str]],
) -> list[dict]:
    """Build x-codeSamples array for an operation from multiple languages.

    lang_configs: list of (lang, label, samples_dict, preamble)
    """
    result = []
    for lang, label, samples, preamble in lang_configs:
        if op_id in samples:
            result.append({
                "lang": lang,
                "label": label,
                "source": preamble + samples[op_id],
            })
    return result


def inject_samples(
    spec_path: Path,
    lang_configs: list[tuple[str, str, dict[str, str], str]],
) -> int:
    """Inject x-codeSamples into an OpenAPI spec. Returns count of injected ops."""
    spec = json.load(spec_path.open())
    injected = 0
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if not isinstance(details, dict):
                continue
            op_id = details.get("operationId", "")
            samples = _build_code_samples(op_id, lang_configs)
            if samples:
                details["x-codeSamples"] = samples
                injected += 1
    with spec_path.open("w") as f:
        json.dump(spec, f, indent=2)
        f.write("\n")
    return injected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec-dir",
        default="docs-vnext/openapi",
        help="Directory containing OpenAPI spec files (default: docs-vnext/openapi)",
    )
    args = parser.parse_args()
    spec_dir = Path(args.spec_dir)

    # Import multi-language samples
    from sdk_samples_multilang import (
        CURL_OPENAI_PREAMBLE, CURL_OPENAI_SAMPLES,
        CURL_PROJECTS_PREAMBLE, CURL_PROJECTS_SAMPLES,
        CSHARP_OPENAI_PREAMBLE, CSHARP_OPENAI_SAMPLES,
        CSHARP_PROJECTS_PREAMBLE, CSHARP_PROJECTS_SAMPLES,
        JS_OPENAI_PREAMBLE, JS_OPENAI_SAMPLES,
        JS_PROJECTS_PREAMBLE, JS_PROJECTS_SAMPLES,
    )

    # Language configs for OpenAI v1 specs
    openai_langs = [
        ("python", "Python", OPENAI_SAMPLES, OPENAI_PREAMBLE),
        ("bash", "cURL", CURL_OPENAI_SAMPLES, CURL_OPENAI_PREAMBLE),
        ("csharp", "C#", CSHARP_OPENAI_SAMPLES, CSHARP_OPENAI_PREAMBLE),
        ("javascript", "JavaScript", JS_OPENAI_SAMPLES, JS_OPENAI_PREAMBLE),
    ]

    # Language configs for Projects specs
    projects_langs = [
        ("python", "Python", PROJECTS_SAMPLES, PROJECTS_PREAMBLE),
        ("bash", "cURL", CURL_PROJECTS_SAMPLES, CURL_PROJECTS_PREAMBLE),
        ("csharp", "C#", CSHARP_PROJECTS_SAMPLES, CSHARP_PROJECTS_PREAMBLE),
        ("javascript", "JavaScript", JS_PROJECTS_SAMPLES, JS_PROJECTS_PREAMBLE),
    ]

    total = 0
    for spec_file, langs in [
        ("openai-v1-stable.json", openai_langs),
        ("openai-v1-preview.json", openai_langs),
        ("projects-stable.json", projects_langs),
        ("projects-preview.json", projects_langs),
    ]:
        path = spec_dir / spec_file
        if not path.exists():
            print(f"  SKIP: {spec_file} (not found)", file=sys.stderr)
            continue
        n = inject_samples(path, langs)
        total += n
        print(f"  {spec_file}: {n} operations with code samples", file=sys.stderr)

    print(f"\nTotal: {total} operations with x-codeSamples injected", file=sys.stderr)


if __name__ == "__main__":
    main()
