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
from itertools import product
from pathlib import Path

from run_docs_eval import (
    MAX_DIAGNOSTIC_EVENTS,
    MAX_DIAGNOSTIC_EVENTS_CHARS,
    MAX_STDERR_EXCERPT,
    MAX_STDOUT_EXCERPT,
    MCP_SERVERS,
    _is_search_tool,
    _source_for_tool,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval_results"
REQUIRED_ROW_FIELDS = (
    "scenario_id",
    "server",
    "model",
    "category",
    "response",
    "response_present",
    "status",
    "passed",
    "selected_source",
    "selected_source_config",
    "source_config_count",
    "observed_tools",
    "successful_tools",
    "source_validated",
    "azure_required",
    "azure_live_query_proven",
    "failure_reason",
    "event_parse_error",
    "diagnostics",
    "exit_code",
    "tool_errors",
    "response_time_seconds",
)


def validate_row_schema(result: object) -> list[str]:
    """Return schema errors without throwing so malformed rows remain diagnostic."""
    if not isinstance(result, dict):
        return ["row must be a JSON object"]

    errors = [f"missing field: {field}" for field in REQUIRED_ROW_FIELDS if field not in result]
    for field in ("scenario_id", "server", "model", "category", "response", "selected_source"):
        if field in result and not isinstance(result[field], str):
            errors.append(f"{field} must be a string")
    if "status" in result and (
        not isinstance(result["status"], str)
        or result["status"] not in {"success", "invalid", "error", "timeout"}
    ):
        errors.append("status must be success, invalid, error, or timeout")
    status = result.get("status")
    if isinstance(status, str) and status in {"invalid", "error", "timeout"} and (
        result.get("response") != "" or result.get("response_present") is not False
    ):
        errors.append("non-success rows must clear response and set response_present=false")
    if status == "success" and (
        not isinstance(result.get("response"), str)
        or not result.get("response")
        or result.get("response_present") is not True
    ):
        errors.append("success rows must contain a response and set response_present=true")
    for field in (
        "response_present",
        "passed",
        "source_validated",
        "azure_required",
        "azure_live_query_proven",
    ):
        if field in result and type(result[field]) is not bool:
            errors.append(f"{field} must be a Boolean")
    if "selected_source_config" in result and not isinstance(result["selected_source_config"], dict):
        errors.append("selected_source_config must be a JSON object")
    if "source_config_count" in result and type(result["source_config_count"]) is not int:
        errors.append("source_config_count must be an integer")
    for field in ("observed_tools", "successful_tools"):
        value = result.get(field)
        if field in result and (
            not isinstance(value, list) or not all(isinstance(tool_name, str) for tool_name in value)
        ):
            errors.append(f"{field} must be a list of strings")
    if "failure_reason" in result and result["failure_reason"] is not None and not isinstance(
        result["failure_reason"], str
    ):
        errors.append("failure_reason must be a string or null")
    if "event_parse_error" in result and result["event_parse_error"] is not None and not isinstance(
        result["event_parse_error"], str
    ):
        errors.append("event_parse_error must be a string or null")
    diagnostics = result.get("diagnostics")
    required_diagnostic_fields = {
        "events",
        "events_truncated",
        "stdout_excerpt",
        "stdout_truncated",
        "stderr_excerpt",
        "stderr_truncated",
    }
    if not isinstance(diagnostics, dict):
        errors.append("diagnostics must be a JSON object")
    elif set(diagnostics) != required_diagnostic_fields:
        errors.append("diagnostics must contain exactly the required bounded-output fields")
    else:
        events = diagnostics["events"]
        if not isinstance(events, list):
            errors.append("diagnostics.events must be a list")
        elif len(events) > MAX_DIAGNOSTIC_EVENTS:
            errors.append(f"diagnostics.events must contain at most {MAX_DIAGNOSTIC_EVENTS} entries")
        else:
            try:
                serialized_event_chars = len(json.dumps(events, ensure_ascii=True))
            except (TypeError, ValueError):
                errors.append("diagnostics.events must contain JSON-serializable values")
            else:
                if serialized_event_chars > MAX_DIAGNOSTIC_EVENTS_CHARS:
                    errors.append("diagnostics.events exceeds its total serialized size limit")
        for field in ("events_truncated", "stdout_truncated", "stderr_truncated"):
            if type(diagnostics[field]) is not bool:
                errors.append(f"diagnostics.{field} must be a Boolean")
        excerpt_limits = {
            "stdout_excerpt": MAX_STDOUT_EXCERPT + len("...[truncated]"),
            "stderr_excerpt": MAX_STDERR_EXCERPT + len("...[truncated]"),
        }
        for field, max_length in excerpt_limits.items():
            excerpt = diagnostics[field]
            if not isinstance(excerpt, str):
                errors.append(f"diagnostics.{field} must be a string")
            elif len(excerpt) > max_length:
                errors.append(f"diagnostics.{field} exceeds its maximum length")
    for field in ("exit_code", "tool_errors"):
        if field in result and type(result[field]) is not int:
            errors.append(f"{field} must be an integer")
    for field in ("turns", "tool_calls", "output_tokens"):
        if field in result and (type(result[field]) is not int or result[field] < 0):
            errors.append(f"{field} must be a non-negative integer")
    response_time = result.get("response_time_seconds")
    if "response_time_seconds" in result and (
        not isinstance(response_time, (int, float))
        or isinstance(response_time, bool)
        or response_time < 0
    ):
        errors.append("response_time_seconds must be a non-negative number")
    rubric = result.get("rubric")
    if rubric is not None:
        if not isinstance(rubric, dict):
            errors.append("rubric must be a JSON object")
        else:
            for field in ("must_mention", "quality_criteria", "expected_docs"):
                value = rubric.get(field, [])
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    errors.append(f"rubric.{field} must be a list of strings")
    return errors


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


def score_result(result: object) -> dict:
    """Score a single evaluation result."""
    schema_errors = validate_row_schema(result)
    if not isinstance(result, dict):
        result = {"raw_row": result}

    response = result.get("response", "")
    if not isinstance(response, str):
        response = ""
    rubric = result.get("rubric", {})
    if not isinstance(rubric, dict):
        rubric = {}
    status = result.get("status", "error")

    # Operational metrics captured by run_docs_eval.py's structured event-stream
    # parsing. Older raw result files won't have these -- default to None/0 so
    # aggregation can distinguish "known zero" from "not captured".
    operational = {
        "passed": result.get("passed") if type(result.get("passed")) is bool else None,
        "turns": result.get("turns") if type(result.get("turns")) is int and result.get("turns") >= 0 else None,
        "tool_calls": (
            result.get("tool_calls")
            if type(result.get("tool_calls")) is int and result.get("tool_calls") >= 0
            else None
        ),
        "tool_errors": (
            result.get("tool_errors")
            if type(result.get("tool_errors")) is int and result.get("tool_errors") >= 0
            else None
        ),
        "output_tokens": (
            result.get("output_tokens")
            if type(result.get("output_tokens")) is int and result.get("output_tokens") >= 0
            else None
        ),
        "response_time_seconds": (
            result.get("response_time_seconds")
            if isinstance(result.get("response_time_seconds"), (int, float))
            and not isinstance(result.get("response_time_seconds"), bool)
            and result.get("response_time_seconds") >= 0
            else None
        ),
    }
    if schema_errors:
        existing_failure = result.get("failure_reason")
        schema_failure = "row_schema_invalid: " + "; ".join(schema_errors)
        failure_reason = f"{existing_failure}; {schema_failure}" if existing_failure else schema_failure
        return {
            **result,
            "response": "",
            "response_present": False,
            "status": "invalid",
            "passed": False,
            "source_validated": False,
            "failure_reason": failure_reason,
            "row_valid": False,
            "scores": {
                "completeness": 0.0,
                "quality": 0.0,
                "doc_retrieval": 0.0,
                "response_length": len(response),
                "has_response": bool(response),
            },
            "operational": operational,
        }

    server = result.get("server")
    expected_server = MCP_SERVERS.get(server, {})
    expected_config = expected_server.get("config", {})
    selected_config = result.get("selected_source_config")
    observed_tools = result.get("observed_tools")
    successful_tools = result.get("successful_tools")
    response_time = result.get("response_time_seconds")
    expected_type = "local" if expected_server.get("type") == "stdio" else "http"
    source_schema_valid = (
        result.get("selected_source") == server
        and result.get("source_config_count") == 1
        and isinstance(selected_config, dict)
        and selected_config.get("name") == expected_config.get("name")
        and selected_config.get("type") == expected_type
        and selected_config.get("endpoint") == expected_config.get("url")
        and selected_config.get("command") == expected_config.get("command")
        and selected_config.get("tool_prefix") == expected_config.get("tool_prefix")
        and selected_config.get("azure_required") is result.get("azure_required")
        and isinstance(observed_tools, list)
        and bool(observed_tools)
        and isinstance(successful_tools, list)
        and bool(successful_tools)
        and set(successful_tools).issubset(observed_tools)
        and all(
            isinstance(tool_name, str) and _source_for_tool(tool_name) == expected_config.get("tool_prefix")
            for tool_name in observed_tools
        )
        and result.get("response_present") is True
        and bool(response)
        and isinstance(response_time, (int, float))
        and not isinstance(response_time, bool)
        and response_time >= 0
        and result.get("failure_reason") is None
        and result.get("event_parse_error") is None
        and result.get("exit_code") == 0
        and result.get("tool_errors") == 0
    )
    azure_evidence_valid = not result.get("azure_required") or (
        result.get("azure_live_query_proven") is True
        and isinstance(successful_tools, list)
        and any(
            _source_for_tool(tool_name) == expected_config.get("tool_prefix") and _is_search_tool(tool_name)
            for tool_name in successful_tools
        )
    )
    row_valid = (
        status == "success"
        and result.get("passed") is True
        and result.get("source_validated") is True
        and source_schema_valid
        and azure_evidence_valid
    )

    if not row_valid:
        return {
            **result,
            "response": "",
            "response_present": False,
            "row_valid": False,
            "scores": {
                "completeness": 0.0,
                "quality": 0.0,
                "doc_retrieval": 0.0,
                "response_length": len(response),
                "has_response": bool(response),
            },
            "operational": operational,
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

    return {**result, "row_valid": True, "scores": scores, "operational": operational}


def aggregate_scores(scored_results: list[dict]) -> dict:
    """Aggregate scores into server × model matrix and category breakdown."""
    # Server × Model matrix
    matrix = defaultdict(lambda: defaultdict(list))
    # Per-category breakdown
    categories = defaultdict(lambda: defaultdict(list))
    # Per-server aggregates
    server_agg = defaultdict(list)
    # Per-server operational metrics (independent of has_response, since a
    # failed/errored run is itself an operational data point)
    server_ops = defaultdict(lambda: {
        "total": 0,
        "passed": 0,
        "passed_known": 0,
        "turns": [],
        "tool_calls": [],
        "tool_errors": 0,
        "tool_errors_known": False,
        "output_tokens": [],
        "response_time_seconds": [],
        "status_counts": defaultdict(int),
        "response_present": 0,
        "response_missing": 0,
    })

    for r in scored_results:
        server = r.get("server") if isinstance(r.get("server"), str) else "<invalid-server>"
        model = r.get("model") if isinstance(r.get("model"), str) else "<invalid-model>"
        category = r.get("category") if isinstance(r.get("category"), str) else "<invalid-category>"

        ops = r.get("operational", {})
        agg = server_ops[server]
        agg["total"] += 1
        agg["status_counts"][r.get("status", "invalid")] += 1
        if r.get("response_present", bool(r.get("response"))):
            agg["response_present"] += 1
        else:
            agg["response_missing"] += 1
        if ops.get("passed") is not None:
            agg["passed_known"] += 1
            if ops["passed"]:
                agg["passed"] += 1
        if ops.get("turns") is not None:
            agg["turns"].append(ops["turns"])
        if ops.get("tool_calls") is not None:
            agg["tool_calls"].append(ops["tool_calls"])
        if ops.get("tool_errors") is not None:
            agg["tool_errors_known"] = True
            agg["tool_errors"] += ops["tool_errors"]
        if ops.get("output_tokens") is not None:
            agg["output_tokens"].append(ops["output_tokens"])
        if ops.get("response_time_seconds") is not None:
            agg["response_time_seconds"].append(ops["response_time_seconds"])

        if not r.get("row_valid"):
            continue

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

    operational_avg = {}
    for server, agg in server_ops.items():
        operational_avg[server] = {
            "total_evaluations": agg["total"],
            "pass_rate": (
                round(agg["passed"] / agg["passed_known"], 3)
                if agg["passed_known"] else None
            ),
            "passed_known": agg["passed_known"],
            "avg_turns": avg(agg["turns"]) if agg["turns"] else None,
            "avg_tool_calls": avg(agg["tool_calls"]) if agg["tool_calls"] else None,
            "total_tool_errors": agg["tool_errors"] if agg["tool_errors_known"] else None,
            "avg_output_tokens": avg(agg["output_tokens"]) if agg["output_tokens"] else None,
            "avg_response_time_seconds": (
                avg(agg["response_time_seconds"]) if agg["response_time_seconds"] else None
            ),
            "status_counts": dict(agg["status_counts"]),
            "response_counts": {
                "present": agg["response_present"],
                "missing": agg["response_missing"],
            },
        }

    return {
        "server_model_matrix": matrix_avg,
        "category_breakdown": category_avg,
        "server_averages": server_avg,
        "operational_metrics": operational_avg,
    }


def validate_required_matrix(
    scored_results: list[dict],
    scenario_ids: list[str] | None = None,
    servers: list[str] | None = None,
    models: list[str] | None = None,
    azure_required_servers: set[str] | None = None,
) -> dict:
    """Validate required scenario/server/model rows and produce complete denominators."""
    azure_required_servers = azure_required_servers or set()
    rows_by_key: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    malformed_rows: list[dict] = []
    for index, row in enumerate(scored_results):
        identity = (row.get("scenario_id"), row.get("server"), row.get("model"))
        if not all(isinstance(value, str) for value in identity):
            malformed_rows.append({
                "row": f"input-index-{index}",
                "status": "invalid",
                "failure_reason": row.get("failure_reason") or "row identity is missing or invalid",
            })
            continue
        key = identity
        rows_by_key[key].append(row)

    if scenario_ids is not None and servers is not None and models is not None:
        expected_keys = set(product(scenario_ids, servers, models))
    else:
        expected_keys = set(rows_by_key)

    status_counts = {"success": 0, "invalid": 0, "error": 0, "timeout": 0, "missing": 0}
    response_counts = {"present": 0, "missing": 0}
    invalid_rows: list[dict] = []
    duplicate_rows: list[str] = []

    for key in sorted(expected_keys):
        row_id = " / ".join(key)
        rows = rows_by_key.get(key, [])
        if not rows:
            status_counts["missing"] += 1
            invalid_rows.append({"row": row_id, "status": "missing", "failure_reason": "required row missing"})
            continue

        if len(rows) > 1:
            duplicate_rows.append(row_id)

        row = rows[0]
        if row["server"] in azure_required_servers and not (
            row.get("azure_required") is True
            and row.get("azure_live_query_proven") is True
            and any(_is_search_tool(tool_name) for tool_name in row.get("successful_tools", []))
        ):
            row["row_valid"] = False
            if not row.get("failure_reason"):
                row["failure_reason"] = "azure_required_evidence_missing"
        response_counts["present" if row.get("response_present", bool(row.get("response"))) else "missing"] += 1
        status = row.get("status", "invalid")
        outcome = status if status in {"error", "timeout"} else ("success" if row.get("row_valid") else "invalid")
        status_counts[outcome] += 1

        if not row.get("row_valid"):
            invalid_rows.append({
                "row": row_id,
                "status": outcome,
                "failure_reason": row.get("failure_reason") or "row evidence invalid",
            })

    unexpected_rows = sorted(" / ".join(key) for key in set(rows_by_key) - expected_keys)
    invalid_rows.extend(malformed_rows)
    status_counts["invalid"] += len(malformed_rows)
    allowed = not invalid_rows and not duplicate_rows and not unexpected_rows
    failure_reasons = []
    if invalid_rows:
        failure_reasons.append(f"{len(invalid_rows)} required row(s) are invalid or missing")
    if duplicate_rows:
        failure_reasons.append(f"{len(duplicate_rows)} required row(s) are duplicated")
    if unexpected_rows:
        failure_reasons.append(f"{len(unexpected_rows)} unexpected row(s) were supplied")

    return {
        "allowed": allowed,
        "failure_reasons": failure_reasons,
        "required_rows": len(expected_keys),
        "observed_rows": len(scored_results),
        "unique_observed_rows": len(rows_by_key),
        "status_counts": status_counts,
        "response_counts": response_counts,
        "invalid_rows": invalid_rows,
        "duplicate_rows": duplicate_rows,
        "unexpected_rows": unexpected_rows,
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
    parser.add_argument(
        "--required-scenarios", default=None,
        help="Scenario JSON whose IDs define the required matrix rows"
    )
    parser.add_argument(
        "--required-servers", nargs="+", default=None,
        help="Servers required for comparative publication"
    )
    parser.add_argument(
        "--required-models", nargs="+", default=None,
        help="Models required for comparative publication"
    )
    parser.add_argument(
        "--azure-required-servers", nargs="*", default=None,
        help="Required servers whose rows must prove a live Azure search"
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
    scenario_ids = None
    if args.required_scenarios:
        with open(args.required_scenarios) as f:
            scenario_ids = [scenario["id"] for scenario in json.load(f)]
    publication = validate_required_matrix(
        scored_results,
        scenario_ids=scenario_ids,
        servers=args.required_servers,
        models=args.required_models,
        azure_required_servers=set(args.azure_required_servers or []),
    )
    aggregates["denominators"] = {
        "required_rows": publication["required_rows"],
        "observed_rows": publication["observed_rows"],
        "unique_observed_rows": publication["unique_observed_rows"],
        "status_counts": publication["status_counts"],
        "response_counts": publication["response_counts"],
    }

    output_data = {
        "metadata": {
            **merged_metadata,
            "scoring_version": "1.0",
        },
        "aggregates": aggregates,
        "publication": publication,
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
    if not publication["allowed"]:
        print(
            "Comparative publication blocked: " + "; ".join(publication["failure_reasons"]),
            file=sys.stderr,
        )

    if not publication["allowed"]:
        raise SystemExit(1)

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
