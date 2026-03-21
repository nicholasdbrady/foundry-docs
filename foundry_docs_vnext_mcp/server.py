"""FastMCP server for Microsoft Foundry documentation (docs-vnext).

Thin wrapper around the shared server factory with docs-vnext config.
Serves the docs-vnext/ content set for A/B/C/D comparison testing.
"""

import os

from foundry_docs_mcp._server_factory import VNEXT_CONFIG, build_server

mcp = build_server(VNEXT_CONFIG)


def main():
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    kwargs = {}
    if transport != "stdio":
        kwargs["host"] = os.environ.get("MCP_HOST", "0.0.0.0")
        kwargs["port"] = int(os.environ.get("MCP_PORT", "8000"))
    mcp.run(transport=transport, **kwargs)


if __name__ == "__main__":
    main()
