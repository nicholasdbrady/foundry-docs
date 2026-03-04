#!/usr/bin/env python3
"""Add realistic example objects to OpenAPI response schemas for Mintlify rendering.

Usage:
    python scripts/add_response_examples.py <openapi-spec.json> [<openapi-spec.json> ...]
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# OpenAI-style response examples keyed by operationId
# ---------------------------------------------------------------------------
OPENAI_RESPONSE_EXAMPLES: dict = {
    # ── Responses API ──────────────────────────────────────────────────────
    "createResponse": {
        "id": "resp_67cb71b4e4a4819085e77aad18f06c92",
        "object": "response",
        "created_at": 1741312436,
        "status": "completed",
        "output": [
            {
                "id": "msg_67cb71b5c1988190b5fba3b237c63581",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "The capital of France is Paris.",
                        "annotations": [],
                    }
                ],
            }
        ],
        "model": "gpt-4o-2024-11-20",
        "usage": {"input_tokens": 13, "output_tokens": 8, "total_tokens": 21},
    },
    "getResponse": {
        "id": "resp_67cb71b4e4a4819085e77aad18f06c92",
        "object": "response",
        "created_at": 1741312436,
        "status": "completed",
        "output": [
            {
                "id": "msg_67cb71b5c1988190b5fba3b237c63581",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "The capital of France is Paris.",
                        "annotations": [],
                    }
                ],
            }
        ],
        "model": "gpt-4o-2024-11-20",
        "usage": {"input_tokens": 13, "output_tokens": 8, "total_tokens": 21},
    },
    "deleteResponse": {
        "id": "resp_67cb71b4e4a4819085e77aad18f06c92",
        "object": "response",
        "deleted": True,
    },
    "cancelResponse": {
        "id": "resp_67cb71b4e4a4819085e77aad18f06c92",
        "object": "response",
        "created_at": 1741312436,
        "status": "cancelled",
        "output": [],
        "model": "gpt-4o-2024-11-20",
        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    },
    "listInputItems": {
        "object": "list",
        "data": [
            {
                "id": "msg_67cb71b5c1988190b5fba3b237c63581",
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "What is the capital of France?"}],
            }
        ],
        "has_more": False,
        "first_id": "msg_67cb71b5c1988190b5fba3b237c63581",
        "last_id": "msg_67cb71b5c1988190b5fba3b237c63581",
    },
    # ── Chat Completions ───────────────────────────────────────────────────
    "createChatCompletion": {
        "id": "chatcmpl-abc123def456",
        "object": "chat.completion",
        "created": 1741312436,
        "model": "gpt-4o-2024-11-20",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello! How can I help you today?"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 9, "total_tokens": 18},
    },
    # ── Completions (legacy) ───────────────────────────────────────────────
    "createCompletion": {
        "id": "cmpl-abc123def456",
        "object": "text_completion",
        "created": 1741312436,
        "model": "gpt-3.5-turbo-instruct",
        "choices": [
            {"text": " world! This is a test.", "index": 0, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
    },
    # ── Embeddings ─────────────────────────────────────────────────────────
    "createEmbedding": {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [-0.0128, -0.0074, -0.0176, -0.0283, -0.0187],
                "index": 0,
            }
        ],
        "model": "text-embedding-3-large",
        "usage": {"prompt_tokens": 5, "total_tokens": 5},
    },
    # ── Models ─────────────────────────────────────────────────────────────
    "listModels": {
        "object": "list",
        "data": [
            {"id": "gpt-4o", "object": "model", "created": 1715367049, "owned_by": "system"},
            {"id": "gpt-4o-mini", "object": "model", "created": 1721172741, "owned_by": "system"},
            {
                "id": "text-embedding-3-large",
                "object": "model",
                "created": 1705953180,
                "owned_by": "system",
            },
        ],
    },
    "retrieveModel": {
        "id": "gpt-4o",
        "object": "model",
        "created": 1715367049,
        "owned_by": "system",
    },
    "deleteModel": {
        "id": "ft:gpt-4o-mini:my-org:custom-suffix:abc123",
        "object": "model",
        "deleted": True,
    },
    # ── Files ──────────────────────────────────────────────────────────────
    "createFile": {
        "id": "file-abc123def456",
        "object": "file",
        "bytes": 140,
        "created_at": 1741312436,
        "filename": "training_data.jsonl",
        "purpose": "fine-tune",
    },
    "listFiles": {
        "object": "list",
        "data": [
            {
                "id": "file-abc123def456",
                "object": "file",
                "bytes": 140,
                "created_at": 1741312436,
                "filename": "training_data.jsonl",
                "purpose": "fine-tune",
            }
        ],
    },
    "retrieveFile": {
        "id": "file-abc123def456",
        "object": "file",
        "bytes": 140,
        "created_at": 1741312436,
        "filename": "training_data.jsonl",
        "purpose": "fine-tune",
    },
    "deleteFile": {
        "id": "file-abc123def456",
        "object": "file",
        "deleted": True,
    },
    # ── Batches ────────────────────────────────────────────────────────────
    "createBatch": {
        "id": "batch_abc123def456",
        "object": "batch",
        "endpoint": "/v1/chat/completions",
        "input_file_id": "file-abc123def456",
        "completion_window": "24h",
        "status": "validating",
        "created_at": 1741312436,
    },
    "listBatches": {
        "object": "list",
        "data": [
            {
                "id": "batch_abc123def456",
                "object": "batch",
                "endpoint": "/v1/chat/completions",
                "input_file_id": "file-abc123def456",
                "completion_window": "24h",
                "status": "completed",
                "created_at": 1741312436,
            }
        ],
        "has_more": False,
        "first_id": "batch_abc123def456",
        "last_id": "batch_abc123def456",
    },
    "retrieveBatch": {
        "id": "batch_abc123def456",
        "object": "batch",
        "endpoint": "/v1/chat/completions",
        "input_file_id": "file-abc123def456",
        "completion_window": "24h",
        "status": "completed",
        "created_at": 1741312436,
        "completed_at": 1741315036,
        "output_file_id": "file-xyz789ghi012",
        "request_counts": {"total": 100, "completed": 95, "failed": 5},
    },
    "cancelBatch": {
        "id": "batch_abc123def456",
        "object": "batch",
        "endpoint": "/v1/chat/completions",
        "input_file_id": "file-abc123def456",
        "completion_window": "24h",
        "status": "cancelling",
        "created_at": 1741312436,
    },
    # ── Fine-tuning ────────────────────────────────────────────────────────
    "createFineTuningJob": {
        "id": "ftjob-abc123def456",
        "object": "fine_tuning.job",
        "model": "gpt-4o-mini-2024-07-18",
        "created_at": 1741312436,
        "status": "validating_files",
        "training_file": "file-abc123def456",
        "hyperparameters": {"n_epochs": "auto", "batch_size": "auto", "learning_rate_multiplier": "auto"},
        "organization_id": "org-abc123",
    },
    "listPaginatedFineTuningJobs": {
        "object": "list",
        "data": [
            {
                "id": "ftjob-abc123def456",
                "object": "fine_tuning.job",
                "model": "gpt-4o-mini-2024-07-18",
                "created_at": 1741312436,
                "status": "succeeded",
                "training_file": "file-abc123def456",
                "fine_tuned_model": "ft:gpt-4o-mini:my-org:custom-suffix:abc123",
            }
        ],
        "has_more": False,
    },
    "retrieveFineTuningJob": {
        "id": "ftjob-abc123def456",
        "object": "fine_tuning.job",
        "model": "gpt-4o-mini-2024-07-18",
        "created_at": 1741312436,
        "finished_at": 1741315036,
        "status": "succeeded",
        "training_file": "file-abc123def456",
        "fine_tuned_model": "ft:gpt-4o-mini:my-org:custom-suffix:abc123",
        "trained_tokens": 52814,
        "result_files": ["file-result123"],
    },
    "cancelFineTuningJob": {
        "id": "ftjob-abc123def456",
        "object": "fine_tuning.job",
        "model": "gpt-4o-mini-2024-07-18",
        "created_at": 1741312436,
        "status": "cancelled",
        "training_file": "file-abc123def456",
    },
    "pauseFineTuningJob": {
        "id": "ftjob-abc123def456",
        "object": "fine_tuning.job",
        "model": "gpt-4o-mini-2024-07-18",
        "created_at": 1741312436,
        "status": "paused",
        "training_file": "file-abc123def456",
    },
    "resumeFineTuningJob": {
        "id": "ftjob-abc123def456",
        "object": "fine_tuning.job",
        "model": "gpt-4o-mini-2024-07-18",
        "created_at": 1741312436,
        "status": "running",
        "training_file": "file-abc123def456",
    },
    "listFineTuningEvents": {
        "object": "list",
        "data": [
            {
                "id": "ftevent-abc123",
                "object": "fine_tuning.job.event",
                "created_at": 1741312436,
                "level": "info",
                "message": "Training started",
            }
        ],
        "has_more": False,
    },
    "listFineTuningJobCheckpoints": {
        "object": "list",
        "data": [
            {
                "id": "ftckpt-abc123def456",
                "object": "fine_tuning.job.checkpoint",
                "created_at": 1741313436,
                "fine_tuning_job_id": "ftjob-abc123def456",
                "fine_tuned_model_checkpoint": "ft:gpt-4o-mini:my-org:custom-suffix:abc123:ckpt-step-100",
                "step_number": 100,
                "metrics": {"step": 100, "train_loss": 0.234, "train_mean_token_accuracy": 0.891},
            }
        ],
        "has_more": False,
        "first_id": "ftckpt-abc123def456",
        "last_id": "ftckpt-abc123def456",
    },
    "listFineTuningCheckpointPermissions": {
        "object": "list",
        "data": [
            {
                "id": "ftckptperm-abc123",
                "object": "fine_tuning.job.checkpoint.permission",
                "created_at": 1741312436,
                "project_id": "proj-abc123",
            }
        ],
        "has_more": False,
        "first_id": "ftckptperm-abc123",
        "last_id": "ftckptperm-abc123",
    },
    "createFineTuningCheckpointPermission": {
        "id": "ftckptperm-abc123",
        "object": "fine_tuning.job.checkpoint.permission",
        "created_at": 1741312436,
        "project_id": "proj-abc123",
    },
    "deleteFineTuningCheckpointPermission": {
        "id": "ftckptperm-abc123",
        "object": "fine_tuning.job.checkpoint.permission",
        "deleted": True,
    },
    "FineTuning_CopyCheckpoint": {
        "id": "ftckpt-copy123",
        "object": "fine_tuning.job.checkpoint",
        "created_at": 1741312436,
        "fine_tuning_job_id": "ftjob-abc123def456",
        "fine_tuned_model_checkpoint": "ft:gpt-4o-mini:my-org:custom-suffix:abc123:ckpt-step-100",
        "step_number": 100,
        "metrics": {"step": 100, "train_loss": 0.234},
    },
    "FineTuning_GetCheckpoint": {
        "id": "ftckpt-abc123def456",
        "object": "fine_tuning.job.checkpoint",
        "created_at": 1741313436,
        "fine_tuning_job_id": "ftjob-abc123def456",
        "fine_tuned_model_checkpoint": "ft:gpt-4o-mini:my-org:custom-suffix:abc123:ckpt-step-100",
        "step_number": 100,
        "metrics": {"step": 100, "train_loss": 0.234, "train_mean_token_accuracy": 0.891},
    },
    # ── Evals ──────────────────────────────────────────────────────────────
    "createEval": {
        "id": "eval_abc123def456",
        "object": "eval",
        "name": "My Evaluation",
        "created_at": 1741312436,
        "data_source_config": {"type": "custom", "item_schema": {}},
        "testing_criteria": [],
        "metadata": {},
    },
    "listEvals": {
        "object": "list",
        "data": [
            {
                "id": "eval_abc123def456",
                "object": "eval",
                "name": "My Evaluation",
                "created_at": 1741312436,
            }
        ],
        "has_more": False,
        "first_id": "eval_abc123def456",
        "last_id": "eval_abc123def456",
    },
    "getEval": {
        "id": "eval_abc123def456",
        "object": "eval",
        "name": "My Evaluation",
        "created_at": 1741312436,
        "data_source_config": {"type": "custom", "item_schema": {}},
        "testing_criteria": [],
        "metadata": {},
    },
    "updateEval": {
        "id": "eval_abc123def456",
        "object": "eval",
        "name": "Updated Evaluation",
        "created_at": 1741312436,
        "data_source_config": {"type": "custom", "item_schema": {}},
        "testing_criteria": [],
        "metadata": {},
    },
    "deleteEval": {
        "id": "eval_abc123def456",
        "object": "eval",
        "deleted": True,
    },
    "createEvalRun": {
        "id": "evalrun_abc123def456",
        "object": "eval.run",
        "eval_id": "eval_abc123def456",
        "status": "queued",
        "created_at": 1741312436,
        "model": "gpt-4o-2024-11-20",
        "result_counts": {"total": 0, "passed": 0, "failed": 0, "errored": 0},
    },
    "getEvalRuns": {
        "object": "list",
        "data": [
            {
                "id": "evalrun_abc123def456",
                "object": "eval.run",
                "eval_id": "eval_abc123def456",
                "status": "completed",
                "created_at": 1741312436,
                "model": "gpt-4o-2024-11-20",
                "result_counts": {"total": 50, "passed": 45, "failed": 3, "errored": 2},
            }
        ],
        "has_more": False,
        "first_id": "evalrun_abc123def456",
        "last_id": "evalrun_abc123def456",
    },
    "getEvalRun": {
        "id": "evalrun_abc123def456",
        "object": "eval.run",
        "eval_id": "eval_abc123def456",
        "status": "completed",
        "created_at": 1741312436,
        "model": "gpt-4o-2024-11-20",
        "result_counts": {"total": 50, "passed": 45, "failed": 3, "errored": 2},
    },
    "cancelEvalRun": {
        "id": "evalrun_abc123def456",
        "object": "eval.run",
        "eval_id": "eval_abc123def456",
        "status": "canceled",
        "created_at": 1741312436,
        "model": "gpt-4o-2024-11-20",
    },
    "deleteEvalRun": {
        "id": "evalrun_abc123def456",
        "object": "eval.run",
        "deleted": True,
    },
    "getEvalRunOutputItems": {
        "object": "list",
        "data": [
            {
                "id": "evalrunitem_abc123",
                "object": "eval.run.output_item",
                "eval_run_id": "evalrun_abc123def456",
                "status": "pass",
                "created_at": 1741312436,
            }
        ],
        "has_more": False,
        "first_id": "evalrunitem_abc123",
        "last_id": "evalrunitem_abc123",
    },
    "getEvalRunOutputItem": {
        "id": "evalrunitem_abc123",
        "object": "eval.run.output_item",
        "eval_run_id": "evalrun_abc123def456",
        "status": "pass",
        "created_at": 1741312436,
    },
    # ── Graders ────────────────────────────────────────────────────────────
    "runGrader": {
        "result": {"score": 0.95, "passed": True, "explanation": "The response accurately answered the question."},
    },
    "validateGrader": {
        "valid": True,
        "errors": [],
    },
    # ── Containers ─────────────────────────────────────────────────────────
    "createContainer": {
        "id": "container_abc123def456",
        "object": "container",
        "name": "my-training-data",
        "created_at": 1741312436,
        "expires_after": None,
    },
    "listContainers": {
        "object": "list",
        "data": [
            {
                "id": "container_abc123def456",
                "object": "container",
                "name": "my-training-data",
                "created_at": 1741312436,
            }
        ],
        "has_more": False,
        "first_id": "container_abc123def456",
        "last_id": "container_abc123def456",
    },
    "retrieveContainer": {
        "id": "container_abc123def456",
        "object": "container",
        "name": "my-training-data",
        "created_at": 1741312436,
        "expires_after": None,
    },
    "createContainerFile": {
        "id": "container_file_abc123",
        "object": "container.file",
        "container_id": "container_abc123def456",
        "path": "/data/training.jsonl",
        "created_at": 1741312436,
        "bytes": 2048,
        "source": "user",
    },
    "listContainerFiles": {
        "object": "list",
        "data": [
            {
                "id": "container_file_abc123",
                "object": "container.file",
                "container_id": "container_abc123def456",
                "path": "/data/training.jsonl",
                "created_at": 1741312436,
                "bytes": 2048,
            }
        ],
        "has_more": False,
        "first_id": "container_file_abc123",
        "last_id": "container_file_abc123",
    },
    "retrieveContainerFile": {
        "id": "container_file_abc123",
        "object": "container.file",
        "container_id": "container_abc123def456",
        "path": "/data/training.jsonl",
        "created_at": 1741312436,
        "bytes": 2048,
        "source": "user",
    },
    # ── Conversations ──────────────────────────────────────────────────────
    "createConversation": {
        "id": "conv_abc123def456",
        "object": "conversation",
        "created_at": 1741312436,
        "metadata": {},
    },
    "retrieveConversation": {
        "id": "conv_abc123def456",
        "object": "conversation",
        "created_at": 1741312436,
        "metadata": {},
    },
    "updateConversation": {
        "id": "conv_abc123def456",
        "object": "conversation",
        "created_at": 1741312436,
        "metadata": {"topic": "customer-support"},
    },
    "deleteConversation": {
        "id": "conv_abc123def456",
        "object": "conversation",
        "deleted": True,
    },
    "createConversationItems": {
        "object": "list",
        "data": [
            {
                "id": "convitem_abc123",
                "object": "conversation.item",
                "conversation_id": "conv_abc123def456",
                "role": "user",
                "type": "message",
                "content": [{"type": "input_text", "text": "Hello!"}],
                "created_at": 1741312436,
            }
        ],
    },
    "listConversationItems": {
        "object": "list",
        "data": [
            {
                "id": "convitem_abc123",
                "object": "conversation.item",
                "conversation_id": "conv_abc123def456",
                "role": "user",
                "type": "message",
                "content": [{"type": "input_text", "text": "Hello!"}],
                "created_at": 1741312436,
            }
        ],
        "has_more": False,
        "first_id": "convitem_abc123",
        "last_id": "convitem_abc123",
    },
    "retrieveConversationItem": {
        "id": "convitem_abc123",
        "object": "conversation.item",
        "conversation_id": "conv_abc123def456",
        "role": "user",
        "type": "message",
        "content": [{"type": "input_text", "text": "Hello!"}],
        "created_at": 1741312436,
    },
    "deleteConversationItem": {
        "id": "convitem_abc123",
        "object": "conversation.item",
        "deleted": True,
    },
    # ── Vector Stores ──────────────────────────────────────────────────────
    "createVectorStore": {
        "id": "vs_abc123def456",
        "object": "vector_store",
        "name": "Product Knowledge Base",
        "created_at": 1741312436,
        "status": "completed",
        "usage_bytes": 0,
        "file_counts": {"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0},
    },
    "listVectorStores": {
        "object": "list",
        "data": [
            {
                "id": "vs_abc123def456",
                "object": "vector_store",
                "name": "Product Knowledge Base",
                "created_at": 1741312436,
                "status": "completed",
                "usage_bytes": 123456,
                "file_counts": {"in_progress": 0, "completed": 3, "failed": 0, "cancelled": 0, "total": 3},
            }
        ],
        "has_more": False,
        "first_id": "vs_abc123def456",
        "last_id": "vs_abc123def456",
    },
    "getVectorStore": {
        "id": "vs_abc123def456",
        "object": "vector_store",
        "name": "Product Knowledge Base",
        "created_at": 1741312436,
        "status": "completed",
        "usage_bytes": 123456,
        "file_counts": {"in_progress": 0, "completed": 3, "failed": 0, "cancelled": 0, "total": 3},
    },
    "modifyVectorStore": {
        "id": "vs_abc123def456",
        "object": "vector_store",
        "name": "Updated Knowledge Base",
        "created_at": 1741312436,
        "status": "completed",
        "usage_bytes": 123456,
        "file_counts": {"in_progress": 0, "completed": 3, "failed": 0, "cancelled": 0, "total": 3},
    },
    "deleteVectorStore": {
        "id": "vs_abc123def456",
        "object": "vector_store",
        "deleted": True,
    },
    "createVectorStoreFile": {
        "id": "file-vs-abc123",
        "object": "vector_store.file",
        "vector_store_id": "vs_abc123def456",
        "created_at": 1741312436,
        "status": "in_progress",
        "usage_bytes": 0,
    },
    "listVectorStoreFiles": {
        "object": "list",
        "data": [
            {
                "id": "file-vs-abc123",
                "object": "vector_store.file",
                "vector_store_id": "vs_abc123def456",
                "created_at": 1741312436,
                "status": "completed",
                "usage_bytes": 12345,
            }
        ],
        "has_more": False,
        "first_id": "file-vs-abc123",
        "last_id": "file-vs-abc123",
    },
    "getVectorStoreFile": {
        "id": "file-vs-abc123",
        "object": "vector_store.file",
        "vector_store_id": "vs_abc123def456",
        "created_at": 1741312436,
        "status": "completed",
        "usage_bytes": 12345,
    },
    "updateVectorStoreFileAttributes": {
        "id": "file-vs-abc123",
        "object": "vector_store.file",
        "vector_store_id": "vs_abc123def456",
        "created_at": 1741312436,
        "status": "completed",
        "usage_bytes": 12345,
        "attributes": {"category": "product-docs"},
    },
    "deleteVectorStoreFile": {
        "id": "file-vs-abc123",
        "object": "vector_store.file",
        "deleted": True,
    },
    "retrieveVectorStoreFileContent": {
        "content": "This is the content of the file stored in the vector store.",
    },
    "searchVectorStore": {
        "object": "vector_store.search_results.page",
        "data": [
            {
                "file_id": "file-vs-abc123",
                "filename": "product-docs.pdf",
                "score": 0.92,
                "content": [{"type": "text", "text": "Our product supports both REST API and SDK integrations."}],
                "attributes": {},
            }
        ],
        "has_more": False,
    },
    "createVectorStoreFileBatch": {
        "id": "vsfb_abc123def456",
        "object": "vector_store.file_batch",
        "vector_store_id": "vs_abc123def456",
        "created_at": 1741312436,
        "status": "in_progress",
        "file_counts": {"in_progress": 3, "completed": 0, "failed": 0, "cancelled": 0, "total": 3},
    },
    "getVectorStoreFileBatch": {
        "id": "vsfb_abc123def456",
        "object": "vector_store.file_batch",
        "vector_store_id": "vs_abc123def456",
        "created_at": 1741312436,
        "status": "completed",
        "file_counts": {"in_progress": 0, "completed": 3, "failed": 0, "cancelled": 0, "total": 3},
    },
    "cancelVectorStoreFileBatch": {
        "id": "vsfb_abc123def456",
        "object": "vector_store.file_batch",
        "vector_store_id": "vs_abc123def456",
        "created_at": 1741312436,
        "status": "cancelling",
        "file_counts": {"in_progress": 1, "completed": 2, "failed": 0, "cancelled": 0, "total": 3},
    },
    "listFilesInVectorStoreBatch": {
        "object": "list",
        "data": [
            {
                "id": "file-vs-abc123",
                "object": "vector_store.file",
                "vector_store_id": "vs_abc123def456",
                "created_at": 1741312436,
                "status": "completed",
                "usage_bytes": 12345,
            }
        ],
        "has_more": False,
        "first_id": "file-vs-abc123",
        "last_id": "file-vs-abc123",
    },
    # ── Threads / Assistants (legacy) ──────────────────────────────────────
    "createThread": {
        "id": "thread_abc123def456",
        "object": "thread",
        "created_at": 1741312436,
        "metadata": {},
    },
    "retrieveThread": {
        "id": "thread_abc123def456",
        "object": "thread",
        "created_at": 1741312436,
        "metadata": {},
    },
    "modifyThread": {
        "id": "thread_abc123def456",
        "object": "thread",
        "created_at": 1741312436,
        "metadata": {"project": "my-project"},
    },
    "deleteThread": {
        "id": "thread_abc123def456",
        "object": "thread",
        "deleted": True,
    },
    "createMessage": {
        "id": "msg_abc123def456",
        "object": "thread.message",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "role": "user",
        "content": [{"type": "text", "text": {"value": "What is the weather today?", "annotations": []}}],
        "status": "completed",
    },
    "listMessages": {
        "object": "list",
        "data": [
            {
                "id": "msg_abc123def456",
                "object": "thread.message",
                "created_at": 1741312436,
                "thread_id": "thread_abc123def456",
                "role": "assistant",
                "content": [{"type": "text", "text": {"value": "Hello! How can I help you?", "annotations": []}}],
                "status": "completed",
            }
        ],
        "has_more": False,
        "first_id": "msg_abc123def456",
        "last_id": "msg_abc123def456",
    },
    "retrieveMessage": {
        "id": "msg_abc123def456",
        "object": "thread.message",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "role": "user",
        "content": [{"type": "text", "text": {"value": "What is the weather today?", "annotations": []}}],
        "status": "completed",
    },
    "modifyMessage": {
        "id": "msg_abc123def456",
        "object": "thread.message",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "role": "user",
        "content": [{"type": "text", "text": {"value": "What is the weather today?", "annotations": []}}],
        "status": "completed",
        "metadata": {"priority": "high"},
    },
    "deleteMessage": {
        "id": "msg_abc123def456",
        "object": "thread.message",
        "deleted": True,
    },
    "createRun": {
        "id": "run_abc123def456",
        "object": "thread.run",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "assistant_id": "asst_abc123def456",
        "status": "queued",
        "model": "gpt-4o",
    },
    "listRuns": {
        "object": "list",
        "data": [
            {
                "id": "run_abc123def456",
                "object": "thread.run",
                "created_at": 1741312436,
                "thread_id": "thread_abc123def456",
                "assistant_id": "asst_abc123def456",
                "status": "completed",
                "model": "gpt-4o",
            }
        ],
        "has_more": False,
        "first_id": "run_abc123def456",
        "last_id": "run_abc123def456",
    },
    "retrieveRun": {
        "id": "run_abc123def456",
        "object": "thread.run",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "assistant_id": "asst_abc123def456",
        "status": "completed",
        "model": "gpt-4o",
    },
    "modifyRun": {
        "id": "run_abc123def456",
        "object": "thread.run",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "assistant_id": "asst_abc123def456",
        "status": "completed",
        "model": "gpt-4o",
        "metadata": {"run_type": "evaluation"},
    },
    "cancelRun": {
        "id": "run_abc123def456",
        "object": "thread.run",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "assistant_id": "asst_abc123def456",
        "status": "cancelling",
        "model": "gpt-4o",
    },
    "submitToolOutputsToRun": {
        "id": "run_abc123def456",
        "object": "thread.run",
        "created_at": 1741312436,
        "thread_id": "thread_abc123def456",
        "assistant_id": "asst_abc123def456",
        "status": "queued",
        "model": "gpt-4o",
    },
    "createThreadAndRun": {
        "id": "run_abc123def456",
        "object": "thread.run",
        "created_at": 1741312436,
        "thread_id": "thread_xyz789ghi012",
        "assistant_id": "asst_abc123def456",
        "status": "queued",
        "model": "gpt-4o",
    },
    "listRunSteps": {
        "object": "list",
        "data": [
            {
                "id": "step_abc123def456",
                "object": "thread.run.step",
                "created_at": 1741312436,
                "run_id": "run_abc123def456",
                "assistant_id": "asst_abc123def456",
                "thread_id": "thread_abc123def456",
                "type": "message_creation",
                "status": "completed",
                "step_details": {
                    "type": "message_creation",
                    "message_creation": {"message_id": "msg_abc123def456"},
                },
            }
        ],
        "has_more": False,
        "first_id": "step_abc123def456",
        "last_id": "step_abc123def456",
    },
    "getRunStep": {
        "id": "step_abc123def456",
        "object": "thread.run.step",
        "created_at": 1741312436,
        "run_id": "run_abc123def456",
        "assistant_id": "asst_abc123def456",
        "thread_id": "thread_abc123def456",
        "type": "message_creation",
        "status": "completed",
        "step_details": {
            "type": "message_creation",
            "message_creation": {"message_id": "msg_abc123def456"},
        },
    },
    # ── Realtime ───────────────────────────────────────────────────────────
    "createRealtimeSession": {
        "id": "sess_abc123def456",
        "object": "realtime.session",
        "model": "gpt-4o-realtime-preview",
        "modalities": ["text", "audio"],
        "voice": "alloy",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "turn_detection": {"type": "server_vad"},
    },
    "createRealtimeClientSecret": {
        "id": "sess_abc123def456",
        "object": "realtime.session",
        "client_secret": {
            "value": "ek_abc123def456ghi789",
            "expires_at": 1741316036,
        },
    },
    "createRealtimeTranscriptionSession": {
        "id": "sess_trans_abc123",
        "object": "realtime.transcription_session",
        "model": "gpt-4o-transcribe",
        "input_audio_format": "pcm16",
    },
    # ── Audio (preview only) ───────────────────────────────────────────────
    "createTranscription": {
        "text": "Hello, this is a transcription of the audio file.",
    },
    "createTranslation": {
        "text": "Hello, this is the English translation of the audio.",
    },
    # ── Images (preview only) ─────────────────────────────────────────────
    "createImage": {
        "created": 1741312436,
        "data": [
            {
                "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/generated-image.png",
                "revised_prompt": "A beautiful sunset over the ocean with vibrant orange and purple hues.",
            }
        ],
    },
    "createImageEdit": {
        "created": 1741312436,
        "data": [
            {
                "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/edited-image.png",
            }
        ],
    },
    "createImageVariation": {
        "created": 1741312436,
        "data": [
            {
                "url": "https://oaidalleapiprodscus.blob.core.windows.net/private/variation-image.png",
            }
        ],
    },
    # ── Videos (preview only) ─────────────────────────────────────────────
    "Videos_Create": {
        "id": "video_abc123def456",
        "object": "video",
        "status": "queued",
        "created_at": 1741312436,
        "model": "sora",
        "prompt": "A serene lake surrounded by mountains at sunrise.",
    },
    "Videos_List": {
        "object": "list",
        "data": [
            {
                "id": "video_abc123def456",
                "object": "video",
                "status": "completed",
                "created_at": 1741312436,
                "model": "sora",
            }
        ],
        "has_more": False,
        "first_id": "video_abc123def456",
        "last_id": "video_abc123def456",
    },
    "Videos_Get": {
        "id": "video_abc123def456",
        "object": "video",
        "status": "completed",
        "created_at": 1741312436,
        "model": "sora",
        "prompt": "A serene lake surrounded by mountains at sunrise.",
    },
    "Videos_Delete": {
        "id": "video_abc123def456",
        "object": "video",
        "deleted": True,
    },
    "Videos_Remix": {
        "id": "video_remix123",
        "object": "video",
        "status": "queued",
        "created_at": 1741312436,
        "model": "sora",
        "prompt": "Same scene but at sunset with warm colors.",
    },
}

# ---------------------------------------------------------------------------
# Projects API response examples keyed by operationId
# ---------------------------------------------------------------------------
PROJECTS_RESPONSE_EXAMPLES: dict = {
    # ── Connections ────────────────────────────────────────────────────────
    "Connections_List": {
        "value": [
            {
                "name": "my-aoai-connection",
                "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.MachineLearningServices/workspaces/my-project/connections/my-aoai-connection",
                "type": "AzureOpenAI",
                "properties": {
                    "category": "AzureOpenAI",
                    "target": "https://my-aoai.openai.azure.com/",
                    "authType": "ApiKey",
                },
            }
        ],
    },
    "Connections_Get": {
        "name": "my-aoai-connection",
        "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.MachineLearningServices/workspaces/my-project/connections/my-aoai-connection",
        "type": "AzureOpenAI",
        "properties": {
            "category": "AzureOpenAI",
            "target": "https://my-aoai.openai.azure.com/",
            "authType": "ApiKey",
        },
    },
    "Connections_GetWithCredentials": {
        "name": "my-aoai-connection",
        "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.MachineLearningServices/workspaces/my-project/connections/my-aoai-connection",
        "type": "AzureOpenAI",
        "properties": {
            "category": "AzureOpenAI",
            "target": "https://my-aoai.openai.azure.com/",
            "authType": "ApiKey",
            "credentials": {"key": "YOUR_API_KEY"},
        },
    },
    # ── Datasets ───────────────────────────────────────────────────────────
    "Datasets_ListLatest": {
        "value": [
            {
                "name": "my-dataset",
                "version": "1",
                "uri": "https://my-storage.blob.core.windows.net/datasets/my-dataset/",
                "type": "uri_folder",
                "tags": {"purpose": "training"},
            }
        ],
    },
    "Datasets_ListVersions": {
        "value": [
            {
                "name": "my-dataset",
                "version": "1",
                "uri": "https://my-storage.blob.core.windows.net/datasets/my-dataset/v1/",
                "type": "uri_folder",
            },
            {
                "name": "my-dataset",
                "version": "2",
                "uri": "https://my-storage.blob.core.windows.net/datasets/my-dataset/v2/",
                "type": "uri_folder",
            },
        ],
    },
    "Datasets_GetVersion": {
        "name": "my-dataset",
        "version": "1",
        "uri": "https://my-storage.blob.core.windows.net/datasets/my-dataset/v1/",
        "type": "uri_folder",
        "tags": {"purpose": "training"},
    },
    "Datasets_CreateOrUpdateVersion": {
        "name": "my-dataset",
        "version": "1",
        "uri": "https://my-storage.blob.core.windows.net/datasets/my-dataset/v1/",
        "type": "uri_folder",
        "tags": {"purpose": "training"},
    },
    "Datasets_GetCredentials": {
        "credentials": {
            "sasUri": "https://my-storage.blob.core.windows.net/datasets/my-dataset?sv=2023-01-01&sig=YOUR_SAS_TOKEN",
        },
    },
    "Datasets_StartPendingUploadVersion": {
        "blobReference": {
            "blobUri": "https://my-storage.blob.core.windows.net/datasets/my-dataset/v1/",
            "credential": {
                "sasUri": "https://my-storage.blob.core.windows.net/datasets?sv=2023-01-01&sig=YOUR_SAS_TOKEN",
            },
        },
    },
    # ── Deployments ────────────────────────────────────────────────────────
    "Deployments_List": {
        "value": [
            {
                "name": "gpt-4o",
                "type": "Azure.OpenAI",
                "model": {"name": "gpt-4o", "version": "2024-11-20", "format": "OpenAI"},
                "properties": {"provisioningState": "Succeeded"},
            },
            {
                "name": "text-embedding-3-large",
                "type": "Azure.OpenAI",
                "model": {"name": "text-embedding-3-large", "version": "1", "format": "OpenAI"},
                "properties": {"provisioningState": "Succeeded"},
            },
        ],
    },
    "Deployments_Get": {
        "name": "gpt-4o",
        "type": "Azure.OpenAI",
        "model": {"name": "gpt-4o", "version": "2024-11-20", "format": "OpenAI"},
        "properties": {"provisioningState": "Succeeded"},
    },
    # ── Indexes ────────────────────────────────────────────────────────────
    "Indexes_ListLatest": {
        "value": [
            {
                "name": "my-search-index",
                "version": "1",
                "type": "AzureSearch",
                "tags": {"domain": "product-docs"},
            }
        ],
    },
    "Indexes_ListVersions": {
        "value": [
            {
                "name": "my-search-index",
                "version": "1",
                "type": "AzureSearch",
            },
            {
                "name": "my-search-index",
                "version": "2",
                "type": "AzureSearch",
            },
        ],
    },
    "Indexes_GetVersion": {
        "name": "my-search-index",
        "version": "1",
        "type": "AzureSearch",
        "tags": {"domain": "product-docs"},
    },
    "Indexes_CreateOrUpdateVersion": {
        "name": "my-search-index",
        "version": "1",
        "type": "AzureSearch",
        "tags": {"domain": "product-docs"},
    },
    # ── Evaluations (preview only) ─────────────────────────────────────────
    "Evaluations_List": {
        "value": [
            {
                "id": "eval-abc123def456",
                "displayName": "Chat Quality Evaluation",
                "status": "Completed",
                "tags": {"domain": "customer-support"},
            }
        ],
    },
    "Evaluations_Get": {
        "id": "eval-abc123def456",
        "displayName": "Chat Quality Evaluation",
        "status": "Completed",
        "tags": {"domain": "customer-support"},
    },
    "Evaluations_Create": {
        "id": "eval-abc123def456",
        "displayName": "Chat Quality Evaluation",
        "status": "Queued",
        "tags": {"domain": "customer-support"},
    },
    "Evaluations_CreateAgentEvaluation": {
        "id": "agenteval-abc123",
        "displayName": "Agent Performance Evaluation",
        "status": "Queued",
    },
    # ── Red Teams (preview only) ───────────────────────────────────────────
    "RedTeams_List": {
        "value": [
            {
                "id": "redteam-abc123def456",
                "displayName": "Safety Red Team",
                "status": "Completed",
            }
        ],
    },
    "RedTeams_Get": {
        "id": "redteam-abc123def456",
        "displayName": "Safety Red Team",
        "status": "Completed",
    },
    "RedTeams_Create": {
        "id": "redteam-abc123def456",
        "displayName": "Safety Red Team",
        "status": "Queued",
    },
}


def add_examples_to_spec(spec_path: str) -> tuple[int, int]:
    """Add response examples to an OpenAPI spec file.

    Returns (total_operations, examples_added) counts.
    """
    with open(spec_path) as f:
        spec = json.load(f)

    is_projects = "projects" in Path(spec_path).name.lower()
    examples = PROJECTS_RESPONSE_EXAMPLES if is_projects else OPENAI_RESPONSE_EXAMPLES

    total = 0
    added = 0

    for _path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue

            operation_id = details.get("operationId")
            if not operation_id:
                continue

            for code in ("200", "201"):
                resp = details.get("responses", {}).get(code)
                if not resp:
                    continue

                content = resp.get("content", {}).get("application/json")
                if not content:
                    continue

                total += 1

                if "example" in content or "examples" in content:
                    continue

                example = examples.get(operation_id)
                if example:
                    content["example"] = example
                    added += 1

    with open(spec_path, "w") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return total, added


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <spec.json> [<spec.json> ...]", file=sys.stderr)
        sys.exit(1)

    for path in sys.argv[1:]:
        total, added = add_examples_to_spec(path)
        remaining = total - added
        print(f"{path}: {total} operations, {added} examples added, {remaining} without examples")


if __name__ == "__main__":
    main()
