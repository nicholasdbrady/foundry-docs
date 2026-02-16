FROM python:3.12-slim

WORKDIR /app

# Install package
COPY pyproject.toml README.md ./
COPY foundry_docs_mcp/ foundry_docs_mcp/

# Pre-built docs and navigation (baked into the image)
COPY docs/ docs/
COPY docs.json .

RUN pip install --no-cache-dir .

# stdio transport — the MCP client drives stdin/stdout
ENTRYPOINT ["foundry-docs-mcp"]
