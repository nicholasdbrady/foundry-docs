#!/usr/bin/env python3
"""Run documentation evaluation harness across MCP servers and models.

Evaluates documentation quality by asking identical questions to different
MCP servers through different frontier models, enabling A/B/C/D comparison.

MCP Servers:
  - microsoft-learn: Official MS Learn docs (control A)
  - mintlify-hosted: Mintlify built-in MCP at hobbyist-e43fa225.mintlify.app/mcp (control B)
  - foundry-docs: Custom FastMCP over docs/ (control C)
  - foundry-docs-vnext: Custom FastMCP over docs-vnext/ (treatment)

Models:
  - claude-sonnet-4.6
  - gpt-5.4
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_FILE = PROJECT_ROOT / "tests" / "docs_eval_scenarios.json"
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval_results"

MODELS = ["claude-sonnet-4.6", "gpt-5.4"]

# MCP server configurations
MCP_SERVERS = {
    "microsoft-learn": {
        "type": "remote",
        "description": "Microsoft Learn official docs (control A)",
        "config": {
            "name": "MicrosoftDocs",
            "url": "https://learn.microsoft.com/api/mcp",
            "tool_prefix": "MicrosoftDocs",
        },
    },
    "mintlify-hosted": {
        "type": "remote",
        "description": "Mintlify hosted MCP (control B)",
        "config": {
            "name": "mintlify",
            "url": "https://hobbyist-e43fa225.mintlify.app/mcp",
            "tool_prefix": "mintlify",
        },
    },
    "foundry-docs": {
        "type": "stdio",
        "description": "Custom FastMCP over docs/ (control C)",
        "config": {
            "name": "foundry_docs",
            "command": "foundry-docs",
            "tool_prefix": "foundry_docs",
            "supports_azure": True,
        },
    },
    "foundry-docs-vnext": {
        "type": "stdio",
        "description": "Custom FastMCP over docs-vnext/ (treatment)",
        "config": {
            "name": "foundry_docs_vnext",
            "command": "foundry-docs-vnext",
            "tool_prefix": "foundry_docs_vnext",
            "supports_azure": True,
        },
    },
}

AZURE_REQUIRED_ENV = ("AZURE_SEARCH_ENDPOINT", "AZURE_AI_PROJECT_ENDPOINT")
AZURE_PASSTHROUGH_ENV = (
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_API_KEY",
    "AZURE_SEARCH_INDEX_NAME",
    "AZURE_SEARCH_VNEXT_INDEX_NAME",
    "AZURE_AI_PROJECT_ENDPOINT",
    "AZURE_AI_PROJECT_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "AZURE_AI_MODEL_DEPLOYMENT_NAME",
)
KNOWN_TOOL_PREFIXES = tuple(
    sorted(
        (server["config"]["tool_prefix"] for server in MCP_SERVERS.values()),
        key=len,
        reverse=True,
    )
)


def load_scenarios(path: Path) -> list[dict]:
    """Load evaluation scenarios from JSON file."""
    with open(path) as f:
        return json.load(f)


def build_prompt(question: str, server_name: str) -> str:
    """Build the evaluation prompt for a given question and server."""
    return (
        f"Answer the following question about Microsoft Foundry using ONLY the "
        f"`{server_name}` documentation source configured for this evaluation row. "
        f"You must call its documentation search tool before answering. Be thorough and include "
        f"code examples where relevant.\n\n"
        f"Question: {question}\n\n"
        f"Instructions:\n"
        f"- Search the documentation to find relevant pages\n"
        f"- Read the most relevant pages\n"
        f"- Provide a comprehensive answer based on what you find\n"
        f"- Include specific file paths or page references\n"
        f"- Include code examples if the documentation contains them"
    )


def build_mcp_config(server_config: dict, require_azure: bool = False) -> tuple[dict, dict]:
    """Build one isolated MCP configuration and its non-secret row descriptor."""
    config = server_config["config"]
    source_name = config["name"]

    if server_config["type"] == "remote":
        mcp_server = {
            "type": "http",
            "url": config["url"],
            "tools": ["*"],
        }
    elif server_config["type"] == "stdio":
        mcp_server = {
            "type": "local",
            "command": config["command"],
            "args": list(config.get("args", [])),
            "tools": ["*"],
        }
    else:
        raise ValueError(f"Unsupported MCP server type: {server_config['type']}")

    azure_required = require_azure and bool(config.get("supports_azure"))
    if azure_required:
        missing = [name for name in AZURE_REQUIRED_ENV if not os.environ.get(name)]
        if missing:
            raise ValueError(f"Azure-required mode is missing environment variables: {', '.join(missing)}")
        mcp_server["env"] = {
            name: os.environ[name]
            for name in AZURE_PASSTHROUGH_ENV
            if os.environ.get(name)
        }
        mcp_server["env"]["FOUNDRY_EVAL_REQUIRE_AZURE"] = "true"

    descriptor = {
        "name": source_name,
        "type": mcp_server["type"],
        "endpoint": config.get("url"),
        "command": config.get("command"),
        "tool_prefix": config["tool_prefix"],
        "azure_required": azure_required,
    }
    return {"mcpServers": {source_name: mcp_server}}, descriptor


def _tool_matches_source(tool_name: str, tool_prefix: str) -> bool:
    normalized_tool = tool_name.casefold()
    normalized_prefix = tool_prefix.casefold()
    if normalized_tool == normalized_prefix:
        return True
    return any(
        normalized_tool.startswith(f"{normalized_prefix}{separator}")
        for separator in (".", "/", ":", "-", "_")
    )


def _source_for_tool(tool_name: str) -> str | None:
    return next(
        (prefix for prefix in KNOWN_TOOL_PREFIXES if _tool_matches_source(tool_name, prefix)),
        None,
    )


def _is_search_tool(tool_name: str) -> bool:
    normalized = tool_name.casefold().replace("-", "_").replace(".", "_").replace("/", "_").replace(":", "_")
    return "search_docs" in normalized or normalized.endswith("_search")


def parse_event_stream(stdout: str) -> dict:
    """Parse `copilot --output-format json` JSONL output into operational metrics.

    Extracts the final assistant response text plus turn count, tool-call count,
    tool-execution failures, output token usage, and session/API duration from the
    structured event stream. Malformed or incomplete event evidence is retained as
    a parse error so evaluation rows fail closed.
    """
    metrics = {
        "turns": 0,
        "tool_calls": 0,
        "tool_errors": 0,
        "output_tokens": 0,
        "premium_requests": None,
        "api_duration_ms": None,
        "session_duration_ms": None,
        "result_exit_code": None,
        "parse_error": None,
        "observed_tools": [],
        "successful_tools": [],
    }

    last_message_content = ""
    turn_ids: set[str] = set()
    parsed_any = False
    result_seen = False
    parse_errors: list[str] = []
    started_tools: dict[str, str] = {}
    completed_tool_calls: set[str] = set()
    final_response_line: int | None = None
    last_successful_tool_line: int | None = None

    for line_number, line in enumerate(stdout.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            parse_errors.append(f"line {line_number}: invalid JSON event")
            continue
        if not isinstance(event, dict):
            parse_errors.append(f"line {line_number}: event must be a JSON object")
            continue
        if result_seen:
            parse_errors.append(f"line {line_number}: event occurred after terminal result")

        parsed_any = True
        etype = event.get("type")
        data = event.get("data", {})
        if not isinstance(data, dict):
            parse_errors.append(f"line {line_number}: event data must be a JSON object")
            continue

        if etype == "assistant.turn_start":
            turn_id = data.get("turnId")
            if isinstance(turn_id, (str, int)):
                turn_ids.add(str(turn_id))
            elif turn_id is not None:
                parse_errors.append(f"line {line_number}: turn ID must be a string or integer")
        elif etype == "assistant.message":
            content = data.get("content")
            if isinstance(content, str) and content:
                last_message_content = content
                final_response_line = line_number
            elif content is not None and not isinstance(content, str):
                parse_errors.append(f"line {line_number}: assistant content must be a string")
            output_tokens = data.get("outputTokens", 0) or 0
            if type(output_tokens) is int and output_tokens >= 0:
                metrics["output_tokens"] += output_tokens
            else:
                parse_errors.append(f"line {line_number}: output token count must be a non-negative integer")
        elif etype == "tool.execution_start":
            tool_call_id = data.get("toolCallId")
            tool_name = data.get("toolName")
            if not isinstance(tool_call_id, str) or not isinstance(tool_name, str):
                parse_errors.append(f"line {line_number}: tool start missing identity")
                continue
            if tool_call_id in started_tools:
                parse_errors.append(f"line {line_number}: duplicate tool start for {tool_call_id}")
                continue
            started_tools[tool_call_id] = tool_name
            if tool_name not in metrics["observed_tools"]:
                metrics["observed_tools"].append(tool_name)
        elif etype == "tool.execution_complete":
            metrics["tool_calls"] += 1
            tool_call_id = data.get("toolCallId")
            tool_name = data.get("toolName") or started_tools.get(tool_call_id)
            if (
                not isinstance(tool_call_id, str)
                or not isinstance(tool_name, str)
                or tool_call_id not in started_tools
            ):
                parse_errors.append(f"line {line_number}: tool completion missing matching start")
            elif tool_call_id in completed_tool_calls:
                parse_errors.append(f"line {line_number}: duplicate tool completion for {tool_call_id}")
            elif tool_name != started_tools[tool_call_id]:
                parse_errors.append(
                    f"line {line_number}: tool completion name {tool_name} does not match "
                    f"start name {started_tools[tool_call_id]}"
                )
            else:
                completed_tool_calls.add(tool_call_id)
                if tool_name not in metrics["observed_tools"]:
                    metrics["observed_tools"].append(tool_name)
                if type(data.get("success")) is not bool:
                    parse_errors.append(f"line {line_number}: tool completion missing Boolean success")
                elif data["success"] is True and tool_name not in metrics["successful_tools"]:
                    metrics["successful_tools"].append(tool_name)
                    last_successful_tool_line = line_number
            if data.get("success") is False:
                metrics["tool_errors"] += 1
        elif etype == "result":
            if result_seen:
                parse_errors.append(f"line {line_number}: duplicate terminal result")
            result_seen = True
            metrics["result_exit_code"] = event.get("exitCode")
            usage = event.get("usage", {}) or {}
            if isinstance(usage, dict):
                metrics["premium_requests"] = usage.get("premiumRequests")
                metrics["api_duration_ms"] = usage.get("totalApiDurationMs")
                metrics["session_duration_ms"] = usage.get("sessionDurationMs")
            else:
                parse_errors.append(f"line {line_number}: result usage must be a JSON object")

    metrics["turns"] = len(turn_ids)

    if not parsed_any:
        parse_errors.append("no parseable JSON events found in stdout")
    if not result_seen:
        parse_errors.append("result event missing from stdout")
    elif type(metrics["result_exit_code"]) is not int:
        parse_errors.append("result event missing integer exit code")

    incomplete_calls = sorted(set(started_tools) - completed_tool_calls)
    if incomplete_calls:
        parse_errors.append(f"{len(incomplete_calls)} tool call(s) missing completion evidence")
    if (
        final_response_line is not None
        and last_successful_tool_line is not None
        and final_response_line < last_successful_tool_line
    ):
        parse_errors.append("assistant response preceded the final successful documentation tool")

    metrics["parse_error"] = "; ".join(dict.fromkeys(parse_errors)) or None

    return {"response": last_message_content, **metrics}


def validate_row_evidence(parsed: dict, tool_prefix: str, azure_required: bool) -> tuple[bool, str | None, bool]:
    """Validate selected-source and optional Azure evidence for one row."""
    if parsed["parse_error"]:
        return False, f"event_parse_failure: {parsed['parse_error']}", False
    if parsed["tool_errors"]:
        return False, f"tool_error: {parsed['tool_errors']} tool execution(s) failed", False

    observed_tools = parsed["observed_tools"]
    cross_source_tools = [name for name in observed_tools if _source_for_tool(name) != tool_prefix]
    if cross_source_tools:
        return False, f"cross_source_tool_call: {', '.join(cross_source_tools)}", False
    if not observed_tools:
        return False, "source_selection_unproven: no documentation tool calls observed", False
    if not any(_source_for_tool(name) == tool_prefix for name in parsed["successful_tools"]):
        return False, "source_selection_unproven: no selected-source tool completed successfully", False
    if not parsed["response"]:
        return False, "missing_response: no assistant response event contained content", False

    azure_live_query_proven = (
        azure_required
        and any(
            _tool_matches_source(name, tool_prefix) and _is_search_tool(name)
            for name in parsed["successful_tools"]
        )
    )
    if azure_required and not azure_live_query_proven:
        return False, "azure_live_query_unproven: selected search tool did not complete successfully", False

    return True, None, azure_live_query_proven


def run_single_eval(
    scenario: dict,
    server_name: str,
    server_config: dict,
    model: str,
    timeout: int = 120,
    require_azure: bool = False,
) -> dict:
    """Run a single evaluation: one scenario × one server × one model."""
    question = scenario["question"]
    source_name = server_config["config"]["name"]
    prompt = build_prompt(question, source_name)

    result = {
        "scenario_id": scenario["id"],
        "category": scenario["category"],
        "question": question,
        "server": server_name,
        "model": model,
        "rubric": scenario["rubric"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "selected_source": server_name,
        "selected_source_config": None,
        "source_config_count": 0,
        "observed_tools": [],
        "successful_tools": [],
        "response_present": False,
        "failure_reason": None,
        "source_validated": False,
        "azure_required": False,
        "azure_live_query_proven": False,
    }

    start_time = time.monotonic()

    try:
        mcp_config, source_descriptor = build_mcp_config(server_config, require_azure=require_azure)
        result["selected_source_config"] = source_descriptor
        result["source_config_count"] = len(mcp_config["mcpServers"])
        result["azure_required"] = source_descriptor["azure_required"]
    except ValueError as exc:
        elapsed = time.monotonic() - start_time
        result.update({
            "response": "",
            "stderr": str(exc),
            "exit_code": -1,
            "response_time_seconds": round(elapsed, 2),
            "status": "error",
            "passed": False,
            "failure_reason": f"setup_error: {exc}",
            "turns": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "output_tokens": 0,
            "premium_requests": None,
            "api_duration_ms": None,
            "session_duration_ms": None,
            "event_parse_error": None,
        })
        return result

    try:
        with tempfile.TemporaryDirectory(prefix="foundry-docs-eval-") as isolated_home:
            config_path = Path(isolated_home) / "selected-source.json"
            config_path.write_text(json.dumps(mcp_config), encoding="utf-8")
            config_path.chmod(0o600)

            cmd = [
                "copilot",
                "--model", model,
                "--prompt", prompt,
                "--output-format", "json",
                "--disable-builtin-mcps",
                "--additional-mcp-config", f"@{config_path}",
                f"--available-tools={source_name}",
                f"--allow-tool={source_name}",
                "--no-ask-user",
            ]
            process_env = os.environ.copy()
            process_env["COPILOT_HOME"] = isolated_home

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=isolated_home,
                env=process_env,
            )

        elapsed = time.monotonic() - start_time
        parsed = parse_event_stream(proc.stdout)
        response = parsed["response"]
        evidence_valid, failure_reason, azure_live_query_proven = validate_row_evidence(
            parsed,
            source_descriptor["tool_prefix"],
            source_descriptor["azure_required"],
        )
        if proc.returncode != 0:
            status = "error"
            failure_reason = f"process_exit_code: {proc.returncode}"
        elif parsed["result_exit_code"] not in (0, None):
            status = "invalid"
            failure_reason = f"event_result_exit_code: {parsed['result_exit_code']}"
        else:
            status = "success" if evidence_valid else "invalid"

        result.update({
            "response": response,
            "stderr": proc.stderr.strip() if proc.stderr else "",
            "exit_code": proc.returncode,
            "response_time_seconds": round(elapsed, 2),
            "status": status,
            "passed": status == "success",
            "response_present": bool(response),
            "failure_reason": failure_reason,
            "source_validated": evidence_valid,
            "azure_live_query_proven": azure_live_query_proven,
            "observed_tools": parsed["observed_tools"],
            "successful_tools": parsed["successful_tools"],
            "turns": parsed["turns"],
            "tool_calls": parsed["tool_calls"],
            "tool_errors": parsed["tool_errors"],
            "output_tokens": parsed["output_tokens"],
            "premium_requests": parsed["premium_requests"],
            "api_duration_ms": parsed["api_duration_ms"],
            "session_duration_ms": parsed["session_duration_ms"],
            "event_parse_error": parsed["parse_error"],
        })

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start_time
        result.update({
            "response": "",
            "stderr": f"Timed out after {timeout}s",
            "exit_code": -1,
            "response_time_seconds": round(elapsed, 2),
            "status": "timeout",
            "passed": False,
            "failure_reason": f"timeout: exceeded {timeout}s",
            "turns": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "output_tokens": 0,
            "premium_requests": None,
            "api_duration_ms": None,
            "session_duration_ms": None,
            "event_parse_error": None,
        })
    except OSError as exc:
        elapsed = time.monotonic() - start_time
        result.update({
            "response": "",
            "stderr": str(exc),
            "exit_code": -1,
            "response_time_seconds": round(elapsed, 2),
            "status": "error",
            "passed": False,
            "failure_reason": f"process_launch_error: {exc}",
            "turns": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "output_tokens": 0,
            "premium_requests": None,
            "api_duration_ms": None,
            "session_duration_ms": None,
            "event_parse_error": None,
        })

    return result


def run_evaluation(
    scenarios: list[dict],
    servers: dict | None = None,
    models: list[str] | None = None,
    timeout: int = 120,
    require_azure: bool = False,
) -> dict:
    """Run the full evaluation matrix."""
    servers = servers or MCP_SERVERS
    models = models or MODELS

    total = len(scenarios) * len(servers) * len(models)
    print(f"Running {total} evaluations: {len(scenarios)} scenarios × "
          f"{len(servers)} servers × {len(models)} models")

    results = []
    completed = 0

    for scenario in scenarios:
        for server_name, server_config in servers.items():
            for model in models:
                completed += 1
                print(f"[{completed}/{total}] {scenario['id']} × "
                      f"{server_name} × {model}...", end=" ", flush=True)

                result = run_single_eval(
                    scenario,
                    server_name,
                    server_config,
                    model,
                    timeout,
                    require_azure=require_azure,
                )
                results.append(result)

                status = result["status"]
                elapsed = result["response_time_seconds"]
                print(f"{status} ({elapsed:.1f}s)")

    run_metadata = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenarios_count": len(scenarios),
        "servers": list(servers.keys()),
        "models": models,
        "total_evaluations": total,
        "completed": completed,
    }

    return {"metadata": run_metadata, "results": results}


def compare_results(current: dict, baseline_path: str) -> int:
    """Compare current results against a baseline run.

    Returns exit code 0 for improvement/inconclusive, 1 for regression.
    """
    if not os.path.exists(baseline_path):
        print(f"Error: Baseline file not found: {baseline_path}", file=sys.stderr)
        return 2

    try:
        with open(baseline_path) as f:
            baseline = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in baseline file: {e}", file=sys.stderr)
        return 2

    def _success_rates(data: dict) -> dict[str, dict[str, float]]:
        """Compute per-scenario, per-server success rates."""
        rates: dict[str, dict[str, list[bool]]] = {}
        for r in data.get("results", []):
            scenario = r["scenario_id"]
            server = r["server"]
            rates.setdefault(scenario, {}).setdefault(server, []).append(
                r["status"] == "success"
            )
        return {
            scenario: {
                server: sum(outcomes) / len(outcomes)
                for server, outcomes in servers.items()
            }
            for scenario, servers in rates.items()
        }

    baseline_rates = _success_rates(baseline)
    current_rates = _success_rates(current)

    THRESHOLD = 0.05
    verdicts: list[dict] = []
    has_regression = False

    all_scenarios = sorted(set(baseline_rates) | set(current_rates))
    for scenario in all_scenarios:
        b_servers = baseline_rates.get(scenario, {})
        c_servers = current_rates.get(scenario, {})
        all_servers = sorted(set(b_servers) | set(c_servers))
        for server in all_servers:
            b_rate = b_servers.get(server)
            c_rate = c_servers.get(server)
            if b_rate is None or c_rate is None:
                verdict = "inconclusive"
            else:
                delta = c_rate - b_rate
                if delta > THRESHOLD:
                    verdict = "improvement"
                elif delta < -THRESHOLD:
                    verdict = "regression"
                    has_regression = True
                else:
                    verdict = "inconclusive"
            verdicts.append({
                "scenario": scenario,
                "server": server,
                "baseline": b_rate,
                "current": c_rate,
                "verdict": verdict,
            })

    # Print summary table
    print("\n" + "=" * 72)
    print("BASELINE COMPARISON")
    print("=" * 72)
    print(f"{'Scenario':<25} {'Server':<22} {'Base':>5} {'Curr':>5} {'Verdict'}")
    print("-" * 72)
    for v in verdicts:
        b_str = f"{v['baseline']:.0%}" if v["baseline"] is not None else "N/A"
        c_str = f"{v['current']:.0%}" if v["current"] is not None else "N/A"
        icon = {"improvement": "✅", "inconclusive": "➖", "regression": "❌"}[v["verdict"]]
        print(f"{v['scenario']:<25} {v['server']:<22} {b_str:>5} {c_str:>5} {icon} {v['verdict']}")
    print("=" * 72)

    if has_regression:
        print("❌ Regression detected — failing the check.")
        return 1
    print("✅ No regressions detected.")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run documentation evaluation harness"
    )
    parser.add_argument(
        "--scenarios", default=str(SCENARIOS_FILE),
        help="Path to scenarios JSON file"
    )
    parser.add_argument(
        "--output-dir", default=str(RESULTS_DIR),
        help="Directory to save results"
    )
    parser.add_argument(
        "--server", type=str, default=None,
        help="Run evals for a single server (used by matrix CI jobs)"
    )
    parser.add_argument(
        "--servers", nargs="*", default=None,
        help="Specific servers to evaluate (default: all)"
    )
    parser.add_argument(
        "--models", nargs="*", default=None,
        help="Specific models to use (default: all three)"
    )
    parser.add_argument(
        "--timeout", type=int, default=120,
        help="Timeout per evaluation in seconds"
    )
    parser.add_argument(
        "--require-azure", action="store_true",
        help="Require Azure hybrid search for Azure-capable selected sources"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would run without executing"
    )
    parser.add_argument(
        "--baseline", type=str, default=None,
        help="Path to a previous results JSON for regression comparison"
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    scenarios = load_scenarios(Path(args.scenarios))
    print(f"Loaded {len(scenarios)} scenarios from {args.scenarios}")

    servers = MCP_SERVERS
    if args.server:
        if args.server not in MCP_SERVERS:
            print(f"Error: unknown server '{args.server}'. Available: {list(MCP_SERVERS.keys())}", file=sys.stderr)
            raise SystemExit(1)
        servers = {args.server: MCP_SERVERS[args.server]}
    elif args.servers:
        servers = {k: v for k, v in MCP_SERVERS.items() if k in args.servers}

    models = args.models or MODELS

    if args.dry_run:
        total = len(scenarios) * len(servers) * len(models)
        print(f"Dry run: would execute {total} evaluations")
        print(f"  Servers: {list(servers.keys())}")
        print(f"  Models: {models}")
        print(f"  Scenarios: {[s['id'] for s in scenarios]}")
        return

    output = run_evaluation(
        scenarios,
        servers,
        models,
        args.timeout,
        require_azure=args.require_azure,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = output["metadata"]["run_id"]
    suffix = f"-{args.server}" if args.server else ""
    output_path = output_dir / f"run-{run_id}{suffix}.json"

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print(f"Total evaluations: {output['metadata']['total_evaluations']}")

    if args.baseline:
        exit_code = compare_results(output, args.baseline)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
