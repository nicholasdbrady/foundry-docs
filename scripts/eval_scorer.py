#!/usr/bin/env python3
"""Score documentation evaluation results against rubrics.

Reads raw evaluation results and produces scored results with metrics:
- Completeness: % of must_mention items found in response
- Quality: % of quality_criteria satisfied
- Doc retrieval: whether expected docs were referenced
- Response time and tool usage stats
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval_results"


def score_completeness(response: str, must_mention: list[str]) -> float:
    """Score how many required concepts appear in the response."""
    if not must_mention:
        return 1.0
    response_lower = response.lower()
    hits = sum(1 for item in must_mention if item.lower() in response_lower)
    return hits / len(must_mention)


def score_quality(response: str, quality_criteria: list[str]) -> float:
    """Score how many quality criteria are satisfied."""
    if not quality_criteria:
        return 1.0

    criteria_checks = {
        "step-by-step instructions": bool(
            re.search(r"(step \d|1\.|first,|next,|\d\))", response, re.I)
        ),
        "runnable code example": bool(
            re.search(r"```(python|typescript|javascript|bash|shell)", response, re.I)
        ),
        "code example": bool(re.search(r"```", response)),
        "prerequisites listed": bool(
            re.search(r"(prerequisit|require|before you begin|you.ll need)", response, re.I)
        ),
        "step-by-step": bool(
            re.search(r"(step \d|1\.|first,|next,|\d\))", response, re.I)
        ),
    }

    hits = 0
    for criterion in quality_criteria:
        criterion_lower = criterion.lower()
        if criterion_lower in criteria_checks:
            hits += 1 if criteria_checks[criterion_lower] else 0
        else:
            # Fallback: check if criterion keywords appear in response
            keywords = criterion_lower.split()
            hits += 1 if any(kw in response.lower() for kw in keywords) else 0

    return hits / len(quality_criteria)


def score_doc_retrieval(response: str, expected_docs: list[str]) -> float:
    """Score whether expected documentation paths were referenced."""
    if not expected_docs:
        return 1.0
    response_lower = response.lower()
    hits = sum(
        1 for doc in expected_docs
        if doc.lower().replace("/", " ").replace("-", " ") in response_lower
        or doc.lower() in response_lower
        or doc.lower().split("/")[-1].replace("-", " ") in response_lower
    )
    return hits / len(expected_docs)


def score_result(result: dict) -> dict:
    """Score a single evaluation result."""
    response = result.get("response", "")
    rubric = result.get("rubric", {})
    status = result.get("status", "error")

    if status != "success" or not response:
        return {
            **result,
            "scores": {
                "completeness": 0.0,
                "quality": 0.0,
                "doc_retrieval": 0.0,
                "response_length": 0,
                "has_response": False,
            },
        }

    scores = {
        "completeness": score_completeness(
            response, rubric.get("must_mention", [])
        ),
        "quality": score_quality(
            response, rubric.get("quality_criteria", [])
        ),
        "doc_retrieval": score_doc_retrieval(
            response, rubric.get("expected_docs", [])
        ),
        "response_length": len(response),
        "has_response": True,
    }

    # Composite score (weighted average)
    scores["composite"] = (
        scores["completeness"] * 0.4
        + scores["quality"] * 0.3
        + scores["doc_retrieval"] * 0.3
    )

    return {**result, "scores": scores}


def aggregate_scores(scored_results: list[dict]) -> dict:
    """Aggregate scores into server × model matrix and category breakdown."""
    # Server × Model matrix
    matrix = defaultdict(lambda: defaultdict(list))
    # Per-category breakdown
    categories = defaultdict(lambda: defaultdict(list))
    # Per-server aggregates
    server_agg = defaultdict(list)

    for r in scored_results:
        if not r.get("scores", {}).get("has_response", False):
            continue

        server = r["server"]
        model = r["model"]
        category = r["category"]
        composite = r["scores"]["composite"]

        matrix[server][model].append(composite)
        categories[category][server].append(composite)
        server_agg[server].append(composite)

    # Compute averages
    def avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else 0.0

    matrix_avg = {
        server: {model: avg(scores) for model, scores in models.items()}
        for server, models in matrix.items()
    }

    category_avg = {
        cat: {server: avg(scores) for server, scores in servers.items()}
        for cat, servers in categories.items()
    }

    server_avg = {server: avg(scores) for server, scores in server_agg.items()}

    return {
        "server_model_matrix": matrix_avg,
        "category_breakdown": category_avg,
        "server_averages": server_avg,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score documentation evaluation results"
    )
    parser.add_argument(
        "input", nargs="+", help="Path(s) to raw evaluation results JSON file(s)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Path to save scored results (default: scored-{run_id}.json)"
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    all_results = []
    merged_metadata = {}

    for input_file in args.input:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"Warning: {input_path} not found, skipping", file=sys.stderr)
            continue

        with open(input_path) as f:
            data = json.load(f)

        file_meta = data.get("metadata", {})
        all_results.extend(data.get("results", []))

        # Merge metadata: keep first run_id, union servers/models, sum counts
        if not merged_metadata:
            merged_metadata = dict(file_meta)
            merged_metadata["servers"] = list(file_meta.get("servers", []))
            merged_metadata["models"] = list(file_meta.get("models", []))
        else:
            for s in file_meta.get("servers", []):
                if s not in merged_metadata["servers"]:
                    merged_metadata["servers"].append(s)
            for m in file_meta.get("models", []):
                if m not in merged_metadata["models"]:
                    merged_metadata["models"].append(m)

    if not all_results:
        print("Error: no results found in input files", file=sys.stderr)
        raise SystemExit(1)

    merged_metadata["total_evaluations"] = len(all_results)
    merged_metadata["input_files"] = len(args.input)

    print(f"Scoring {len(all_results)} evaluation results from {len(args.input)} file(s)...")

    scored_results = [score_result(r) for r in all_results]
    aggregates = aggregate_scores(scored_results)

    output_data = {
        "metadata": {
            **merged_metadata,
            "scoring_version": "1.0",
        },
        "aggregates": aggregates,
        "results": scored_results,
    }

    if args.output:
        output_path = Path(args.output)
    else:
        run_id = merged_metadata.get("run_id", "unknown")
        output_path = Path(args.input[0]).parent / f"scored-{run_id}.json"

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Scored results saved to {output_path}")

    # Print summary
    print("\n=== Server Averages ===")
    for server, avg_val in sorted(
        aggregates["server_averages"].items(), key=lambda x: -x[1]
    ):
        print(f"  {server}: {avg_val:.3f}")

    print("\n=== Server × Model Matrix ===")
    matrix = aggregates["server_model_matrix"]
    if matrix:
        models = sorted(next(iter(matrix.values())).keys())
        header = f"{'Server':<25}" + "".join(f"{m:<20}" for m in models)
        print(f"  {header}")
        for server in sorted(matrix.keys()):
            row = f"  {server:<25}" + "".join(
                f"{matrix[server].get(m, 0):<20.3f}" for m in models
            )
            print(row)


if __name__ == "__main__":
    main()
