"""FastMCP server for Microsoft Foundry documentation.

Provides searchable documentation context for AI assistants via MCP tools,
resources, and prompts.  Built on FastMCP 3.x with composable lifespans,
tool annotations, Context logging, resource templates, and reusable prompts.
"""

import json
import logging
from pathlib import Path
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.prompts import Message
from fastmcp.server.lifespan import lifespan

from .indexer import SearchIndex

logger = logging.getLogger(__name__)

PACKAGE_DIR = Path(__file__).parent
PROJECT_ROOT = PACKAGE_DIR.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_JSON = PROJECT_ROOT / "docs.json"


# ---------------------------------------------------------------------------
# Lifespan — load the search index once at startup
# ---------------------------------------------------------------------------

@lifespan
async def load_docs(server):
    """Build the search index and load navigation at server startup."""
    index = SearchIndex()
    index.load_from_directory(DOCS_DIR)

    navigation = {}
    if DOCS_JSON.exists():
        navigation = json.loads(DOCS_JSON.read_text())

    yield {"index": index, "navigation": navigation}


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
    index: SearchIndex = _get_index(ctx)
    results = index.search(query, limit=limit)

    if not results:
        await _log(ctx, "warning", f"No results for query: {query}")
        return json.dumps({"message": "No results found", "query": query})

    await _log(ctx, "info", f"Found {len(results)} results")
    return json.dumps(results, indent=2)


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
