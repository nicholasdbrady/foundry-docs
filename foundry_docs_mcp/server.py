"""FastMCP server for Microsoft Foundry documentation (primary docs/).

Thin wrapper around the shared server factory with docs/-specific config.
"""

import os

from ._server_factory import DOCS_CONFIG, build_server

mcp = build_server(DOCS_CONFIG)


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
