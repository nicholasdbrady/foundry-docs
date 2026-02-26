"""FastMCP server for Microsoft Foundry documentation.

Provides searchable documentation context for AI assistants via MCP tools,
resources, and prompts.  Built on FastMCP 3.x with composable lifespans,
tool annotations, Context logging, resource templates, and reusable prompts.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.prompts import Message
from fastmcp.server.lifespan import lifespan

from .foundry_client import FoundryProjectOpenAI
from .indexer import AzureSearchIndex, SearchIndex
from .telemetry import Telemetry, emit_feedback, instrument_search, setup_telemetry

logger = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).parent
PROJECT_ROOT = PACKAGE_DIR.parent


def _resolve_docs_dir() -> Path:
    """Find the docs directory, checking env var and common locations.

    When pip-installed, ``Path(__file__).parent.parent`` points to
    site-packages — not the project root — so we fall back to well-known
    paths (e.g. ``/app/docs`` inside the Docker image).
    """
    if env := os.environ.get("FOUNDRY_DOCS_DIR"):
        return Path(env)
    candidate = PROJECT_ROOT / "docs"
    if candidate.is_dir():
        return candidate
    # Docker image layout
    if (fallback := Path("/app/docs")).is_dir():
        return fallback
    return candidate  # return default even if missing so errors are clear


def _resolve_docs_json() -> Path:
    if env := os.environ.get("FOUNDRY_DOCS_JSON"):
        return Path(env)
    candidate = PROJECT_ROOT / "docs.json"
    if candidate.exists():
        return candidate
    if (fallback := Path("/app/docs.json")).exists():
        return fallback
    return candidate


DOCS_DIR = _resolve_docs_dir()
DOCS_JSON = _resolve_docs_json()


# ---------------------------------------------------------------------------
# Lifespan — load the search index once at startup
# ---------------------------------------------------------------------------

@lifespan
async def load_docs(server):
    """Build the search index and load navigation at server startup."""
    index = SearchIndex()
    index.load_from_directory(DOCS_DIR)

    azure_index = None
    embed_query = None
    rewrite_query = None
    foundry_client = None

    if os.environ.get("AZURE_SEARCH_ENDPOINT"):
        try:
            azure_index = AzureSearchIndex(
                endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
                index_name=os.environ.get("AZURE_SEARCH_INDEX_NAME", "foundry-docs"),
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
            logger.info("Azure AI Search hybrid mode enabled via Azure AI Foundry project endpoint")
        except Exception as exc:
            logger.warning("Failed to initialize Azure hybrid mode; using local search fallback: %s", exc)

    telemetry = setup_telemetry("foundry-docs")

    navigation = {}
    if DOCS_JSON.exists():
        navigation = json.loads(DOCS_JSON.read_text())

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


mcp = FastMCP(
    "foundry-docs",
    instructions=(
        "Microsoft Foundry documentation server with ~250 docs covering agents, "
        "models, fine-tuning, observability, guardrails, security, and more.\n\n"
        "Workflow:\n"
        "1. search_docs — find pages by keyword (returns ranked results)\n"
        "2. get_doc — read the full content of a page by its path\n"
        "3. list_sections — see every documentation section at a glance\n"
        "4. get_section — browse all pages inside one section\n\n"
        "Resource templates:\n"
        "  docs://page/{path}  — read a doc directly by URI\n"
        "  docs://navigation   — full navigation structure"
    ),
    version="0.1.0",
    lifespan=load_docs,
)


async def _log(ctx: Context, level: str, msg: str):
    """Log to MCP client when in a session, otherwise fall back to stdlib."""
    if ctx.request_context is not None:
        fn = getattr(ctx, level, ctx.info)
        await fn(msg)
    else:
        getattr(logger, level, logger.info)(msg)


# Lazy-loaded fallback for direct calls (no lifespan)
_fallback_index: SearchIndex | None = None
_fallback_nav: dict | None = None


def _get_index(ctx: Context) -> SearchIndex:
    """Get search index from lifespan context, or lazy-load as fallback."""
    lc = ctx.lifespan_context
    if "index" in lc:
        return lc["index"]
    global _fallback_index
    if _fallback_index is None:
        _fallback_index = SearchIndex()
        _fallback_index.load_from_directory(DOCS_DIR)
    return _fallback_index


def _get_nav(ctx: Context) -> dict:
    """Get navigation from lifespan context, or lazy-load as fallback."""
    lc = ctx.lifespan_context
    if "navigation" in lc:
        return lc["navigation"]
    global _fallback_nav
    if _fallback_nav is None:
        _fallback_nav = json.loads(DOCS_JSON.read_text()) if DOCS_JSON.exists() else {"navigation": {"tabs": []}}
    return _fallback_nav


def _get_azure_index(ctx: Context) -> AzureSearchIndex | None:
    return ctx.lifespan_context.get("azure_index")


def _get_embed_query(ctx: Context):
    return ctx.lifespan_context.get("embed_query")


def _get_rewrite_query(ctx: Context):
    return ctx.lifespan_context.get("rewrite_query")


def _get_telemetry(ctx: Context) -> Telemetry:
    return ctx.lifespan_context.get("telemetry") or Telemetry(enabled=False)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    tags={"search", "discovery"},
    annotations={
        "title": "Search Foundry Documentation",
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
    await _log(ctx, "info", f"Searching docs for: {query}")
    started = time.perf_counter()
    telemetry = _get_telemetry(ctx)
    backend = "local"

    azure_index = _get_azure_index(ctx)
    embed_query = _get_embed_query(ctx)
    rewrite_query = _get_rewrite_query(ctx)
    effective_query = rewrite_query(query) if callable(rewrite_query) else query

    if azure_index and embed_query:
        try:
            results = azure_index.search(query=effective_query, limit=limit, embedding_fn=embed_query)
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
        "title": "Submit Search Feedback",
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
        project_root=PROJECT_ROOT,
        user_request=user_request,
        query=query,
        result_paths=result_paths,
        expected_result=expected_result,
        proposed_solution=proposed_solution,
    )

    await _log(ctx, "info", "Recorded search feedback event")
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
        "title": "Get Documentation Page",
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

    # Exact match
    clean = path.lstrip("/").removesuffix(".mdx")
    if clean in index.docs:
        await _log(ctx, "info", f"Returning doc: {clean}")
        return index.docs[clean]["content"]

    # Fuzzy match on filename stem
    target = clean.split("/")[-1]
    for doc_path in index.docs:
        if doc_path.endswith(f"/{target}") or doc_path == target:
            await _log(ctx, "info", f"Fuzzy matched '{path}' → '{doc_path}'")
            return index.docs[doc_path]["content"]

    await _log(ctx, "warning", f"Document not found: {path}")
    return json.dumps({
        "error": f"Document not found: {path}",
        "hint": "Use search_docs or list_sections to find available docs",
    })


@mcp.tool(
    tags={"navigation", "discovery"},
    annotations={
        "title": "List Documentation Sections",
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

    for tab in nav.get("navigation", {}).get("tabs", []):
        for group in tab.get("groups", []):
            pages = group.get("pages", [])
            page_count = sum(
                len(p["pages"]) if isinstance(p, dict) and "pages" in p else 1
                for p in pages
            )
            sections.append({"name": group["group"], "page_count": page_count})

    await _log(ctx, "info", f"Returning {len(sections)} sections")
    return json.dumps(sections, indent=2)


@mcp.tool(
    tags={"navigation", "content"},
    annotations={
        "title": "Get Section Pages",
        "readOnlyHint": True,
        "openWorldHint": False,
    },
)
async def get_section(
    section: Annotated[str, "Section name (e.g. 'Agent development', 'Get started', 'Model capabilities')"],
    *,
    ctx: Context,
) -> str:
    """List all pages in a specific documentation section.

    Returns page paths and titles. Pass any path to get_doc to read the full content.
    """
    nav = _get_nav(ctx)
    index: SearchIndex = _get_index(ctx)
    section_lower = section.lower()

    for tab in nav.get("navigation", {}).get("tabs", []):
        for group in tab.get("groups", []):
            if group["group"].lower() == section_lower:
                pages = []
                for p in group.get("pages", []):
                    if isinstance(p, str):
                        doc = index.docs.get(p)
                        pages.append({"path": p, "title": doc["title"] if doc else p})
                    elif isinstance(p, dict):
                        sub_group = p.get("group", "")
                        for sp in p.get("pages", []):
                            doc = index.docs.get(sp)
                            pages.append({
                                "path": sp,
                                "title": doc["title"] if doc else sp,
                                "group": sub_group,
                            })
                await _log(ctx, "info", f"Section '{section}': {len(pages)} pages")
                return json.dumps(pages, indent=2)

    await _log(ctx, "warning", f"Section not found: {section}")
    return json.dumps({
        "error": f"Section not found: {section}",
        "hint": "Use list_sections to see available sections",
    })


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource(
    "docs://navigation",
    name="Navigation Structure",
    description="Full Mintlify navigation with all sections, groups, and page paths",
    mime_type="application/json",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def navigation_resource() -> str:
    """The complete documentation navigation structure."""
    if DOCS_JSON.exists():
        return DOCS_JSON.read_text()
    return json.dumps({"navigation": {"tabs": []}})


@mcp.resource(
    "docs://page/{section}/{page}",
    name="Documentation Page",
    description=(
        "Read a documentation page by section and page name. "
        "Example: docs://page/get-started/quickstart-create-foundry-resources"
    ),
    mime_type="text/markdown",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def page_resource(section: str, page: str) -> str:
    """Retrieve a single documentation page by section/page path."""
    mdx_file = DOCS_DIR / section / f"{page}.mdx"
    if mdx_file.exists():
        return mdx_file.read_text(encoding="utf-8", errors="replace")
    return f"Document not found: {section}/{page}. Use the get_doc tool for nested paths."


@mcp.resource(
    "docs://page/{section}/{subsection}/{page}",
    name="Documentation Page (nested)",
    description=(
        "Read a documentation page with a nested path. "
        "Example: docs://page/agents/development/overview"
    ),
    mime_type="text/markdown",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def nested_page_resource(section: str, subsection: str, page: str) -> str:
    """Retrieve a nested documentation page."""
    mdx_file = DOCS_DIR / section / subsection / f"{page}.mdx"
    if mdx_file.exists():
        return mdx_file.read_text(encoding="utf-8", errors="replace")
    return f"Document not found: {section}/{subsection}/{page}"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt(
    name="explain_foundry_concept",
    title="Explain a Foundry Concept",
    description="Generate a prompt that asks for a clear explanation of a Microsoft Foundry concept",
    tags={"explanation", "learning"},
)
def explain_concept(concept: str) -> list[Message]:
    """Ask for an explanation of a Foundry concept using the documentation."""
    return [
        Message(
            "You are a Microsoft Foundry documentation expert. "
            "Use the foundry-docs MCP tools to ground every answer in official docs.",
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
    """Create a guided prompt for building a Foundry agent."""
    tool_note = f" that uses {tools}" if tools else ""
    return [
        Message(
            "You are a Microsoft Foundry agent development expert. "
            "Use the foundry-docs MCP tools to provide accurate, up-to-date guidance.",
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
    """Create a comparison prompt for Foundry decision-making."""
    ctx_note = f" Context: {context}" if context else ""
    return [
        Message(
            "You are a Microsoft Foundry architecture advisor. "
            "Use the foundry-docs MCP tools to ground comparisons in official docs.",
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
