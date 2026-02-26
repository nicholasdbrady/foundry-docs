"""Markdown-aware chunking utilities for Foundry docs."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from pathlib import Path

from .indexer import extract_description, extract_title


def _strip_front_matter(content: str) -> str:
    return re.sub(r"^---\n.*?---\n", "", content, flags=re.DOTALL)


def _slugify(value: str) -> str:
    lowered = value.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s-]", "", lowered)
    return re.sub(r"\s+", "-", cleaned).strip("-") or "section"


def _encode_search_key(raw: str) -> str:
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def _split_with_overlap(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentence_parts = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentence_parts:
        sentence = sentence.strip()
        if not sentence:
            continue

        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail} {sentence}".strip()
        else:
            hard_chunks = [
                sentence[idx: idx + max_chars]
                for idx in range(0, len(sentence), max_chars)
            ]
            chunks.extend(hard_chunks[:-1])
            current = hard_chunks[-1]

    if current:
        chunks.append(current)

    return chunks


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    doc_path: str
    title: str
    description: str
    section_heading: str
    content: str
    char_count: int


class MarkdownChunker:
    """Chunk MDX docs by heading structure with overlap fallback for long sections."""

    def __init__(self, max_chars: int = 4000, overlap_chars: int = 400):
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def _split_by_headings(self, body: str) -> list[tuple[str, str]]:
        lines = body.splitlines()
        sections: list[tuple[str, list[str]]] = []
        current_heading = "Introduction"
        current_lines: list[str] = []

        for line in lines:
            if re.match(r"^###?\s+", line):
                if current_lines:
                    sections.append((current_heading, current_lines))
                current_heading = re.sub(r"^###?\s+", "", line).strip() or "Introduction"
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_heading, current_lines))

        return [(heading, "\n".join(block).strip()) for heading, block in sections if "\n".join(block).strip()]

    def chunk(self, doc_path: str, raw_mdx: str) -> list[Chunk]:
        title = extract_title(raw_mdx) or doc_path.split("/")[-1]
        description = extract_description(raw_mdx)
        body = _strip_front_matter(raw_mdx)

        all_chunks: list[Chunk] = []
        for section_index, (heading, section_text) in enumerate(self._split_by_headings(body)):
            prefixed = f"{title} > {heading}\n\n{section_text}".strip()
            chunks = _split_with_overlap(prefixed, self.max_chars, self.overlap_chars)
            heading_slug = _slugify(heading)

            for split_index, chunk_text in enumerate(chunks):
                raw_chunk_id = f"{doc_path}#{heading_slug}#{section_index}-{split_index}"
                chunk_id = _encode_search_key(raw_chunk_id)
                all_chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        doc_path=doc_path,
                        title=title,
                        description=description,
                        section_heading=heading,
                        content=chunk_text,
                        char_count=len(chunk_text),
                    )
                )

        return all_chunks


def chunk_directory(docs_dir: Path, chunker: MarkdownChunker | None = None) -> list[Chunk]:
    chunker = chunker or MarkdownChunker()
    chunks: list[Chunk] = []
    for mdx_file in sorted(docs_dir.rglob("*.mdx")):
        rel_path = str(mdx_file.relative_to(docs_dir))
        doc_path = rel_path.rsplit(".mdx", 1)[0]
        raw = mdx_file.read_text(encoding="utf-8", errors="replace")
        chunks.extend(chunker.chunk(doc_path=doc_path, raw_mdx=raw))
    return chunks