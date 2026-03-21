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
        try:
            kwargs["port"] = int(os.environ.get("MCP_PORT", "8000"))
        except ValueError as e:
            raise ValueError(f"MCP_PORT must be a valid integer, got: {os.environ.get('MCP_PORT')!r}") from e
    mcp.run(transport=transport, **kwargs)


if __name__ == "__main__":
    main()
