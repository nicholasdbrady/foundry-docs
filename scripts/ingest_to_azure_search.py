#!/usr/bin/env python3
"""Chunk docs and ingest into Azure AI Search with embeddings."""

from __future__ import annotations

import argparse
import hashlib
import os
import time
from pathlib import Path

from foundry_docs_mcp.chunker import chunk_directory
from foundry_docs_mcp.foundry_client import FoundryProjectOpenAI
from foundry_docs_mcp.indexer import AzureSearchIndex

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(os.environ.get("FOUNDRY_DOCS_DIR", PROJECT_ROOT / "docs"))


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Incrementally sync docs chunks to Azure AI Search")
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate the index before ingest")
    parser.add_argument("--dry-run", action="store_true", help="Compute diff only, do not upload/delete")
    parser.add_argument("--batch-size", type=int, default=100, help="Embedding/upload batch size")
    return parser.parse_args()


def main():
    args = _parse_args()
    started = time.perf_counter()

    search_endpoint = _require("AZURE_SEARCH_ENDPOINT")
    search_index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "foundry-docs")
    search_api_key = os.environ.get("AZURE_SEARCH_API_KEY")

    project_endpoint = _require("AZURE_AI_PROJECT_ENDPOINT")
    embedding_model = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    foundry_client = FoundryProjectOpenAI(
        project_endpoint=project_endpoint,
        embedding_model=embedding_model,
        api_key=os.environ.get("AZURE_AI_PROJECT_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY"),
    )

    azure_index = AzureSearchIndex(
        endpoint=search_endpoint,
        index_name=search_index_name,
        api_key=search_api_key,
    )
    azure_index.create_index(recreate=args.recreate)

    chunks = chunk_directory(DOCS_DIR)

    def embed_batch(texts: list[str]) -> list[list[float]]:
        return foundry_client.embed_texts(texts)

    records = {
        chunk.chunk_id: {
            "chunk_id": chunk.chunk_id,
            "doc_path": chunk.doc_path,
            "content_hash": _content_hash(chunk.content),
            "title": chunk.title,
            "section_heading": chunk.section_heading,
            "description": chunk.description,
            "content": chunk.content,
        }
        for chunk in chunks
    }

    if args.recreate:
        to_upsert = list(records.values())
        to_delete: list[str] = []
        unchanged = 0
        new_count = len(to_upsert)
        changed_count = 0
        existing_count = 0
    else:
        existing = azure_index.get_existing_chunk_metadata()
        existing_count = len(existing)
        incoming_keys = set(records.keys())
        existing_keys = set(existing.keys())

        to_delete = sorted(existing_keys - incoming_keys)
        to_upsert = []
        unchanged = 0
        new_count = 0
        changed_count = 0

        for chunk_id, record in records.items():
            prev = existing.get(chunk_id)
            if prev is None:
                new_count += 1
                to_upsert.append(record)
                continue
            if prev.get("content_hash") != record["content_hash"]:
                changed_count += 1
                to_upsert.append(record)
            else:
                unchanged += 1

    print(
        "Sync plan:",
        f"existing={existing_count}",
        f"incoming={len(records)}",
        f"new={new_count}",
        f"changed={changed_count}",
        f"unchanged={unchanged}",
        f"delete={len(to_delete)}",
    )

    if args.dry_run:
        duration = time.perf_counter() - started
        print(f"Dry run complete in {duration:.1f}s")
        foundry_client.close()
        return

    try:
        if to_upsert:
            azure_index.upload_chunks(to_upsert, embedding_fn=embed_batch, batch_size=max(args.batch_size, 1))
        if to_delete:
            azure_index.delete_chunks(to_delete)
    finally:
        foundry_client.close()

    duration = time.perf_counter() - started
    docs = {chunk.doc_path for chunk in chunks}
    print(
        f"Ingest complete: docs={len(docs)} chunks={len(chunks)} "
        f"upserted={len(to_upsert)} deleted={len(to_delete)} "
        f"index={search_index_name} duration={duration:.1f}s"
    )


if __name__ == "__main__":
    main()
