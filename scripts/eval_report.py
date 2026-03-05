#!/usr/bin/env python3
"""Generate markdown evaluation report from scored results.

Produces a report comparing 4 MCP servers across 3 models with:
- Server × model scoreboard matrix
- Hypothesis test results (H1-H4)
- Category breakdown
- Model agreement analysis
- Regression detection vs. previous runs
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval_results"

SERVER_LABELS = {
    "microsoft-learn": "MS Learn (Control A)",
    "mintlify-hosted": "Mintlify MCP (Control B)",
    "foundry-docs": "FastMCP docs/ (Control C)",
    "foundry-docs-vnext": "FastMCP docs-vnext/ (Treatment)",
}

HYPOTHESES = {
    "H1": {
        "description": "docs-vnext (treatment) outperforms docs/ (control C)",
        "treatment": "foundry-docs-vnext",
        "control": "foundry-docs",
    },
    "H2": {
        "description": "Custom FastMCP outperforms Mintlify built-in MCP",
        "treatment": "foundry-docs-vnext",
        "control": "mintlify-hosted",
    },
    "H3": {
        "description": "Custom FastMCP outperforms Microsoft Learn",
        "treatment": "foundry-docs-vnext",
        "control": "microsoft-learn",
    },
    "H4": {
        "description": "Results are consistent across all 3 models",
        "type": "consistency",
    },
}


def generate_scoreboard(aggregates: dict) -> str:
    """Generate the server × model scoreboard table."""
    matrix = aggregates.get("server_model_matrix", {})
    if not matrix:
        return "*No data available for scoreboard.*\n"

    all_models = set()
    for models in matrix.values():
        all_models.update(models.keys())
    models = sorted(all_models)

    lines = ["| Server | " + " | ".join(models) + " | Average |"]
    lines.append("|" + "---|" * (len(models) + 2))

    server_avgs = aggregates.get("server_averages", {})
    ranked = sorted(matrix.keys(), key=lambda s: server_avgs.get(s, 0), reverse=True)

    for server in ranked:
        label = SERVER_LABELS.get(server, server)
        scores = [f"{matrix[server].get(m, 0):.3f}" for m in models]
        avg = f"{server_avgs.get(server, 0):.3f}"
        medal = ""
        if ranked.index(server) == 0:
            medal = " 🥇"
        elif ranked.index(server) == 1:
            medal = " 🥈"
        elif ranked.index(server) == 2:
            medal = " 🥉"
        lines.append(f"| {label}{medal} | " + " | ".join(scores) + f" | **{avg}** |")

    return "\n".join(lines) + "\n"


def test_hypotheses(aggregates: dict) -> str:
    """Test H1-H4 hypotheses and generate results."""
    server_avgs = aggregates.get("server_averages", {})
    matrix = aggregates.get("server_model_matrix", {})
    lines = []

    for hid, h in HYPOTHESES.items():
        if h.get("type") == "consistency":
            # H4: model consistency
            if not matrix:
                lines.append(f"### {hid}: {h['description']}\n\n*Insufficient data.*\n")
                continue

            rankings_by_model = {}
            all_models = set()
            for models in matrix.values():
                all_models.update(models.keys())

            for model in sorted(all_models):
                model_scores = {
                    s: matrix[s].get(model, 0) for s in matrix
                }
                ranking = sorted(model_scores, key=model_scores.get, reverse=True)
                rankings_by_model[model] = ranking

            # Check if all models rank servers the same
            rankings_list = list(rankings_by_model.values())
            all_agree = all(r == rankings_list[0] for r in rankings_list)

            status = "✅ SUPPORTED" if all_agree else "⚠️ MIXED"
            lines.append(f"### {hid}: {h['description']}\n")
            lines.append(f"**Result**: {status}\n")
            for model, ranking in rankings_by_model.items():
                rank_str = " > ".join(
                    SERVER_LABELS.get(s, s) for s in ranking
                )
                lines.append(f"- **{model}**: {rank_str}")
            lines.append("")
        else:
            treatment = h["treatment"]
            control = h["control"]
            t_score = server_avgs.get(treatment, 0)
            c_score = server_avgs.get(control, 0)
            diff = t_score - c_score

            if diff > 0.05:
                status = "✅ SUPPORTED"
            elif diff > 0:
                status = "⚠️ MARGINAL"
            elif diff == 0:
                status = "➖ NO DIFFERENCE"
            else:
                status = "❌ REJECTED"

            t_label = SERVER_LABELS.get(treatment, treatment)
            c_label = SERVER_LABELS.get(control, control)
            lines.append(f"### {hid}: {h['description']}\n")
            lines.append(
                f"**Result**: {status} — "
                f"{t_label} ({t_score:.3f}) vs {c_label} ({c_score:.3f}), "
                f"delta = {diff:+.3f}\n"
            )

    return "\n".join(lines) + "\n"


def generate_category_breakdown(aggregates: dict) -> str:
    """Generate per-category comparison table."""
    categories = aggregates.get("category_breakdown", {})
    if not categories:
        return "*No category data available.*\n"

    all_servers = set()
    for servers in categories.values():
        all_servers.update(servers.keys())
    servers = sorted(all_servers)

    lines = ["| Category | " + " | ".join(
        SERVER_LABELS.get(s, s)[:15] for s in servers
    ) + " |"]
    lines.append("|" + "---|" * (len(servers) + 1))

    for cat in sorted(categories.keys()):
        scores = [f"{categories[cat].get(s, 0):.3f}" for s in servers]
        lines.append(f"| {cat} | " + " | ".join(scores) + " |")

    return "\n".join(lines) + "\n"


def generate_report(scored_data: dict) -> str:
    """Generate the full markdown report."""
    metadata = scored_data.get("metadata", {})
    aggregates = scored_data.get("aggregates", {})

    timestamp = metadata.get("timestamp", datetime.now().isoformat())
    run_id = metadata.get("run_id", "unknown")
    total = metadata.get("total_evaluations", 0)

    report = f"""# 📊 Documentation Evaluation Report

**Run ID**: {run_id}
**Timestamp**: {timestamp}
**Total Evaluations**: {total}
**Servers**: {', '.join(metadata.get('servers', []))}
**Models**: {', '.join(metadata.get('models', []))}

---

## Scoreboard: Server × Model Matrix

{generate_scoreboard(aggregates)}

---

## Hypothesis Testing

{test_hypotheses(aggregates)}

---

## Category Breakdown

{generate_category_breakdown(aggregates)}

---

## Methodology

Each evaluation scenario poses a real-world Microsoft Foundry documentation question to a frontier model,
providing only one MCP server's tools. Responses are scored on:

| Metric | Weight | Description |
|--------|--------|-------------|
| Completeness | 40% | % of required concepts mentioned in response |
| Quality | 30% | Whether response includes code examples, step-by-step instructions, prerequisites |
| Doc Retrieval | 30% | Whether the model found and referenced expected documentation pages |

**Composite score** = 0.4 × completeness + 0.3 × quality + 0.3 × doc_retrieval

---

*Generated by `scripts/eval_report.py` — foundry-docs evaluation harness*
"""
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate evaluation report from scored results"
    )
    parser.add_argument("input", help="Path to scored results JSON")
    parser.add_argument(
        "--output", default=None,
        help="Output file path (default: stdout)"
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        raise SystemExit(1)

    with open(input_path) as f:
        scored_data = json.load(f)

    report = generate_report(scored_data)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"Report saved to {output_path}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
