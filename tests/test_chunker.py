"""Tests for foundry_docs_mcp.chunker — markdown-aware chunking."""

from foundry_docs_mcp.chunker import Chunk, MarkdownChunker, chunk_directory, _split_with_overlap, _slugify, _encode_search_key


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert _slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert _slugify("What's New?") == "whats-new"

    def test_empty(self):
        assert _slugify("") == "section"

    def test_preserves_hyphens(self):
        assert _slugify("fine-tuning") == "fine-tuning"


# ---------------------------------------------------------------------------
# _encode_search_key
# ---------------------------------------------------------------------------

class TestEncodeSearchKey:
    def test_deterministic(self):
        a = _encode_search_key("test/doc#intro#0-0")
        b = _encode_search_key("test/doc#intro#0-0")
        assert a == b

    def test_no_padding(self):
        result = _encode_search_key("short")
        assert "=" not in result


# ---------------------------------------------------------------------------
# _split_with_overlap
# ---------------------------------------------------------------------------

class TestSplitWithOverlap:
    def test_short_text_no_split(self):
        result = _split_with_overlap("short text", max_chars=100, overlap=10)
        assert result == ["short text"]

    def test_splits_at_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence."
        chunks = _split_with_overlap(text, max_chars=30, overlap=10)
        assert len(chunks) >= 2
        assert "First sentence." in chunks[0]

    def test_overlap_present(self):
        text = "Sentence one is here. Sentence two is next. Sentence three ends it."
        chunks = _split_with_overlap(text, max_chars=40, overlap=15)
        if len(chunks) >= 2:
            # The tail of chunk 0 should appear at the start of chunk 1
            tail = chunks[0][-15:]
            assert any(tail in c for c in chunks[1:])

    def test_empty_text(self):
        result = _split_with_overlap("", max_chars=100, overlap=10)
        assert result == [""]


# ---------------------------------------------------------------------------
# MarkdownChunker
# ---------------------------------------------------------------------------

SAMPLE_MDX = '''---
title: "Agent Overview"
description: "How to build agents"
---

## Introduction

Agents are autonomous programs that use tools.

## Getting Started

To get started, create a project.

### Prerequisites

You need Python 3.11+.

## Advanced Topics

This section covers advanced patterns.
'''


class TestMarkdownChunker:
    def test_basic_chunking(self):
        chunker = MarkdownChunker(max_chars=4000, overlap_chars=400)
        chunks = chunker.chunk("agents/overview", SAMPLE_MDX)
        assert len(chunks) >= 1
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunk_metadata(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk("agents/overview", SAMPLE_MDX)
        for chunk in chunks:
            assert chunk.doc_path == "agents/overview"
            assert chunk.title == "Agent Overview"
            assert chunk.description == "How to build agents"
            assert chunk.chunk_id  # non-empty
            assert chunk.char_count == len(chunk.content)

    def test_section_headings_captured(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk("test", SAMPLE_MDX)
        headings = {c.section_heading for c in chunks}
        assert "Introduction" in headings
        assert "Getting Started" in headings

    def test_large_section_splits(self):
        """A section exceeding max_chars should be split with overlap."""
        big_section = "## Big Section\n\n" + "This is a sentence. " * 500
        mdx = f'---\ntitle: "Big"\ndescription: ""\n---\n\n{big_section}'
        chunker = MarkdownChunker(max_chars=200, overlap_chars=50)
        chunks = chunker.chunk("big-doc", mdx)
        assert len(chunks) > 1

    def test_empty_doc(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk("empty", "")
        assert chunks == []

    def test_no_frontmatter(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk("no-fm", "## Section\n\nSome content here.")
        assert len(chunks) >= 1
        assert chunks[0].title == "no-fm"


# ---------------------------------------------------------------------------
# chunk_directory
# ---------------------------------------------------------------------------

class TestChunkDirectory:
    def test_chunks_from_directory(self, tmp_path):
        (tmp_path / "doc.mdx").write_text(
            '---\ntitle: "Doc"\ndescription: "A doc"\n---\n\n## Intro\n\nContent.'
        )
        chunks = chunk_directory(tmp_path)
        assert len(chunks) >= 1
        assert chunks[0].doc_path == "doc"

    def test_nested_directory(self, tmp_path):
        sub = tmp_path / "agents" / "dev"
        sub.mkdir(parents=True)
        (sub / "overview.mdx").write_text(
            '---\ntitle: "Overview"\ndescription: ""\n---\n\n## Intro\n\nText.'
        )
        chunks = chunk_directory(tmp_path)
        assert any(c.doc_path == "agents/dev/overview" for c in chunks)

    def test_empty_directory(self, tmp_path):
        chunks = chunk_directory(tmp_path)
        assert chunks == []
