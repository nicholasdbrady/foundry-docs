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
  - claude-opus-4.6
  - gpt-5.3-codex
  - gemini-3-pro-preview
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_FILE = PROJECT_ROOT / "tests" / "docs_eval_scenarios.json"
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval_results"

MODELS = ["claude-opus-4.6", "gpt-5.3-codex", "gemini-3-pro-preview"]

# MCP server configurations
MCP_SERVERS = {
    "microsoft-learn": {
        "type": "remote",
        "description": "Microsoft Learn official docs (control A)",
        "config": {
            # MS Learn MCP is available as a built-in tool in Copilot CLI
            "tool_prefix": "MicrosoftDocs",
        },
    },
    "mintlify-hosted": {
        "type": "remote",
        "description": "Mintlify hosted MCP (control B)",
        "config": {
            "url": "https://hobbyist-e43fa225.mintlify.app/mcp",
            "tool_prefix": "mintlify",
        },
    },
    "foundry-docs": {
        "type": "stdio",
        "description": "Custom FastMCP over docs/ (control C)",
        "config": {
            "command": "foundry-docs",
            "tool_prefix": "foundry_docs",
        },
    },
    "foundry-docs-vnext": {
        "type": "stdio",
        "description": "Custom FastMCP over docs-vnext/ (treatment)",
        "config": {
            "command": "foundry-docs-vnext",
            "tool_prefix": "foundry_docs_vnext",
        },
    },
}


def load_scenarios(path: Path) -> list[dict]:
    """Load evaluation scenarios from JSON file."""
    with open(path) as f:
        return json.load(f)


def build_prompt(question: str, server_name: str) -> str:
    """Build the evaluation prompt for a given question and server."""
    return (
        f"Answer the following question about Microsoft Foundry using ONLY "
        f"the documentation tools available to you. Be thorough and include "
        f"code examples where relevant.\n\n"
        f"Question: {question}\n\n"
        f"Instructions:\n"
        f"- Search the documentation to find relevant pages\n"
        f"- Read the most relevant pages\n"
        f"- Provide a comprehensive answer based on what you find\n"
        f"- Include specific file paths or page references\n"
        f"- Include code examples if the documentation contains them"
    )


def run_single_eval(
    scenario: dict,
    server_name: str,
    server_config: dict,
    model: str,
    timeout: int = 120,
) -> dict:
    """Run a single evaluation: one scenario × one server × one model."""
    question = scenario["question"]
    prompt = build_prompt(question, server_name)

    result = {
        "scenario_id": scenario["id"],
        "category": scenario["category"],
        "question": question,
        "server": server_name,
        "model": model,
        "rubric": scenario["rubric"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    start_time = time.monotonic()

    try:
        cmd = [
            "copilot",
            "--model", model,
            "--prompt", prompt,
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )

        elapsed = time.monotonic() - start_time

        result.update({
            "response": proc.stdout.strip(),
            "stderr": proc.stderr.strip() if proc.stderr else "",
            "exit_code": proc.returncode,
            "response_time_seconds": round(elapsed, 2),
            "status": "success" if proc.returncode == 0 else "error",
        })

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start_time
        result.update({
            "response": "",
            "stderr": f"Timed out after {timeout}s",
            "exit_code": -1,
            "response_time_seconds": round(elapsed, 2),
            "status": "timeout",
        })
    except Exception as e:
        elapsed = time.monotonic() - start_time
        result.update({
            "response": "",
            "stderr": str(e),
            "exit_code": -1,
            "response_time_seconds": round(elapsed, 2),
            "status": "error",
        })

    return result


def run_evaluation(
    scenarios: list[dict],
    servers: dict | None = None,
    models: list[str] | None = None,
    timeout: int = 120,
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
                    scenario, server_name, server_config, model, timeout
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

    output = run_evaluation(scenarios, servers, models, args.timeout)

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
