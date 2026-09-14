"""Tests for foundry_docs_mcp.indexer — TF-IDF search index."""


from foundry_docs_mcp.indexer import SearchIndex, extract_description, extract_title, strip_mdx_markup, tokenize


# ---------------------------------------------------------------------------
# tokenize
# ---------------------------------------------------------------------------

class TestTokenize:
    def test_basic(self):
        assert tokenize("Hello World") == ["hello", "world"]

    def test_strips_html_tags(self):
        tokens = tokenize("<Note>Important info</Note>")
        assert "note" not in tokens
        assert "important" in tokens

    def test_strips_code_blocks(self):
        text = "Before ```python\nprint('hi')\n``` After"
        tokens = tokenize(text)
        assert "print" not in tokens
        assert "before" in tokens
        assert "after" in tokens

    def test_filters_single_char(self):
        assert tokenize("a b cd") == ["cd"]

    def test_hyphenated_tokens(self):
        tokens = tokenize("fine-tuning is great")
        assert "fine-tuning" in tokens

    def test_empty_string(self):
        assert tokenize("") == []


# ---------------------------------------------------------------------------
# extract_title / extract_description
# ---------------------------------------------------------------------------

SAMPLE_FRONTMATTER = '''---
title: "My Test Doc"
description: "A test document for unit tests"
---

# Heading

Body text here.
'''

SAMPLE_NO_FRONTMATTER = '''# Fallback Title

Body text here.
'''


class TestExtractTitle:
    def test_from_frontmatter(self):
        assert extract_title(SAMPLE_FRONTMATTER) == "My Test Doc"

    def test_from_heading(self):
        assert extract_title(SAMPLE_NO_FRONTMATTER) == "Fallback Title"

    def test_empty(self):
        assert extract_title("no title here") == ""


class TestExtractDescription:
    def test_from_frontmatter(self):
        assert extract_description(SAMPLE_FRONTMATTER) == "A test document for unit tests"

    def test_missing(self):
        assert extract_description(SAMPLE_NO_FRONTMATTER) == ""


# ---------------------------------------------------------------------------
# strip_mdx_markup
# ---------------------------------------------------------------------------

class TestStripMdxMarkup:
    def test_removes_frontmatter(self):
        result = strip_mdx_markup(SAMPLE_FRONTMATTER)
        assert "title:" not in result

    def test_removes_links(self):
        result = strip_mdx_markup("[click here](https://example.com)")
        assert "click here" in result
        assert "https://example.com" not in result

    def test_removes_markdown_formatting(self):
        result = strip_mdx_markup("**bold** and *italic*")
        assert "bold" in result
        assert "**" not in result


# ---------------------------------------------------------------------------
# SearchIndex
# ---------------------------------------------------------------------------

def _build_index(docs: dict[str, str]) -> SearchIndex:
    """Helper to build an index from {path: content} pairs."""
    idx = SearchIndex()
    for path, content in docs.items():
        idx.add_doc(path, content)
    idx.build()
    return idx


class TestSearchIndex:
    def test_add_and_search(self):
        idx = _build_index({
            "agents/overview": '---\ntitle: "Agent Overview"\ndescription: "How agents work"\n---\nAgents are autonomous.',
            "models/deploy": '---\ntitle: "Deploy Models"\ndescription: "Model deployment"\n---\nDeploy models to endpoints.',
        })
        assert idx.total_docs == 2
        results = idx.search("agents")
        assert len(results) > 0
        assert results[0]["path"] == "agents/overview"

    def test_empty_query(self):
        idx = _build_index({"doc": "content"})
        assert idx.search("") == []

    def test_no_match(self):
        idx = _build_index({"doc": "---\ntitle: \"X\"\ndescription: \"Y\"\n---\nalpha beta"})
        results = idx.search("zzzzzznotfound")
        assert results == []

    def test_limit(self):
        docs = {f"doc{i}": f'---\ntitle: "Doc {i}"\ndescription: "test"\n---\nkeyword content' for i in range(20)}
        idx = _build_index(docs)
        results = idx.search("keyword", limit=5)
        assert len(results) <= 5

    def test_title_weighted(self):
        """Title tokens should be weighted higher than body tokens."""
        idx = _build_index({
            "title-match": '---\ntitle: "Fine Tuning Guide"\ndescription: ""\n---\nGeneral content.',
            "body-match": '---\ntitle: "General Guide"\ndescription: ""\n---\nFine tuning is covered here.',
        })
        results = idx.search("fine tuning")
        assert len(results) == 2
        assert results[0]["path"] == "title-match"

    def test_idf_computed(self):
        idx = _build_index({
            "a": "common rare",
            "b": "common other",
        })
        assert "common" in idx.idf
        assert "rare" in idx.idf
        # rare should have higher IDF than common
        assert idx.idf["rare"] > idx.idf["common"]

    def test_result_format(self):
        idx = _build_index({
            "test/doc": '---\ntitle: "Test"\ndescription: "A test doc"\n---\nBody.',
        })
        results = idx.search("test")
        assert len(results) == 1
        r = results[0]
        assert r["path"] == "test/doc"
        assert r["title"] == "Test"
        assert r["description"] == "A test doc"
        assert isinstance(r["score"], float)

    def test_load_from_directory(self, tmp_path):
        """Test loading MDX files from a directory."""
        (tmp_path / "section").mkdir()
        (tmp_path / "section" / "page.mdx").write_text(
            '---\ntitle: "Page"\ndescription: "A page"\n---\nContent here.'
        )
        (tmp_path / "other.mdx").write_text(
            '---\ntitle: "Other"\ndescription: "Another"\n---\nMore content.'
        )
        idx = SearchIndex()
        idx.load_from_directory(tmp_path)
        assert idx.total_docs == 2
        assert "section/page" in idx.docs
        assert "other" in idx.docs
