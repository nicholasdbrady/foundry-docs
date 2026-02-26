"""Telemetry helpers for Foundry docs MCP server.

Emits OpenTelemetry spans/logs to Application Insights when configured,
and always appends feedback events to a local JSONL file for testbench use.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter, AzureMonitorTraceExporter
    from opentelemetry import trace
    from opentelemetry._logs import get_logger_provider, set_logger_provider
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except Exception:
    AzureMonitorLogExporter = None
    AzureMonitorTraceExporter = None
    trace = None
    get_logger_provider = None
    set_logger_provider = None
    LoggerProvider = None
    BatchLogRecordProcessor = None
    TracerProvider = None
    BatchSpanProcessor = None


class Telemetry:
    def __init__(self, enabled: bool, tracer: Any | None = None, log_emitter: Any | None = None):
        self.enabled = enabled
        self.tracer = tracer
        self.log_emitter = log_emitter


def setup_telemetry(service_name: str = "foundry-docs") -> Telemetry:
    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        return Telemetry(enabled=False)

    if not all(
        [
            AzureMonitorTraceExporter,
            AzureMonitorLogExporter,
            trace,
            set_logger_provider,
            LoggerProvider,
            BatchLogRecordProcessor,
            TracerProvider,
            BatchSpanProcessor,
        ]
    ):
        logger.warning("Application Insights configured but telemetry dependencies are unavailable")
        return Telemetry(enabled=False)

    try:
        trace_exporter = AzureMonitorTraceExporter(connection_string=connection_string)
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        tracer = trace.get_tracer(service_name)

        log_exporter = AzureMonitorLogExporter(connection_string=connection_string)
        logger_provider = LoggerProvider()
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        set_logger_provider(logger_provider)
        log_emitter = get_logger_provider().get_logger(service_name)

        return Telemetry(enabled=True, tracer=tracer, log_emitter=log_emitter)
    except Exception as exc:
        logger.warning("Failed to initialize telemetry: %s", exc)
        return Telemetry(enabled=False)


def _append_feedback_jsonl(project_root: Path, payload: dict[str, Any]):
    telemetry_dir = project_root / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    sink = telemetry_dir / "feedback.jsonl"
    with sink.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def instrument_search(
    telemetry: Telemetry,
    query: str,
    result_count: int,
    backend: str,
    latency_ms: float,
    top_paths: list[str],
):
    if not telemetry.enabled or telemetry.tracer is None:
        return

    with telemetry.tracer.start_as_current_span("foundry_docs.search") as span:
        span.set_attribute("search.query", query)
        span.set_attribute("search.result_count", result_count)
        span.set_attribute("search.backend", backend)
        span.set_attribute("search.latency_ms", latency_ms)
        span.set_attribute("search.top_paths", ",".join(top_paths[:5]))
        span.set_attribute("search.failed", result_count == 0)


def emit_feedback(
    telemetry: Telemetry,
    project_root: Path,
    *,
    user_request: str,
    query: str,
    result_paths: list[str],
    expected_result: str,
    proposed_solution: str,
):
    payload = {
        "event": "SearchFeedback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_request": user_request,
        "query": query,
        "result_paths": result_paths,
        "expected_result": expected_result,
        "proposed_solution": proposed_solution,
    }

    _append_feedback_jsonl(project_root, payload)

    if telemetry.enabled and telemetry.tracer is not None:
        try:
            with telemetry.tracer.start_as_current_span("foundry_docs.feedback") as span:
                span.set_attribute("feedback.event", payload["event"])
                span.set_attribute("feedback.user_request", payload["user_request"])
                span.set_attribute("feedback.query", payload["query"])
                span.set_attribute("feedback.expected_result", payload["expected_result"])
                span.set_attribute("feedback.proposed_solution", payload["proposed_solution"])
                span.set_attribute("feedback.result_paths", ",".join(result_paths))
        except Exception as exc:
            logger.warning("Failed to emit feedback telemetry: %s", exc)
