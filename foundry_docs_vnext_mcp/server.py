"""FastMCP server for Microsoft Foundry documentation (docs-vnext).

Thin wrapper around the shared server factory with docs-vnext config.
Serves the docs-vnext/ content set for A/B/C/D comparison testing.
"""

from foundry_docs_mcp._server_factory import VNEXT_CONFIG, build_server

mcp = build_server(VNEXT_CONFIG)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
