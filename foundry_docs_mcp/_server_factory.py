"""Shared factory for building foundry-docs MCP servers.

Both the primary (docs/) and vnext (docs-vnext/) servers are structurally
identical — they differ only in configuration: directory paths, env var
names, URI prefixes, and display labels.  This module captures the shared
logic so each server module is a thin wrapper.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.prompts import Message
from fastmcp.server.lifespan import lifespan

from .foundry_client import FoundryProjectOpenAI
from .indexer import AzureSearchIndex, SearchIndex
from .telemetry import Telemetry, emit_feedback, instrument_search, setup_telemetry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ServerConfig:
    """All values that differ between the docs and docs-vnext servers."""

    name: str                          # e.g. "foundry-docs" or "foundry-docs-vnext"
    docs_dir_env: str                  # e.g. "FOUNDRY_DOCS_DIR"
    docs_json_env: str                 # e.g. "FOUNDRY_DOCS_JSON"
    default_docs_subdir: str           # e.g. "docs" or "docs-vnext"
    default_docs_json_rel: str         # e.g. "docs.json" or "docs-vnext/docs.json"
    search_index_env: str              # e.g. "AZURE_SEARCH_INDEX_NAME"
    default_index_name: str            # e.g. "foundry-docs" or "foundry-docs-vnext"
    resource_prefix: str               # e.g. "docs://" or "docs://vnext/"
    label_suffix: str                  # e.g. "" or " (vnext)"
    telemetry_service: str             # e.g. "foundry-docs" or "foundry-docs-vnext"
    docker_fallback_dir: str           # e.g. "/app/docs" or "/app/docs-vnext"
    docker_fallback_json: str          # e.g. "/app/docs.json" or "/app/docs-vnext/docs.json"


# Pre-defined configurations
DOCS_CONFIG = ServerConfig(
    name="foundry-docs",
    docs_dir_env="FOUNDRY_DOCS_DIR",
    docs_json_env="FOUNDRY_DOCS_JSON",
    default_docs_subdir="docs",
    default_docs_json_rel="docs.json",
    search_index_env="AZURE_SEARCH_INDEX_NAME",
    default_index_name="foundry-docs",
    resource_prefix="docs://",
    label_suffix="",
    telemetry_service="foundry-docs",
    docker_fallback_dir="/app/docs",
    docker_fallback_json="/app/docs.json",
)

VNEXT_CONFIG = ServerConfig(
    name="foundry-docs-vnext",
    docs_dir_env="FOUNDRY_VNEXT_DOCS_DIR",
    docs_json_env="FOUNDRY_VNEXT_DOCS_JSON",
    default_docs_subdir="docs-vnext",
    default_docs_json_rel="docs-vnext/docs.json",
    search_index_env="AZURE_SEARCH_VNEXT_INDEX_NAME",
    default_index_name="foundry-docs-vnext",
    resource_prefix="docs://vnext/",
    label_suffix=" (vnext)",
    telemetry_service="foundry-docs-vnext",
    docker_fallback_dir="/app/docs-vnext",
    docker_fallback_json="/app/docs-vnext/docs.json",
)


def _resolve_docs_dir(cfg: ServerConfig, project_root: Path) -> Path:
    """Find the docs directory, checking env var and common locations."""
    if env := os.environ.get(cfg.docs_dir_env):
        return Path(env)
    candidate = project_root / cfg.default_docs_subdir
    if candidate.is_dir():
        return candidate
    if (fallback := Path(cfg.docker_fallback_dir)).is_dir():
        return fallback
    return candidate


def _resolve_docs_json(cfg: ServerConfig, project_root: Path) -> Path:
    if env := os.environ.get(cfg.docs_json_env):
        return Path(env)
    candidate = project_root / cfg.default_docs_json_rel
    if candidate.exists():
        return candidate
    if (fallback := Path(cfg.docker_fallback_json)).exists():
        return fallback
    return candidate


def build_server(cfg: ServerConfig) -> FastMCP:
    """Build a fully configured FastMCP server for the given content set."""

    package_dir = Path(__file__).parent
    project_root = package_dir.parent
    docs_dir = _resolve_docs_dir(cfg, project_root)
    docs_json = _resolve_docs_json(cfg, project_root)

    # --- Lifespan ---

    @lifespan
    async def load_docs(server):
        index = SearchIndex()
        index.load_from_directory(docs_dir)

        azure_index = None
        embed_query = None
        rewrite_query = None
        foundry_client = None

        if os.environ.get("AZURE_SEARCH_ENDPOINT"):
            try:
                azure_index = AzureSearchIndex(
                    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
                    index_name=os.environ.get(cfg.search_index_env, cfg.default_index_name),
                    api_key=os.environ.get("AZURE_SEARCH_API_KEY"),
                )

                project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
                foundry_client = FoundryProjectOpenAI(
                    project_endpoint=project_endpoint,
                    embedding_model=os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
                    chat_model=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
                    api_key=os.environ.get("AZURE_AI_PROJECT_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY"),
                )

                embed_query = foundry_client.embed_query
                rewrite_query = foundry_client.rewrite_query_for_search
                logger.info("Azure AI Search hybrid mode enabled for %s", cfg.name)
            except Exception as exc:
                logger.warning("Failed to initialize Azure hybrid mode; using local search fallback: %s", exc)

        telemetry = setup_telemetry(cfg.telemetry_service)

        navigation = {}
        if docs_json.exists():
            navigation = json.loads(docs_json.read_text())

        try:
            yield {
                "index": index,
                "navigation": navigation,
                "azure_index": azure_index,
                "embed_query": embed_query,
                "rewrite_query": rewrite_query,
                "telemetry": telemetry,
            }
        finally:
            if foundry_client is not None:
                foundry_client.close()

    # --- MCP server instance ---

    suffix = cfg.label_suffix
    res_prefix = cfg.resource_prefix

    mcp = FastMCP(
        cfg.name,
        instructions=(
            f"Microsoft Foundry documentation server{suffix} with ~250+ docs covering agents, "
            "models, fine-tuning, observability, guardrails, security, and more.\n\n"
            "Workflow:\n"
            "1. search_docs — find pages by keyword (returns ranked results)\n"
            "2. get_doc — read the full content of a page by its path\n"
            "3. list_sections — see every documentation section at a glance\n"
            "4. get_section — browse all pages inside one section\n\n"
            "Resource templates:\n"
            f"  {res_prefix}page/{{path}}  — read a doc directly by URI\n"
            f"  {res_prefix}navigation   — full navigation structure"
        ),
        version="0.1.0",
        lifespan=load_docs,
    )

    # --- Helpers ---

    async def _log(ctx: Context, level: str, msg: str):
        if ctx.request_context is not None:
            fn = getattr(ctx, level, ctx.info)
            await fn(msg)
        else:
            getattr(logger, level, logger.info)(msg)

    _fallback_index: list[SearchIndex | None] = [None]
    _fallback_nav: list[dict | None] = [None]

    def _get_index(ctx: Context) -> SearchIndex:
        lc = ctx.lifespan_context
        if "index" in lc:
            return lc["index"]
        if _fallback_index[0] is None:
            _fallback_index[0] = SearchIndex()
            _fallback_index[0].load_from_directory(docs_dir)
        return _fallback_index[0]

    def _get_nav(ctx: Context) -> dict:
        lc = ctx.lifespan_context
        if "navigation" in lc:
            return lc["navigation"]
        if _fallback_nav[0] is None:
            _fallback_nav[0] = json.loads(docs_json.read_text()) if docs_json.exists() else {"navigation": {"tabs": []}}
        return _fallback_nav[0]

    def _get_azure_index(ctx: Context) -> AzureSearchIndex | None:
        return ctx.lifespan_context.get("azure_index")

    def _get_embed_query(ctx: Context):
        return ctx.lifespan_context.get("embed_query")

    def _get_rewrite_query(ctx: Context):
        return ctx.lifespan_context.get("rewrite_query")

    def _get_telemetry(ctx: Context) -> Telemetry:
        return ctx.lifespan_context.get("telemetry") or Telemetry(enabled=False)

    # --- Tools ---

    @mcp.tool(
        tags={"search", "discovery"},
        annotations={
            "title": f"Search Foundry Documentation{suffix}",
            "readOnlyHint": True,
            "openWorldHint": False,
        },
    )
    async def search_docs(
        query: Annotated[str, "Search query (e.g. 'deploy agent', 'fine-tuning', 'RAG', 'MCP server')"],
        limit: Annotated[int, "Maximum results to return"] = 10,
        *,
        ctx: Context,
    ) -> str:
        """Full-text search across all Microsoft Foundry documentation.

        Returns ranked results with path, title, description, and relevance score.
        Use the returned paths with get_doc to read the full page content.
        """
        await _log(ctx, "info", f"Searching {cfg.name} for: {query}")
        started = time.perf_counter()
        telemetry = _get_telemetry(ctx)
        backend = "local"

        azure_index = _get_azure_index(ctx)
        embed_query_fn = _get_embed_query(ctx)
        rewrite_query_fn = _get_rewrite_query(ctx)
        effective_query = rewrite_query_fn(query) if callable(rewrite_query_fn) else query

        if azure_index and embed_query_fn:
            try:
                results = azure_index.search(query=effective_query, limit=limit, embedding_fn=embed_query_fn)
                backend = "azure-hybrid"
            except Exception as exc:
                await _log(ctx, "warning", f"Azure search failed, falling back to local index: {exc}")
                index: SearchIndex = _get_index(ctx)
                results = index.search(query, limit=limit)
        else:
            index = _get_index(ctx)
            results = index.search(query, limit=limit)

        latency_ms = (time.perf_counter() - started) * 1000
        instrument_search(
            telemetry=telemetry,
            query=effective_query,
            result_count=len(results),
            backend=backend,
            latency_ms=latency_ms,
            top_paths=[r.get("path", "") for r in results[:5]],
        )

        if not results:
            await _log(ctx, "warning", f"No results for query: {query}")
            return json.dumps({"message": "No results found", "query": query, "backend": backend})

        await _log(ctx, "info", f"Found {len(results)} results ({backend}, {latency_ms:.1f}ms)")
        return json.dumps(results, indent=2)

    @mcp.tool(
        tags={"feedback", "evaluation"},
        annotations={
            "title": f"Submit Search Feedback{suffix}",
            "readOnlyHint": False,
            "openWorldHint": False,
        },
    )
    async def submit_search_feedback(
        user_request: Annotated[str, "Original user request"],
        query: Annotated[str, "The query attempted in search_docs"],
        result_paths: Annotated[list[str], "Paths returned by search_docs (empty if no results)"],
        expected_result: Annotated[str, "Expected result path or expected doc description"],
        proposed_solution: Annotated[str, "How the agent resolved or plans to resolve the failure"],
        *,
        ctx: Context,
    ) -> str:
        """Record failed/weak search cases for testbench generation and relevance tuning."""
        telemetry = _get_telemetry(ctx)
        emit_feedback(
            telemetry=telemetry,
            project_root=project_root,
            user_request=user_request,
            query=query,
            result_paths=result_paths,
            expected_result=expected_result,
            proposed_solution=proposed_solution,
        )

        await _log(ctx, "info", f"Recorded search feedback event{suffix}")
        return json.dumps(
            {
                "message": "Feedback recorded",
                "query": query,
                "hint": "Run scripts/build_testbench.py to convert feedback into evaluation cases",
            },
            indent=2,
        )

    @mcp.tool(
        tags={"read", "content"},
        annotations={
            "title": f"Get Documentation Page{suffix}",
            "readOnlyHint": True,
            "openWorldHint": False,
        },
    )
    async def get_doc(
        path: Annotated[str, "Document path (e.g. 'get-started/quickstart-create-foundry-resources')"],
        *,
        ctx: Context,
    ) -> str:
        """Retrieve the full content of a specific documentation page.

        Accepts exact paths or partial filenames. Returns the full MDX content.
        Paths are returned by search_docs and get_section.
        """
        index: SearchIndex = _get_index(ctx)

        clean = path.lstrip("/").removesuffix(".mdx")
        if clean in index.docs:
            await _log(ctx, "info", f"Returning doc: {clean}")
            return index.docs[clean]["content"]

        target = clean.split("/")[-1]
        for doc_path in index.docs:
            if doc_path.endswith(f"/{target}") or doc_path == target:
                await _log(ctx, "info", f"Fuzzy matched '{path}' → '{doc_path}'")
                return index.docs[doc_path]["content"]

        await _log(ctx, "warning", f"Document not found: {path}")
        raise ValueError(
            f"Document not found: {path}. "
            "Use search_docs to find pages by keyword, or list_sections to browse."
        )

    @mcp.tool(
        tags={"navigation", "discovery"},
        annotations={
            "title": f"List Documentation Sections{suffix}",
            "readOnlyHint": True,
            "openWorldHint": False,
        },
    )
    async def list_sections(*, ctx: Context) -> str:
        """List all documentation sections and their page counts.

        Returns the top-level table of contents: section names and how many
        pages each contains. Use get_section to drill into a specific section.
        """
        nav = _get_nav(ctx)
        sections = []

        def count_pages(items) -> int:
            total = 0
            for p in items:
                if isinstance(p, str):
                    total += 1
                elif isinstance(p, dict) and "pages" in p:
                    total += count_pages(p["pages"])
            return total

        for tab in nav.get("navigation", {}).get("tabs", []):
            for group in tab.get("groups", []):
                sections.append({"name": group["group"], "page_count": count_pages(group.get("pages", []))})

        await _log(ctx, "info", f"Returning {len(sections)} sections")
        return json.dumps(sections, indent=2)

    @mcp.tool(
        tags={"navigation", "content"},
        annotations={
            "title": f"Get Section Pages{suffix}",
            "readOnlyHint": True,
            "openWorldHint": False,
        },
    )
    async def get_section(
        section: Annotated[str, "Section name or keyword (e.g. 'agents', 'models', 'Get started', 'safety')"],
        *,
        ctx: Context,
    ) -> str:
        """List all pages in a specific documentation section.

        Returns page paths and titles. Pass any path to get_doc to read the full content.
        Supports partial matching: 'agents' matches 'Foundry Agent Service'.
        """
        nav = _get_nav(ctx)
        index: SearchIndex = _get_index(ctx)
        section_lower = section.lower()

        all_groups = []
        for tab in nav.get("navigation", {}).get("tabs", []):
            for group in tab.get("groups", []):
                all_groups.append(group)

        # Exact match, then substring, then word-prefix match
        matched_group = None
        for group in all_groups:
            if group["group"].lower() == section_lower:
                matched_group = group
                break
        if matched_group is None:
            for group in all_groups:
                if section_lower in group["group"].lower():
                    matched_group = group
                    break
        if matched_group is None:
            section_words = set(section_lower.split())
            for group in all_groups:
                group_words = set(group["group"].lower().split())
                # Match if any query word is a prefix of any group word (or vice versa)
                if any(
                    gw.startswith(sw) or sw.startswith(gw)
                    for sw in section_words
                    for gw in group_words
                ):
                    matched_group = group
                    break

        if matched_group is not None:
            pages = []

            def collect_pages(items, parent_group=""):
                for p in items:
                    if isinstance(p, str):
                        doc = index.docs.get(p)
                        entry = {"path": p, "title": doc["title"] if doc else p}
                        if parent_group:
                            entry["group"] = parent_group
                        pages.append(entry)
                    elif isinstance(p, dict) and "pages" in p:
                        collect_pages(p["pages"], p.get("group", parent_group))

            collect_pages(matched_group.get("pages", []))
            await _log(ctx, "info", f"Section '{matched_group['group']}': {len(pages)} pages")
            return json.dumps(pages, indent=2)

        available = [g["group"] for g in all_groups]
        await _log(ctx, "warning", f"Section not found: {section}")
        raise ValueError(
            f"Section not found: {section}. "
            f"Available sections: {', '.join(available)}"
        )

    # --- Resources ---

    @mcp.resource(
        f"{res_prefix}navigation",
        name=f"Navigation Structure{suffix}",
        description=f"Full Mintlify navigation with all sections, groups, and page paths{suffix}",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def navigation_resource() -> str:
        if docs_json.exists():
            return docs_json.read_text()
        return json.dumps({"navigation": {"tabs": []}})

    @mcp.resource(
        f"{res_prefix}page/{{section}}/{{page}}",
        name=f"Documentation Page{suffix}",
        description=(
            f"Read a documentation page by section and page name{suffix}. "
            f"Example: {res_prefix}page/get-started/quickstart-create-foundry-resources"
        ),
        mime_type="text/markdown",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def page_resource(section: str, page: str) -> str:
        mdx_file = docs_dir / section / f"{page}.mdx"
        if mdx_file.exists():
            return mdx_file.read_text(encoding="utf-8", errors="replace")
        return f"Document not found: {section}/{page}. Use the get_doc tool for nested paths."

    @mcp.resource(
        f"{res_prefix}page/{{section}}/{{subsection}}/{{page}}",
        name=f"Documentation Page ({cfg.name}, nested)",
        description=(
            f"Read a documentation page with a nested path{suffix}. "
            f"Example: {res_prefix}page/agents/development/overview"
        ),
        mime_type="text/markdown",
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    def nested_page_resource(section: str, subsection: str, page: str) -> str:
        mdx_file = docs_dir / section / subsection / f"{page}.mdx"
        if mdx_file.exists():
            return mdx_file.read_text(encoding="utf-8", errors="replace")
        return f"Document not found: {section}/{subsection}/{page}"

    # --- Prompts ---

    @mcp.prompt(
        name="explain_foundry_concept",
        title="Explain a Foundry Concept",
        description="Generate a prompt that asks for a clear explanation of a Microsoft Foundry concept",
        tags={"explanation", "learning"},
    )
    def explain_concept(concept: str) -> list[Message]:
        return [
            Message(
                "You are a Microsoft Foundry documentation expert. "
                f"Use the {cfg.name} MCP tools to ground every answer in official docs.",
                role="assistant",
            ),
            Message(
                f"Using the Microsoft Foundry documentation, explain '{concept}' clearly. "
                f"Include:\n"
                f"1. What it is and why it matters\n"
                f"2. Key features or capabilities\n"
                f"3. How to get started with it\n"
                f"4. Related concepts or next steps\n\n"
                f"Search the Foundry docs for '{concept}' to ground your answer."
            ),
        ]

    @mcp.prompt(
        name="build_foundry_agent",
        title="Build a Foundry Agent",
        description="Generate a step-by-step prompt for building a specific type of Foundry agent",
        tags={"agents", "tutorial"},
    )
    def build_agent(agent_type: str, tools: str = "") -> list[Message]:
        tool_note = f" that uses {tools}" if tools else ""
        return [
            Message(
                "You are a Microsoft Foundry agent development expert. "
                f"Use the {cfg.name} MCP tools to provide accurate, up-to-date guidance.",
                role="assistant",
            ),
            Message(
                f"Help me build a {agent_type} agent{tool_note} using Microsoft Foundry. "
                f"Walk me through:\n"
                f"1. Prerequisites and resource setup\n"
                f"2. Agent configuration and deployment\n"
                f"3. Adding tools and integrations\n"
                f"4. Testing and monitoring\n\n"
                f"Use search_docs to find relevant pages for '{agent_type}' agents."
            ),
        ]

    @mcp.prompt(
        name="compare_foundry_options",
        title="Compare Foundry Options",
        description="Generate a comparison prompt for choosing between Foundry options",
        tags={"comparison", "decision"},
    )
    def compare_options(option_a: str, option_b: str, context: str = "") -> list[Message]:
        ctx_note = f" Context: {context}" if context else ""
        return [
            Message(
                "You are a Microsoft Foundry architecture advisor. "
                f"Use the {cfg.name} MCP tools to ground comparisons in official docs.",
                role="assistant",
            ),
            Message(
                f"Compare '{option_a}' vs '{option_b}' in Microsoft Foundry.{ctx_note}\n\n"
                f"For each option, cover:\n"
                f"- When to use it\n"
                f"- Key advantages and limitations\n"
                f"- Pricing/resource implications\n"
                f"- Recommendation based on common scenarios\n\n"
                f"Search the Foundry docs for both topics."
            ),
        ]

    return mcp
