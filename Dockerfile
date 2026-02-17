FROM python:3.12-slim

WORKDIR /app

# Install package
COPY pyproject.toml README.md ./
COPY foundry_docs_mcp/ foundry_docs_mcp/

# Pre-built docs and navigation (baked into the image)
COPY docs/ docs/
COPY docs.json .

RUN pip install --no-cache-dir .

# Tell the server where the docs live (pip installs the package to
# site-packages, so Path(__file__).parent.parent won't find /app/docs).
ENV FOUNDRY_DOCS_DIR=/app/docs
ENV FOUNDRY_DOCS_JSON=/app/docs.json

# stdio transport — the MCP client drives stdin/stdout
ENTRYPOINT ["foundry-docs-mcp"]
