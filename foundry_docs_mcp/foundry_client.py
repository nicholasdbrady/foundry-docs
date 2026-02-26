"""Azure AI Foundry client helpers.

Uses AIProjectClient to obtain an OpenAI-compatible client scoped to a
Foundry project endpoint, then provides helper methods for embeddings and
query rewriting via the OpenAI Responses API.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

logger = logging.getLogger(__name__)


class FoundryProjectOpenAI:
    """Wrapper around Foundry project OpenAI client for embeddings + responses."""

    def __init__(
        self,
        project_endpoint: str,
        embedding_model: str = "text-embedding-3-small",
        chat_model: str | None = None,
        api_key: str | None = None,
    ):
        self.project_endpoint = project_endpoint
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self.api_key = api_key

        self._credential: DefaultAzureCredential | None = None
        self._project_client: AIProjectClient | None = None
        self._project_openai_client: Any | None = None
        self._embedding_openai_client: OpenAI | None = None

    @staticmethod
    def _cognitiveservices_base_url_from_project_endpoint(project_endpoint: str) -> str:
        host = urlparse(project_endpoint).hostname or ""
        account_name = host.split(".services.ai.azure.com")[0]
        return f"https://{account_name}.cognitiveservices.azure.com/openai/v1/"

    def _ensure_clients(self):
        if self._project_openai_client is not None and self._embedding_openai_client is not None:
            return

        self._credential = DefaultAzureCredential()
        self._project_client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=self._credential,
        )
        self._project_openai_client = self._project_client.get_openai_client()

        if self.api_key:
            auth_value = self.api_key
        else:
            auth_value = get_bearer_token_provider(
                self._credential,
                "https://cognitiveservices.azure.com/.default",
            )

        self._embedding_openai_client = OpenAI(
            base_url=self._cognitiveservices_base_url_from_project_endpoint(self.project_endpoint),
            api_key=auth_value,
        )

    def close(self):
        for client in (
            self._project_openai_client,
            self._embedding_openai_client,
            self._project_client,
            self._credential,
        ):
            if client is None:
                continue
            close_fn = getattr(client, "close", None)
            if callable(close_fn):
                close_fn()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._ensure_clients()
        response = self._embedding_openai_client.embeddings.create(model=self.embedding_model, input=texts)
        return [row.embedding for row in response.data]

    def embed_query(self, query: str) -> list[float]:
        self._ensure_clients()
        response = self._embedding_openai_client.embeddings.create(model=self.embedding_model, input=query)
        return response.data[0].embedding

    def rewrite_query_for_search(self, query: str) -> str:
        """Rewrite user query into retrieval-optimized query using Responses API."""
        if not self.chat_model:
            return query

        self._ensure_clients()

        try:
            response = self._project_openai_client.responses.create(
                model=self.chat_model,
                instructions=(
                    "Rewrite the user search query for enterprise documentation retrieval. "
                    "Keep intent, expand key technical terms and synonyms, return one concise line only."
                ),
                input=query,
                max_output_tokens=80,
            )
            rewritten = (getattr(response, "output_text", "") or "").strip()
            return rewritten or query
        except Exception as exc:
            logger.warning("Failed to rewrite query via Responses API; using raw query: %s", exc)
            return query