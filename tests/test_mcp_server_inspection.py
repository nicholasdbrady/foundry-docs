"""Deterministic FastMCP in-memory client tests for both foundry-docs servers.

Uses FastMCP's standard in-memory testing pattern (`Client(server)` connected
directly to the server object, no network/process boundary) to assert real
MCP protocol facts for the primary (docs/) and vnext (docs-vnext/) servers:
server metadata, tool/resource/prompt inventories, and tool schemas.

These are deterministic protocol-level assertions, not LLM "vibe tests" --
every check calls the real MCP client methods (list_tools, list_resources,
list_resource_templates, list_prompts, get_prompt, ping) and asserts on their
structured results. See https://gofastmcp.com/development/tests for the
upstream in-memory testing pattern this follows.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, TypeVar

import pytest
from fastmcp import Client, FastMCP

from foundry_docs_mcp.server import mcp as docs_mcp
from foundry_docs_vnext_mcp.server import mcp as vnext_mcp

T = TypeVar("T")

# Tool/prompt inventories are the deterministic regression gate: if a tool,
# resource, or prompt is added/removed/renamed, these tests fail and force an
# explicit update, keeping MCP discovery state truthful for agents.
EXPECTED_TOOL_NAMES = {
    "search_docs",
    "submit_search_feedback",
    "get_doc",
    "list_sections",
    "get_section",
}

EXPECTED_PROMPT_NAMES = {
    "explain_foundry_concept",
    "build_foundry_agent",
    "compare_foundry_options",
}

# server object, resource URI prefix, expected server name/version
SERVERS: dict[str, tuple[FastMCP, str, str]] = {
    "foundry-docs": (docs_mcp, "docs://", "0.1.0"),
    "foundry-docs-vnext": (vnext_mcp, "docs://vnext/", "0.1.0"),
}


def _run(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from a synchronous pytest test function.

    Avoids requiring pytest-asyncio configuration/marks for this module.
    """
    return asyncio.run(coro)


async def _with_client(server: FastMCP, fn: Callable[[Client], Awaitable[T]]) -> T:
    async with Client(server) as client:
        return await fn(client)


@pytest.mark.parametrize("server_name", sorted(SERVERS))
class TestServerMetadata:
    """Server identity/instructions must be inspectable without calling any tool."""

    def test_server_name_and_version(self, server_name: str) -> None:
        server, _prefix, expected_version = SERVERS[server_name]

        async def check(client: Client) -> None:
            info = client.initialize_result.serverInfo
            assert info.name == server_name
            assert info.version == expected_version

        _run(_with_client(server, check))

    def test_instructions_describe_workflow(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            instructions = client.initialize_result.instructions
            assert instructions
            # Instructions must name the discovery tool so agents know where to start.
            assert "search_docs" in instructions

        _run(_with_client(server, check))

    def test_ping(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            assert await client.ping() is True

        _run(_with_client(server, check))


@pytest.mark.parametrize("server_name", sorted(SERVERS))
class TestTools:
    """Tool inventory and schemas are the deterministic MCP contract for agents."""

    def test_expected_tools_present(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            tools = await client.list_tools()
            names = {t.name for t in tools}
            assert names == EXPECTED_TOOL_NAMES

        _run(_with_client(server, check))

    def test_search_docs_schema_and_annotations(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            tools = {t.name: t for t in await client.list_tools()}
            search_docs = tools["search_docs"]
            schema = search_docs.inputSchema
            assert schema["required"] == ["query"]
            assert schema["properties"]["query"]["type"] == "string"
            assert schema["properties"]["limit"]["default"] == 10
            # Read-only vs. mutating tools must be distinguishable via annotations
            # so agents can tell discovery calls from feedback-recording calls.
            assert search_docs.annotations.readOnlyHint is True
            assert tools["submit_search_feedback"].annotations.readOnlyHint is False

        _run(_with_client(server, check))

    def test_get_doc_schema_requires_path(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            tools = {t.name: t for t in await client.list_tools()}
            schema = tools["get_doc"].inputSchema
            assert schema["required"] == ["path"]
            assert schema["properties"]["path"]["type"] == "string"

        _run(_with_client(server, check))

    def test_get_section_schema_requires_section(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            tools = {t.name: t for t in await client.list_tools()}
            schema = tools["get_section"].inputSchema
            assert schema["required"] == ["section"]

        _run(_with_client(server, check))


@pytest.mark.parametrize("server_name", sorted(SERVERS))
class TestResources:
    """Resource/resource-template discovery, scoped to this server's URI prefix."""

    def test_navigation_resource_present(self, server_name: str) -> None:
        server, prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            resources = await client.list_resources()
            uris = {str(r.uri) for r in resources}
            assert f"{prefix}navigation" in uris

        _run(_with_client(server, check))

    def test_page_resource_templates_present(self, server_name: str) -> None:
        server, prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            templates = await client.list_resource_templates()
            uri_templates = {t.uriTemplate for t in templates}
            assert f"{prefix}page/{{section}}/{{page}}" in uri_templates
            assert f"{prefix}page/{{section}}/{{subsection}}/{{page}}" in uri_templates

        _run(_with_client(server, check))


@pytest.mark.parametrize("server_name", sorted(SERVERS))
class TestPrompts:
    """Prompt inventory and a live render of one prompt template."""

    def test_expected_prompts_present(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            prompts = await client.list_prompts()
            names = {p.name for p in prompts}
            assert names == EXPECTED_PROMPT_NAMES

        _run(_with_client(server, check))

    def test_explain_foundry_concept_renders(self, server_name: str) -> None:
        server, _prefix, _version = SERVERS[server_name]

        async def check(client: Client) -> None:
            result = await client.get_prompt("explain_foundry_concept", {"concept": "RAG"})
            assert len(result.messages) == 2
            combined = " ".join(
                m.content.text for m in result.messages if hasattr(m.content, "text")
            )
            assert "RAG" in combined

        _run(_with_client(server, check))
