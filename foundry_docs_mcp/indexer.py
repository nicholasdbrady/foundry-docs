"""Search indexer for Foundry docs.

Builds a TF-IDF-like search index from MDX docs for fast full-text search.
"""

import math
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex as AzureSearchSchema,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import QueryCaptionType, QueryType, VectorizedQuery


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


class AzureSearchIndex:
    """Azure AI Search hybrid index for chunk-level semantic retrieval."""

    def __init__(
        self,
        endpoint: str,
        index_name: str = "foundry-docs",
        api_key: str | None = None,
    ):
        credential = AzureKeyCredential(api_key) if api_key else DefaultAzureCredential()
        self.endpoint = endpoint
        self.index_name = index_name
        self.index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
        self.search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

    def _schema(self) -> AzureSearchSchema:
        return AzureSearchSchema(
            name=self.index_name,
            fields=[
                SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
                SimpleField(name="doc_path", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="content_hash", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
                SearchableField(name="section_heading", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
                SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
                SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="hnsw-profile",
                ),
            ],
            vector_search=VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="hnsw-algorithm",
                        parameters=HnswParameters(metric="cosine"),
                    )
                ],
                profiles=[
                    VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algorithm")
                ],
            ),
            semantic_search=SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="foundry-semantic",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            content_fields=[
                                SemanticField(field_name="section_heading"),
                                SemanticField(field_name="content"),
                            ],
                            keywords_fields=[SemanticField(field_name="description")],
                        ),
                    )
                ]
            ),
        )

    def create_index(self, recreate: bool = False):
        if recreate:
            try:
                self.index_client.delete_index(self.index_name)
            except Exception:
                pass
        self.index_client.create_or_update_index(self._schema())

    def upload_chunks(self, chunks: list[dict], embedding_fn: Callable[[list[str]], list[list[float]]], batch_size: int = 100):
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start: start + batch_size]
            vectors = embedding_fn([item["content"] for item in batch])
            docs = []
            for item, vector in zip(batch, vectors):
                docs.append(
                    {
                        "chunk_id": item["chunk_id"],
                        "doc_path": item["doc_path"],
                        "content_hash": item.get("content_hash", ""),
                        "title": item.get("title", ""),
                        "section_heading": item.get("section_heading", ""),
                        "description": item.get("description", ""),
                        "content": item["content"],
                        "content_vector": vector,
                    }
                )
            self.search_client.upload_documents(docs)

    def get_existing_chunk_metadata(self) -> dict[str, dict]:
        """Return existing chunk metadata keyed by chunk_id."""
        rows: dict[str, dict] = {}
        page_size = 1000
        skip = 0
        while True:
            page = list(
                self.search_client.search(
                    search_text="*",
                    select=["chunk_id", "doc_path", "content_hash"],
                    top=page_size,
                    skip=skip,
                )
            )
            if not page:
                break

            for item in page:
                chunk_id = item.get("chunk_id")
                if not chunk_id:
                    continue
                rows[chunk_id] = {
                    "doc_path": item.get("doc_path", ""),
                    "content_hash": item.get("content_hash", ""),
                }

            if len(page) < page_size:
                break
            skip += page_size
        return rows

    def delete_chunks(self, chunk_ids: list[str], batch_size: int = 500):
        """Delete chunks by key from the index."""
        if not chunk_ids:
            return
        for start in range(0, len(chunk_ids), batch_size):
            batch = chunk_ids[start: start + batch_size]
            self.search_client.delete_documents([{"chunk_id": chunk_id} for chunk_id in batch])

    def search(
        self,
        query: str,
        limit: int,
        embedding_fn: Callable[[str], list[float]],
    ) -> list[dict]:
        query_vector = embedding_fn(query)
        vector_query = VectorizedQuery(vector=query_vector, fields="content_vector", k_nearest_neighbors=50)
        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="foundry-semantic",
            query_caption=QueryCaptionType.EXTRACTIVE,
            top=max(limit * 5, 20),
            select=["doc_path", "title", "description", "section_heading", "content"],
        )

        best_by_doc: dict[str, dict] = {}
        for item in results:
            doc_path = item.get("doc_path", "")
            score = float(item.get("@search.score", 0.0))
            caption = ""
            captions = item.get("@search.captions")
            if captions:
                caption = captions[0].text
            record = {
                "path": doc_path,
                "title": item.get("title", doc_path),
                "description": item.get("description", ""),
                "section_heading": item.get("section_heading", ""),
                "excerpt": caption,
                "score": round(score, 4),
            }
            if doc_path not in best_by_doc or score > best_by_doc[doc_path]["score"]:
                best_by_doc[doc_path] = record

        ranked = sorted(best_by_doc.values(), key=lambda x: x["score"], reverse=True)
        return ranked[:limit]
