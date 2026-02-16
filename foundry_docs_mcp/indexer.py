"""Search indexer for Foundry docs.

Builds a TF-IDF-like search index from MDX docs for fast full-text search.
"""

import math
import re
from collections import Counter, defaultdict
from pathlib import Path


def tokenize(text: str) -> list[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric, filter short tokens."""
    text = text.lower()
    # Remove MDX/HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Remove code blocks
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    tokens = re.findall(r'[a-z0-9]+(?:[-_][a-z0-9]+)*', text)
    return [t for t in tokens if len(t) > 1]


def extract_title(content: str) -> str:
    """Extract title from front matter or first heading."""
    fm = re.match(r'^---\n.*?title:\s*"?([^"\n]+)"?\n.*?---', content, re.DOTALL)
    if fm:
        return fm.group(1).strip()
    h1 = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1:
        return h1.group(1).strip()
    return ""


def extract_description(content: str) -> str:
    """Extract description from front matter."""
    fm = re.match(r'^---\n.*?description:\s*"?([^"\n]+)"?\n.*?---', content, re.DOTALL)
    if fm:
        return fm.group(1).strip()
    return ""


def strip_mdx_markup(content: str) -> str:
    """Strip MDX/HTML markup for plain text extraction."""
    text = re.sub(r'^---\n.*?---\n', '', content, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[#*_`~]', '', text)
    return text


class SearchIndex:
    """Simple TF-IDF search index for docs."""

    def __init__(self):
        self.docs: dict[str, dict] = {}  # path → {title, description, content, tokens}
        self.idf: dict[str, float] = {}
        self.doc_freq: dict[str, int] = defaultdict(int)
        self.total_docs = 0

    def add_doc(self, path: str, content: str):
        """Add a document to the index."""
        title = extract_title(content)
        description = extract_description(content)
        plain = strip_mdx_markup(content)
        tokens = tokenize(f"{title} {title} {description} {plain}")  # title weighted 2x
        token_counts = Counter(tokens)

        self.docs[path] = {
            "title": title,
            "description": description,
            "content": content,
            "tokens": token_counts,
            "token_count": len(tokens),
        }

        for token in set(tokens):
            self.doc_freq[token] += 1

        self.total_docs += 1

    def build(self):
        """Compute IDF scores after all docs are added."""
        for token, df in self.doc_freq.items():
            self.idf[token] = math.log((self.total_docs + 1) / (df + 1)) + 1

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search for docs matching the query."""
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = {}
        for path, doc in self.docs.items():
            score = 0.0
            for qt in query_tokens:
                tf = doc["tokens"].get(qt, 0) / max(doc["token_count"], 1)
                idf = self.idf.get(qt, 0)
                score += tf * idf
            if score > 0:
                scores[path] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        results = []
        for path, score in ranked:
            doc = self.docs[path]
            results.append({
                "path": path,
                "title": doc["title"],
                "description": doc["description"],
                "score": round(score, 4),
            })
        return results

    def load_from_directory(self, docs_dir: Path):
        """Load all MDX files from a directory into the index."""
        for mdx_file in sorted(docs_dir.rglob("*.mdx")):
            rel_path = str(mdx_file.relative_to(docs_dir))
            # Remove .mdx extension for clean paths
            path = rel_path.rsplit(".mdx", 1)[0]
            content = mdx_file.read_text(encoding="utf-8", errors="replace")
            self.add_doc(path, content)
        self.build()
