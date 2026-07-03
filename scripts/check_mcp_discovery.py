#!/usr/bin/env python3
"""Report current MCP/tool discovery state across all docs-serving variants.

This is a deterministic inspection script -- no LLM is involved. It answers
"what MCP surface does an agent actually see right now?" for each variant
this repository serves documentation through, and is careful to distinguish
what was *verified live* from what could not be reached or is simply not
configured. It never fabricates a "pass" for a check it could not run.

Variants covered:
  - local-fastmcp-docs        FastMCP server over docs/ (in-memory client)
  - local-fastmcp-vnext       FastMCP server over docs-vnext/ (in-memory client)
  - hosted-mintlify           Mintlify-hosted docs site's own MCP/AI-readiness
                              endpoints (live HTTP checks, best-effort)
  - azure-backed-hybrid       Whether Azure AI Search hybrid retrieval mode is
                              configured for search_docs (env-var presence
                              only -- this does not make a live Azure call)

Usage:
    python scripts/check_mcp_discovery.py
    python scripts/check_mcp_discovery.py --output tests/eval_results/mcp_discovery.json
    python scripts/check_mcp_discovery.py --hosted-base-url https://example.mintlify.app
    python scripts/check_mcp_discovery.py --skip-hosted   # local-only, no network
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastmcp import Client

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default hosted docs-vnext site, as configured in .mcp.json for this repo.
DEFAULT_HOSTED_BASE_URL = "https://hobbyist-e43fa225.mintlify.app"

# Endpoints Mintlify documents as its agent-readiness/MCP-discovery surface.
# Source: https://www.mintlify.com/docs/ai/model-context-protocol,
#         https://www.mintlify.com/docs/ai/skillmd,
#         https://www.mintlify.com/docs/ai/llmstxt
HOSTED_ENDPOINTS = [
    "/mcp",
    "/.well-known/mcp",
    "/.well-known/mcp/server-card.json",
    "/skill.md",
    "/llms.txt",
    "/llms-full.txt",
]


async def _discover_local_server(server, expected_name: str) -> dict[str, Any]:
    """Inspect one FastMCP server in-memory. Never raises -- errors are captured."""
    try:
        async with Client(server) as client:
            info = client.initialize_result.serverInfo
            tools = await client.list_tools()
            resources = await client.list_resources()
            templates = await client.list_resource_templates()
            prompts = await client.list_prompts()
            return {
                "status": "verified",
                "server_name": info.name,
                "server_version": info.version,
                "instructions_present": bool(client.initialize_result.instructions),
                "ping_ok": await client.ping(),
                "tools": sorted(t.name for t in tools),
                "resources": sorted(str(r.uri) for r in resources),
                "resource_templates": sorted(t.uriTemplate for t in templates),
                "prompts": sorted(p.name for p in prompts),
            }
    except Exception as exc:  # noqa: BLE001 - report, don't crash the whole run
        return {
            "status": "error",
            "server_name": expected_name,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _classify_http(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "available"
    if status_code == 404:
        return "not_found"
    if status_code == 405:
        # Streamable-HTTP MCP transports only accept POST/initialize; a 405 on a
        # plain GET means the endpoint exists and is routed, just not GET-able.
        return "present_method_not_allowed"
    if status_code == 401 or status_code == 403:
        return "present_requires_auth"
    return f"http_{status_code}"


async def _check_hosted_endpoints(base_url: str, timeout_s: float) -> dict[str, Any]:
    """Best-effort live HTTP checks against a hosted Mintlify docs site.

    Every result is either a real HTTP status classification or an explicit
    'unreachable' -- this function never guesses that an endpoint is present.
    """
    results: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as http_client:
        for path in HOSTED_ENDPOINTS:
            url = base_url.rstrip("/") + path
            # The streamable-HTTP MCP transport expects this Accept header on /mcp;
            # other endpoints are plain JSON/text and must not be given it, since
            # some Mintlify edge routing 404s a JSON endpoint when it's present.
            headers = {"Accept": "application/json, text/event-stream"} if path == "/mcp" else {}
            try:
                resp = await http_client.get(url, headers=headers)
                entry: dict[str, Any] = {
                    "http_status": resp.status_code,
                    "status": _classify_http(resp.status_code),
                    "content_type": resp.headers.get("content-type", ""),
                }
                if path == "/.well-known/mcp/server-card.json" and resp.status_code == 200:
                    try:
                        card = resp.json()
                        entry["server_card_name"] = card.get("name")
                        entry["server_card_tools"] = sorted(
                            t.get("name", "") for t in card.get("tools", [])
                        )
                    except (ValueError, json.JSONDecodeError):
                        entry["note"] = "200 response was not valid JSON"
                results[path] = entry
            except httpx.RequestError as exc:
                results[path] = {
                    "status": "unreachable",
                    "note": f"{type(exc).__name__}: network unreachable in this environment",
                }
    return results


def _azure_hybrid_config_state() -> dict[str, Any]:
    """Report whether Azure AI Search hybrid mode is *configured*.

    This intentionally checks environment variables only. It does not attempt
    a live Azure Search/OpenAI call, so it cannot claim the hybrid path is
    verified working -- only that credentials/endpoints are present.
    """
    endpoint_configured = bool(os.environ.get("AZURE_SEARCH_ENDPOINT"))
    project_configured = bool(os.environ.get("AZURE_AI_PROJECT_ENDPOINT"))
    return {
        "status": "configured" if (endpoint_configured and project_configured) else "not_configured",
        "azure_search_endpoint_set": endpoint_configured,
        "azure_ai_project_endpoint_set": project_configured,
        "index_name_docs": os.environ.get("AZURE_SEARCH_INDEX_NAME", "foundry-docs (default)"),
        "index_name_vnext": os.environ.get("AZURE_SEARCH_VNEXT_INDEX_NAME", "foundry-docs-vnext (default)"),
        "note": (
            "Presence of endpoint env vars only -- this does not verify a live Azure "
            "call succeeds. Run scripts/run_testbench.py against a configured environment "
            "for a verified-live check."
        ),
    }


async def run_discovery(hosted_base_url: str | None, timeout_s: float) -> dict[str, Any]:
    from foundry_docs_mcp.server import mcp as docs_mcp
    from foundry_docs_vnext_mcp.server import mcp as vnext_mcp

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "local_fastmcp": {
            "foundry-docs": await _discover_local_server(docs_mcp, "foundry-docs"),
            "foundry-docs-vnext": await _discover_local_server(vnext_mcp, "foundry-docs-vnext"),
        },
        "azure_backed_hybrid": _azure_hybrid_config_state(),
    }

    if hosted_base_url:
        report["hosted_mintlify"] = {
            "base_url": hosted_base_url,
            "endpoints": await _check_hosted_endpoints(hosted_base_url, timeout_s),
            "note": (
                "'mint score <url>' (Mintlify agent-readiness scoring) requires an "
                "authenticated Mintlify account (`mint login`) and is not run here -- "
                "report as not configured/unavailable rather than fabricating a score."
            ),
        }
    else:
        report["hosted_mintlify"] = {"status": "skipped", "note": "hosted checks disabled via --skip-hosted"}

    return report


def render_summary(report: dict[str, Any]) -> str:
    """Render a short human-readable summary distinguishing each variant."""
    lines = ["# MCP & Tool Discovery State", "", f"_Generated: {report['generated_at']}_", ""]

    lines.append("## Local FastMCP servers (in-memory, verified live)")
    for name, data in report["local_fastmcp"].items():
        if data["status"] == "verified":
            lines.append(
                f"- **{name}** v{data['server_version']}: {len(data['tools'])} tools, "
                f"{len(data['resources'])} resources, {len(data['resource_templates'])} resource templates, "
                f"{len(data['prompts'])} prompts. Tools: {', '.join(data['tools'])}"
            )
        else:
            lines.append(f"- **{name}**: ERROR -- {data.get('error', 'unknown error')}")

    lines.append("")
    lines.append("## Hosted Mintlify docs site")
    hosted = report["hosted_mintlify"]
    if hosted.get("status") == "skipped":
        lines.append(f"- Skipped: {hosted['note']}")
    else:
        lines.append(f"- Base URL: {hosted['base_url']}")
        for path, entry in hosted["endpoints"].items():
            extra = ""
            if "server_card_tools" in entry:
                extra = f" (tools: {', '.join(entry['server_card_tools'])})"
            lines.append(f"  - `{path}` -> {entry['status']}{extra}")
        lines.append(f"- {hosted['note']}")

    lines.append("")
    lines.append("## Azure-backed hybrid search")
    azure = report["azure_backed_hybrid"]
    lines.append(f"- Status: **{azure['status']}**")
    lines.append(f"- {azure['note']}")

    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", default=None, help="Write JSON report to this path")
    parser.add_argument("--summary-output", default=None, help="Write markdown summary to this path")
    parser.add_argument(
        "--hosted-base-url", default=DEFAULT_HOSTED_BASE_URL,
        help="Base URL of the hosted Mintlify docs site to check (default: repo's configured site)",
    )
    parser.add_argument("--skip-hosted", action="store_true", help="Skip live hosted-site HTTP checks")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout for hosted checks")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    hosted_base_url = None if args.skip_hosted else args.hosted_base_url

    report = asyncio.run(run_discovery(hosted_base_url, args.timeout))
    summary = render_summary(report)

    print(summary)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"JSON report saved to {output_path}", file=sys.stderr)

    if args.summary_output:
        summary_path = Path(args.summary_output)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
        print(f"Summary saved to {summary_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
