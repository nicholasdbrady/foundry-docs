"""FastMCP server for Microsoft Foundry documentation (primary docs/).

Thin wrapper around the shared server factory with docs/-specific config.
"""

from ._server_factory import DOCS_CONFIG, build_server

mcp = build_server(DOCS_CONFIG)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
