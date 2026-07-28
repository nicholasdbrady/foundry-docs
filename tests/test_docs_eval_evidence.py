"""Process-boundary and publication-gate tests for documentation evaluation evidence."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastmcp import Client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from eval_report import generate_report  # noqa: E402
from eval_scorer import aggregate_scores, score_result, validate_required_matrix, validate_row_schema  # noqa: E402
from foundry_docs_mcp._server_factory import DOCS_CONFIG, build_server  # noqa: E402
from run_docs_eval import (  # noqa: E402
    MCP_SERVERS,
    _sanitize_text,
    build_mcp_config,
    parse_event_stream,
    run_single_eval,
    serialized_diagnostic_events_size,
)


SCENARIO = {
    "id": "scenario-1",
    "category": "getting-started",
    "question": "How do I create an agent?",
    "rubric": {
        "must_mention": ["agent"],
        "quality_criteria": [],
        "expected_docs": [],
    },
}


def _event_stream(
    tool_name: str = "foundry_docs-search_docs",
    *,
    tool_success: bool = True,
    response: str | None = "Use an agent.",
) -> str:
    events = [
        {
            "type": "assistant.turn_start",
            "data": {"turnId": "turn-1"},
        },
        {
            "type": "tool.execution_start",
            "data": {"toolCallId": "call-1", "toolName": tool_name, "arguments": {"query": "agent"}},
        },
        {
            "type": "tool.execution_complete",
            "data": {"toolCallId": "call-1", "success": tool_success, "result": {"content": "result"}},
        },
    ]
    if response is not None:
        events.append({"type": "assistant.message", "data": {"content": response, "outputTokens": 12}})
    events.append({"type": "result", "exitCode": 0, "usage": {"sessionDurationMs": 25}})
    return "\n".join(json.dumps(event) for event in events)


def _raw_row(
    *,
    scenario_id: str = "scenario-1",
    server: str = "foundry-docs",
    model: str = "model-1",
    status: str = "success",
    response: str = "Use an agent.",
    failure_reason: str | None = None,
) -> dict:
    valid = status == "success"
    config = MCP_SERVERS[server]["config"]
    return {
        "scenario_id": scenario_id,
        "server": server,
        "model": model,
        "category": "getting-started",
        "response": response,
        "response_present": bool(response),
        "status": status,
        "passed": valid,
        "selected_source": server,
        "selected_source_config": {
            "name": config["name"],
            "type": "local" if MCP_SERVERS[server]["type"] == "stdio" else "http",
            "endpoint": config.get("url"),
            "command": config.get("command"),
            "tool_prefix": config["tool_prefix"],
            "azure_required": False,
        },
        "source_config_count": 1,
        "observed_tools": [f"{config['tool_prefix']}-search_docs"],
        "successful_tools": [f"{config['tool_prefix']}-search_docs"],
        "source_validated": valid,
        "azure_required": False,
        "azure_live_query_proven": False,
        "failure_reason": failure_reason,
        "event_parse_error": None,
        "diagnostics": {
            "events": [],
            "events_truncated": False,
            "stdout_excerpt": "",
            "stdout_truncated": False,
            "stderr_excerpt": "",
            "stderr_truncated": False,
        },
        "exit_code": 0 if valid else -1,
        "rubric": SCENARIO["rubric"],
        "turns": 1,
        "tool_calls": 1,
        "tool_errors": 0,
        "output_tokens": 12,
        "response_time_seconds": 0.1,
    }


def test_build_mcp_config_contains_exactly_one_selected_source(monkeypatch):
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://search.example")
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://project.example")
    monkeypatch.setenv("AZURE_SEARCH_API_KEY", "secret")

    payload, descriptor = build_mcp_config(MCP_SERVERS["foundry-docs"], require_azure=True)

    assert list(payload["mcpServers"]) == ["foundry_docs"]
    assert payload["mcpServers"]["foundry_docs"]["command"] == "foundry-docs"
    assert payload["mcpServers"]["foundry_docs"]["env"]["FOUNDRY_EVAL_REQUIRE_AZURE"] == "true"
    assert descriptor == {
        "name": "foundry_docs",
        "type": "local",
        "endpoint": None,
        "command": "foundry-docs",
        "tool_prefix": "foundry_docs",
        "azure_required": True,
    }


def test_azure_required_config_fails_fast_with_setup_diagnostics(monkeypatch):
    monkeypatch.delenv("AZURE_SEARCH_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
        require_azure=True,
    )

    assert result["status"] == "error"
    assert result["passed"] is False
    assert result["failure_reason"].startswith("setup_error:")
    assert "AZURE_SEARCH_ENDPOINT" in result["failure_reason"]
    assert result["response_present"] is False


def test_mcp_server_refuses_local_fallback_in_azure_required_mode(monkeypatch):
    monkeypatch.setenv("FOUNDRY_EVAL_REQUIRE_AZURE", "true")
    monkeypatch.delenv("AZURE_SEARCH_ENDPOINT", raising=False)
    server = build_server(DOCS_CONFIG)

    async def connect() -> None:
        async with Client(server):
            pass

    with pytest.raises(RuntimeError, match="AZURE_SEARCH_ENDPOINT"):
        asyncio.run(connect())


def test_run_single_eval_passes_only_selected_config_across_process_boundary(monkeypatch):
    captured: dict = {}

    def fake_run(cmd, **kwargs):
        config_arg = cmd[cmd.index("--additional-mcp-config") + 1]
        config_path = Path(config_arg.removeprefix("@"))
        captured["config"] = json.loads(config_path.read_text(encoding="utf-8"))
        captured["cmd"] = cmd
        captured["cwd"] = kwargs["cwd"]
        captured["copilot_home"] = kwargs["env"]["COPILOT_HOME"]
        return subprocess.CompletedProcess(cmd, 0, stdout=_event_stream(), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert list(captured["config"]["mcpServers"]) == ["foundry_docs"]
    assert "--disable-builtin-mcps" in captured["cmd"]
    assert "--available-tools=foundry_docs" in captured["cmd"]
    assert "--allow-tool=foundry_docs" in captured["cmd"]
    assert captured["cwd"] == captured["copilot_home"]
    assert result["selected_source"] == "foundry-docs"
    assert result["source_config_count"] == 1
    assert result["observed_tools"] == ["foundry_docs-search_docs"]
    assert result["successful_tools"] == ["foundry_docs-search_docs"]
    assert result["source_validated"] is True
    assert result["response_present"] is True
    assert result["status"] == "success"
    assert result["failure_reason"] is None


@pytest.mark.parametrize(
    ("stdout", "failure_prefix"),
    [
        (_event_stream(tool_name="mintlify-search"), "cross_source_tool_call:"),
        (_event_stream(tool_name="foundry_docs_vnext-search_docs"), "cross_source_tool_call:"),
        (_event_stream(tool_success=False), "tool_error:"),
        (_event_stream(response=None), "missing_response:"),
        ("not-json", "event_parse_failure:"),
    ],
)
def test_invalid_event_evidence_fails_closed(monkeypatch, stdout, failure_prefix):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "invalid"
    assert result["passed"] is False
    assert result["failure_reason"].startswith(failure_prefix)


def test_azure_required_row_needs_successful_selected_search(monkeypatch):
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://search.example")
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://project.example")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=_event_stream(tool_name="foundry_docs-get_doc"),
            stderr="",
        ),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
        require_azure=True,
    )

    assert result["azure_required"] is True
    assert result["azure_live_query_proven"] is False
    assert result["status"] == "invalid"
    assert result["failure_reason"].startswith("azure_live_query_unproven:")


def test_timeout_is_preserved_as_invalid_row_diagnostics(monkeypatch):
    def time_out(cmd, **kwargs):
        partial_events = "\n".join([
            json.dumps({
                "type": "session.mcp_server_status_changed",
                "data": {
                    "serverName": "foundry_docs",
                    "status": "failed",
                    "error": "API_KEY=super-secret at C:\\Users\\someone\\repo",
                },
            }),
            json.dumps({
                "type": "tool.execution_start",
                "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"},
            }),
        ])
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=kwargs["timeout"],
            output=partial_events.encode(),
            stderr=b"Bearer abc.def.ghi from C:\\Users\\someone\\repo",
        )

    monkeypatch.setattr(subprocess, "run", time_out)

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
        timeout=3,
    )

    assert result["status"] == "timeout"
    assert result["response_present"] is False
    assert result["failure_reason"] == "timeout: exceeded 3s"
    assert result["response_time_seconds"] >= 0
    assert result["observed_tools"] == ["foundry_docs-search_docs"]
    assert result["diagnostics"]["events"][0]["event_type"] == "session.mcp_server_status_changed"
    assert "API_KEY=[REDACTED]" in result["diagnostics"]["events"][0]["data"]["error"]
    assert "<PATH>" in result["diagnostics"]["events"][0]["data"]["error"]
    assert "super-secret" not in result["diagnostics"]["stdout_excerpt"]
    assert "Bearer [REDACTED]" in result["diagnostics"]["stderr_excerpt"]
    assert result["response"] == ""

    scored = score_result(result)
    publication = validate_required_matrix(
        [scored],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
    )
    assert publication["allowed"] is False


def test_process_launch_error_sanitizes_every_persisted_field(monkeypatch):
    leaked = (
        "failed to launch with GITHUB_TOKEN=github_pat_launchsecret "
        "Authorization: Basic dXNlcjpwYXNz\n"
        "failed at C:/Users/Jane Doe/private/copilot.exe"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: (_ for _ in ()).throw(OSError(leaked)),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    persisted = json.dumps({
        "stderr": result["stderr"],
        "failure_reason": result["failure_reason"],
        "diagnostics": result["diagnostics"],
    })
    for secret in ("github_pat_launchsecret", "dXNlcjpwYXNz", "Jane Doe", "copilot.exe"):
        assert secret not in persisted
    assert "GITHUB_TOKEN=[REDACTED]" in result["stderr"]
    assert "Authorization: [REDACTED]" in result["stderr"]
    assert "<PATH>" in result["stderr"]
    assert result["failure_reason"] == f"process_launch_error: {result['stderr']}"
    assert result["diagnostics"]["stderr_excerpt"] == result["stderr"]


def test_exact_process_launch_error_leaks_neither_token_nor_path_in_raw_or_scored_row(monkeypatch):
    leaked = r"token=LEAKME at C:\Users\Alice\private"
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: (_ for _ in ()).throw(OSError(leaked)),
    )

    raw_row = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )
    scored_row = score_result(raw_row)

    for row in (raw_row, scored_row):
        persisted = json.dumps(row)
        assert "LEAKME" not in persisted
        assert "Alice" not in persisted
        assert "private" not in persisted
        assert "token=[REDACTED]" in persisted
        assert "<PATH>" in persisted


def test_mcp_initialization_failure_preserves_sanitized_lifecycle_diagnostics(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_server_status_changed",
            "data": {
                "serverName": "foundry_docs",
                "status": "failed",
                "error": "token=top-secret failed in C:\\Users\\someone\\repo",
                "authorization": "Bearer should-never-survive",
            },
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "invalid"
    assert result["failure_reason"].startswith("mcp_initialization_failure:")
    assert "source_selection_unproven" not in result["failure_reason"]
    diagnostic = result["diagnostics"]["events"][0]
    assert diagnostic["event_type"] == "session.mcp_server_status_changed"
    assert diagnostic["data"]["status"] == "failed"
    assert "token=[REDACTED]" in diagnostic["data"]["error"]
    assert "<PATH>" in diagnostic["data"]["error"]
    assert diagnostic["data"]["authorization"] == "[REDACTED]"


def test_real_mcp_servers_loaded_schema_preserves_statuses_and_selected_failure(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_servers_loaded",
            "ephemeral": True,
            "data": {
                "servers": [
                    {
                        "name": "foundry_docs",
                        "status": "failed",
                        "error": "Authorization: Digest username=alice response=secret",
                        "source": "user",
                        "transport": "stdio",
                    },
                    {
                        "name": "disabled_builtin",
                        "status": "disabled",
                        "source": "builtin",
                        "transport": "memory",
                    },
                ]
            },
        }),
        json.dumps({"type": "assistant.message", "data": {"content": "untrusted answer"}}),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "invalid"
    assert result["response"] == ""
    assert result["response_present"] is False
    assert result["failure_reason"].startswith("mcp_initialization_failure:")
    assert "secret" not in result["failure_reason"]
    diagnostic = result["diagnostics"]["events"][0]
    assert diagnostic["event_type"] == "session.mcp_servers_loaded"
    assert diagnostic["data"]["servers"][0]["status"] == "failed"
    assert "[REDACTED]" in diagnostic["data"]["servers"][0]["error"]


def test_real_session_error_schema_preserves_diagnostics_and_invalidates_answer(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.error",
            "data": {
                "errorType": "authentication",
                "errorCode": "invalid_token",
                "message": "Authorization: Custom opaque-secret",
                "providerCallId": "request-123",
                "serviceRequestId": "service-456",
                "stack": "at C:/Users/Jane Doe/private/module.js",
                "statusCode": 401,
                "url": "https://example.invalid/login",
            },
        }),
        json.dumps({"type": "assistant.message", "data": {"content": "untrusted answer"}}),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "invalid"
    assert result["response"] == ""
    assert result["response_present"] is False
    assert result["failure_reason"].startswith("session_error: authentication:")
    assert "opaque-secret" not in result["failure_reason"]
    diagnostic = result["diagnostics"]["events"][0]
    assert diagnostic["event_type"] == "session.error"
    assert diagnostic["data"]["statusCode"] == 401
    assert diagnostic["data"]["stack"] == "at <PATH>"


def test_diagnostic_output_is_bounded(monkeypatch):
    long_error = "failure " + ("x" * 20_000)
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_server_status_changed",
            "data": {"serverName": "foundry_docs", "status": "failed", "error": long_error},
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=long_error),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["diagnostics"]["stdout_truncated"] is True
    assert result["diagnostics"]["stderr_truncated"] is True
    assert len(result["diagnostics"]["stdout_excerpt"]) < 12_100
    assert len(result["diagnostics"]["stderr_excerpt"]) < 4_100


def test_sanitizer_redacts_prefixed_secrets_and_windows_paths(monkeypatch):
    stderr = (
        'AZURE_SEARCH_API_KEY="super secret" GITHUB_TOKEN=github_pat_abc '
        "at C:\\Users\\Jane Doe\\repo and \\\\server\\share\\private"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout="not-json",
            stderr=stderr,
        ),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    excerpt = result["diagnostics"]["stderr_excerpt"]
    assert "super secret" not in excerpt
    assert "github_pat_abc" not in excerpt
    assert "Jane Doe" not in excerpt
    assert "server\\share" not in excerpt
    assert "<PATH>" in excerpt


@pytest.mark.parametrize(
    ("raw", "secret"),
    [
        ("Authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
        ('Authorization: Digest username="alice", response="digest-secret"', "digest-secret"),
        ("Authorization: CustomScheme opaque custom value", "opaque custom value"),
    ],
)
def test_authorization_header_redacts_entire_value_for_every_scheme(raw, secret):
    sanitized, _truncated = _sanitize_text(raw)

    assert sanitized == "Authorization: [REDACTED]"
    assert secret not in sanitized


@pytest.mark.parametrize(
    "raw",
    [
        r'upstream={\"Authorization\":\"CustomScheme opaque-value\"}',
        r'upstream={\"authorization\":\"Basic dXNlcjpwYXNz\"}',
        r'upstream={\"AUTHORIZATION\":\"Digest username=alice response=digest-secret\"}',
    ],
)
def test_escaped_serialized_authorization_is_redacted_from_text(raw):
    sanitized, _truncated = _sanitize_text(raw)

    assert "opaque-value" not in sanitized
    assert "dXNlcjpwYXNz" not in sanitized
    assert "digest-secret" not in sanitized
    assert "[REDACTED]" in sanitized


def test_escaped_authorization_does_not_leak_in_stdout_or_stderr(monkeypatch):
    leaked = (
        r'upstream={\"Authorization\":\"Digest username=\\\"alice\\\", '
        r'response=\\\"digest-secret\\\"\"}'
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=f"{leaked}\nnot-json",
            stderr=leaked,
        ),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert "alice" not in result["diagnostics"]["stdout_excerpt"]
    assert "alice" not in result["diagnostics"]["stderr_excerpt"]
    assert "digest-secret" not in result["diagnostics"]["stdout_excerpt"]
    assert "digest-secret" not in result["diagnostics"]["stderr_excerpt"]
    assert "[REDACTED]" in result["diagnostics"]["stdout_excerpt"]
    assert "[REDACTED]" in result["diagnostics"]["stderr_excerpt"]


def test_exact_custom_scheme_escaped_authorization_does_not_leak_in_excerpts(monkeypatch):
    leaked = r'upstream={\"Authorization\":\"CustomScheme opaque-value\"}'
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=f"{leaked}\nnot-json",
            stderr=leaked,
        ),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert "opaque-value" not in result["diagnostics"]["stdout_excerpt"]
    assert "opaque-value" not in result["diagnostics"]["stderr_excerpt"]
    assert "[REDACTED]" in result["diagnostics"]["stdout_excerpt"]
    assert "[REDACTED]" in result["diagnostics"]["stderr_excerpt"]


def test_truncated_escaped_authorization_value_fails_closed(monkeypatch):
    leaked = (
        r'upstream={\"Authorization\":\"Digest nonce=LEAKME, username=\\\"alice\\\", '
        r'response=\\\"digest-secret\\\"' + ("x" * 20_000)
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=f"{leaked}\nnot-json",
            stderr=leaked,
        ),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    for excerpt in (
        result["diagnostics"]["stdout_excerpt"],
        result["diagnostics"]["stderr_excerpt"],
    ):
        assert "LEAKME" not in excerpt
        assert "digest-secret" not in excerpt
        assert "[REDACTED]" in excerpt


@pytest.mark.parametrize(
    "raw_path",
    [
        "C:/Users/Jane Doe/private/file.txt",
        "C:\\Users\\Jane Doe\\private\\file.txt",
        "\\\\server\\share\\Jane Doe\\private.txt",
        "//server/share/Jane Doe/private.txt",
        "/root",
        "/var/lib/My App/private.txt",
    ],
)
def test_absolute_path_leak_probes_cover_windows_unc_and_unix(raw_path):
    sanitized, _truncated = _sanitize_text(f"failed at {raw_path}")

    assert raw_path not in sanitized
    assert sanitized == "failed at <PATH>"


def test_sanitizer_redacts_json_style_secret_keys(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_server_status_changed",
            "data": {
                "serverName": "foundry_docs",
                "status": "failed",
                "api_key": "json-secret-value",
            },
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert "json-secret-value" not in result["diagnostics"]["stdout_excerpt"]
    assert result["diagnostics"]["events"][0]["data"]["api_key"] == "[REDACTED]"


def test_sanitizer_redacts_escaped_nested_json_secrets(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_server_status_changed",
            "data": {
                "serverName": "foundry_docs",
                "status": "failed",
                "message": json.dumps({"AZURE_SEARCH_API_KEY": "nested-json-secret"}),
            },
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert "nested-json-secret" not in result["diagnostics"]["stdout_excerpt"]


def test_process_exit_preserves_specific_mcp_failure_reason(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_server_status_changed",
            "data": {"serverName": "foundry_docs", "status": "failed", "error": "startup failed"},
        }),
        json.dumps({"type": "result", "exitCode": 1}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 1, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert "mcp_initialization_failure:" in result["failure_reason"]
    assert "process_exit_code: 1" in result["failure_reason"]


def test_non_success_preserves_stdout_even_when_tool_evidence_was_valid(monkeypatch):
    stdout = _event_stream(response="untrusted answer")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 1, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "error"
    assert result["response"] == ""
    assert result["response_present"] is False
    assert "untrusted answer" in result["diagnostics"]["stdout_excerpt"]


def test_failed_tool_clears_untrusted_answer_and_preserves_diagnostics(monkeypatch):
    stdout = _event_stream(tool_success=False, response="untrusted answer")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "invalid"
    assert result["response"] == ""
    assert result["response_present"] is False
    assert result["failure_reason"].startswith("tool_error:")
    assert "untrusted answer" in result["diagnostics"]["stdout_excerpt"]
    assert result["diagnostics"]["events"][0]["event_type"] == "tool.execution_complete"


@pytest.mark.parametrize("status", ["invalid", "error", "timeout"])
def test_scorer_clears_response_for_every_non_success_status(status):
    row = _raw_row(status=status, response="untrusted answer", failure_reason="failed")

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored["status"] == "invalid"
    assert scored["passed"] is False
    assert scored["operational"]["passed"] is False
    aggregates = aggregate_scores([scored])
    assert aggregates["operational_metrics"]["foundry-docs"]["pass_rate"] == 0.0
    assert aggregates["operational_metrics"]["foundry-docs"]["status_counts"] == {"invalid": 1}


def test_invalid_source_config_is_sanitized_in_scored_output():
    row = _raw_row()
    row["selected_source_config"]["command"] = r"token=CONFIGSECRET C:\Users\Victim\private"

    scored = score_result(row)
    persisted = json.dumps(scored)

    assert scored["row_valid"] is False
    assert "CONFIGSECRET" not in persisted
    assert "Victim" not in persisted
    assert "private" not in persisted
    assert "token=[REDACTED]" in persisted
    assert "<PATH>" in persisted
    assert scored["response"] == ""
    assert scored["response_present"] is False


def test_mcp_failure_server_name_is_sanitized_and_bounded(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_server_status_changed",
            "data": {
                "serverName": "token=server-secret C:\\Users\\alice\\private " + ("x" * 20_000),
                "status": "failed",
                "error": "startup failed",
            },
        }),
        json.dumps({"type": "result", "exitCode": 1}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 1, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert "server-secret" not in result["failure_reason"]
    assert "alice" not in result["failure_reason"]
    assert len(result["failure_reason"]) < 2_200


def test_size_based_event_truncation_is_schema_valid():
    row = _raw_row()
    source_events = _session_error_events_at_serialized_size(40_000)
    row["diagnostics"]["events"] = [
        {"event_type": "session.error", "data": event["data"]}
        for event in source_events
    ]
    row["diagnostics"]["events_truncated"] = True

    assert validate_row_schema(row) == []


def test_serialized_event_size_helper_matches_persisted_json_envelope():
    events = [
        {"event_type": "session.error", "data": {"message": "first"}},
        {"event_type": "session.mcp_servers_loaded", "data": {"servers": []}},
    ]

    assert serialized_diagnostic_events_size(events) == len(
        json.dumps(events, ensure_ascii=True, separators=(",", ":"))
    )


def _session_error_events_at_serialized_size(target_size: int) -> list[dict]:
    source_events = []
    diagnostic_events = []
    for _ in range(5):
        data = {"errorType": "q", "message": "m"}
        data.update({f"field{field_index}": "" for field_index in range(18)})
        source_events.append({"type": "session.error", "data": data})
        diagnostic_events.append({"event_type": "session.error", "data": dict(data)})

    remaining = target_size - serialized_diagnostic_events_size(diagnostic_events)
    assert remaining >= 0
    for field_index in range(18):
        for event_index in range(5):
            if remaining == 0:
                break
            addition = min(2_000, remaining)
            value = "x" * addition
            source_events[event_index]["data"][f"field{field_index}"] = value
            diagnostic_events[event_index]["data"][f"field{field_index}"] = value
            remaining -= addition
        if remaining == 0:
            break

    assert remaining == 0
    assert serialized_diagnostic_events_size(diagnostic_events) == target_size
    return source_events


def test_runner_accepts_event_envelope_at_49_998():
    source_events = _session_error_events_at_serialized_size(49_998)
    stdout = "\n".join([
        *(json.dumps(event, separators=(",", ":")) for event in source_events),
        json.dumps({"type": "result", "exitCode": 0}),
    ])

    parsed = parse_event_stream(stdout)

    assert parsed["diagnostic_events_truncated"] is False
    assert len(parsed["diagnostic_events"]) == 5
    assert serialized_diagnostic_events_size(parsed["diagnostic_events"]) == 49_998


def test_runner_accepts_event_envelope_at_50_000():
    source_events = _session_error_events_at_serialized_size(50_000)
    stdout = "\n".join([
        *(json.dumps(event, separators=(",", ":")) for event in source_events),
        json.dumps({"type": "result", "exitCode": 0}),
    ])

    parsed = parse_event_stream(stdout)

    assert parsed["diagnostic_events_truncated"] is False
    assert len(parsed["diagnostic_events"]) == 5
    assert serialized_diagnostic_events_size(parsed["diagnostic_events"]) == 50_000


def test_runner_truncates_event_envelope_at_50_001():
    source_events = _session_error_events_at_serialized_size(50_001)
    stdout = "\n".join([
        *(json.dumps(event, separators=(",", ":")) for event in source_events),
        json.dumps({"type": "result", "exitCode": 0}),
    ])

    parsed = parse_event_stream(stdout)

    assert parsed["diagnostic_events_truncated"] is True
    assert len(parsed["diagnostic_events"]) == 4
    assert serialized_diagnostic_events_size(parsed["diagnostic_events"]) < 50_000


def test_runner_truncates_event_envelope_at_50_002():
    source_events = _session_error_events_at_serialized_size(50_002)
    stdout = "\n".join([
        *(json.dumps(event, separators=(",", ":")) for event in source_events),
        json.dumps({"type": "result", "exitCode": 0}),
    ])

    parsed = parse_event_stream(stdout)

    assert parsed["diagnostic_events_truncated"] is True
    assert len(parsed["diagnostic_events"]) == 4
    assert serialized_diagnostic_events_size(parsed["diagnostic_events"]) < 50_000


def test_scorer_accepts_exact_event_envelope_limit_and_rejects_one_byte_over():
    at_limit = _raw_row()
    at_limit["diagnostics"]["events"] = [
        {"event_type": "session.error", "data": event["data"]}
        for event in _session_error_events_at_serialized_size(50_000)
    ]
    assert serialized_diagnostic_events_size(at_limit["diagnostics"]["events"]) == 50_000
    assert validate_row_schema(at_limit) == []

    over_limit = _raw_row()
    over_limit["diagnostics"]["events"] = [
        {"event_type": "session.error", "data": event["data"]}
        for event in _session_error_events_at_serialized_size(50_001)
    ]
    assert serialized_diagnostic_events_size(over_limit["diagnostics"]["events"]) == 50_001
    assert "diagnostics.events exceeds its total serialized size limit" in validate_row_schema(over_limit)


def test_scorer_accepts_49_998_event_envelope_and_rejects_50_002():
    below_limit = _raw_row()
    below_limit["diagnostics"]["events"] = [
        {"event_type": "session.error", "data": event["data"]}
        for event in _session_error_events_at_serialized_size(49_998)
    ]
    assert serialized_diagnostic_events_size(below_limit["diagnostics"]["events"]) == 49_998
    assert validate_row_schema(below_limit) == []

    above_limit = _raw_row()
    above_limit["diagnostics"]["events"] = [
        {"event_type": "session.error", "data": event["data"]}
        for event in _session_error_events_at_serialized_size(50_002)
    ]
    assert serialized_diagnostic_events_size(above_limit["diagnostics"]["events"]) == 50_002
    assert "diagnostics.events exceeds its total serialized size limit" in validate_row_schema(above_limit)


def _session_error_event_with_individual_size(target_size: int) -> tuple[dict, dict]:
    source = {"type": "session.error", "data": {"errorType": "q", "message": "m"}}
    source["data"].update({f"field{field_index}": "" for field_index in range(18)})
    diagnostic = {"event_type": "session.error", "data": dict(source["data"])}

    remaining = target_size - len(json.dumps(diagnostic, ensure_ascii=True, separators=(",", ":")))
    assert remaining >= 0
    for field_index in range(18):
        if remaining == 0:
            break
        addition = min(2_000, remaining)
        value = "x" * addition
        source["data"][f"field{field_index}"] = value
        diagnostic["data"][f"field{field_index}"] = value
        remaining -= addition

    assert remaining == 0
    assert len(json.dumps(diagnostic, ensure_ascii=True, separators=(",", ":"))) == target_size
    return source, diagnostic


def test_list_envelope_overhead_truncates_runner_and_is_rejected_by_scorer():
    source_events = []
    diagnostic_events = []
    for _ in range(3):
        source, diagnostic = _session_error_event_with_individual_size(16_666)
        source_events.append(source)
        diagnostic_events.append(diagnostic)

    per_event_sum = sum(
        len(json.dumps(event, ensure_ascii=True, separators=(",", ":")))
        for event in diagnostic_events
    )
    assert per_event_sum == 49_998
    assert serialized_diagnostic_events_size(diagnostic_events) == 50_002

    parsed = parse_event_stream("\n".join([
        *(json.dumps(event, separators=(",", ":")) for event in source_events),
        json.dumps({"type": "result", "exitCode": 0}),
    ]))
    assert parsed["diagnostic_events_truncated"] is True
    assert len(parsed["diagnostic_events"]) == 2
    assert serialized_diagnostic_events_size(parsed["diagnostic_events"]) < 50_000

    row = _raw_row()
    row["diagnostics"]["events"] = diagnostic_events
    assert "diagnostics.events exceeds its total serialized size limit" in validate_row_schema(row)


def test_nested_stdout_truncation_flag_is_schema_valid():
    row = _raw_row()
    row["diagnostics"]["stdout_excerpt"] = "x" * 2_000 + "...[truncated]"
    row["diagnostics"]["stdout_truncated"] = True

    assert validate_row_schema(row) == []


def test_large_event_is_stopped_before_json_parse_and_remains_bounded():
    huge_event = b'{"type":"session.error","data":{"message":"' + (b"x" * 5_000_000) + b'"}}'

    started = time.perf_counter()
    parsed = parse_event_stream(huge_event)
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0
    assert parsed["stdout_input_truncated"] is True
    assert "pre-parse limit" in parsed["parse_error"]
    assert parsed["diagnostic_events"] == []
    assert parsed["response"] == ""


def test_real_size_57kb_tool_result_parses_and_validates_selected_source(monkeypatch):
    completion = {
        "type": "tool.execution_complete",
        "data": {
            "toolCallId": "call-1",
            "success": True,
            "result": {"content": [{"type": "text", "text": ""}]},
        },
    }
    base_size = len(json.dumps(completion, separators=(",", ":")).encode())
    completion["data"]["result"]["content"][0]["text"] = "x" * (57_000 - base_size)
    completion_line = json.dumps(completion, separators=(",", ":"))
    assert len(completion_line.encode()) == 57_000

    stdout = "\n".join([
        json.dumps({
            "type": "tool.execution_start",
            "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"},
        }),
        completion_line,
        json.dumps({"type": "assistant.message", "data": {"content": "trusted answer"}}),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "success"
    assert result["source_validated"] is True
    assert result["response"] == "trusted answer"
    assert result["event_parse_error"] is None


def test_deeply_nested_bounded_json_fails_closed_without_recursion_crash():
    nested = "[" * 5_000 + "null" + "]" * 5_000
    stdout = f'{{"type":"session.error","data":{{"message":{nested}}}}}'

    parsed = parse_event_stream(stdout)

    assert "invalid JSON event" in parsed["parse_error"]
    assert parsed["diagnostic_events"] == []
    assert parsed["response"] == ""


def test_diagnostic_path_keys_are_sanitized(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "tool.execution_start",
            "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"},
        }),
        json.dumps({
            "type": "tool.execution_complete",
            "data": {
                "toolCallId": "call-1",
                "success": False,
                "result": {"C:\\Users\\someone\\private.txt": "failed"},
            },
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    serialized = json.dumps(result["diagnostics"])
    assert "private.txt" not in serialized
    assert "<PATH>" in serialized


def test_tool_name_is_validated_raw_but_persisted_sanitized(monkeypatch):
    tool_name = r"foundry_docs-search_docs token=LEAKME C:\Users\Alice\private"
    stdout = _event_stream(tool_name=tool_name, response="trusted answer")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    raw_row = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )
    scored_row = score_result(raw_row)

    assert raw_row["source_validated"] is True
    assert scored_row["row_valid"] is True
    assert raw_row["observed_tools"] == ["foundry_docs-search_docs token=[REDACTED] <PATH>"]
    for row in (raw_row, scored_row):
        persisted = json.dumps(row)
        assert "LEAKME" not in persisted
        assert "Alice" not in persisted
        assert "private" not in persisted


def test_cross_source_failure_reason_sanitizes_tool_identifier(monkeypatch):
    tool_name = r"evil-search token=LEAKME C:\Users\Alice\private"
    stdout = _event_stream(tool_name=tool_name, response="untrusted answer")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=""),
    )

    result = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )

    assert result["status"] == "invalid"
    assert result["failure_reason"].startswith("cross_source_tool_call:")
    assert "LEAKME" not in result["failure_reason"]
    assert "Alice" not in result["failure_reason"]
    assert "private" not in result["failure_reason"]
    assert "token=[REDACTED]" in result["failure_reason"]
    assert "<PATH>" in result["failure_reason"]


def test_parse_error_sanitizes_tool_call_identifier():
    tool_call_id = r"call token=CALLSECRET C:\Users\Alice\private"
    stdout = "\n".join([
        json.dumps({
            "type": "tool.execution_start",
            "data": {"toolCallId": tool_call_id, "toolName": "foundry_docs-search_docs"},
        }),
        json.dumps({
            "type": "tool.execution_start",
            "data": {"toolCallId": tool_call_id, "toolName": "foundry_docs-search_docs"},
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ])

    parsed = parse_event_stream(stdout)

    assert "CALLSECRET" not in parsed["parse_error"]
    assert "Alice" not in parsed["parse_error"]
    assert "private" not in parsed["parse_error"]
    assert "token=[REDACTED]" in parsed["parse_error"]
    assert "<PATH>" in parsed["parse_error"]


@pytest.mark.parametrize(
    "diagnostics",
    [
        None,
        {
            "events": [{}] * 21,
            "events_truncated": True,
            "stdout_excerpt": "",
            "stdout_truncated": False,
            "stderr_excerpt": "",
            "stderr_truncated": False,
        },
        {
            "events": [],
            "events_truncated": False,
            "stdout_excerpt": "x" * 20_000,
            "stdout_truncated": False,
            "stderr_excerpt": "",
            "stderr_truncated": False,
        },
        {
            "events": [{"event_type": "status", "data": {"message": "x" * 1_000_000}}],
            "events_truncated": False,
            "stdout_excerpt": "",
            "stdout_truncated": False,
            "stderr_excerpt": "",
            "stderr_truncated": False,
        },
        {
            "events": [],
            "events_truncated": False,
            "stdout_excerpt": "",
            "stdout_truncated": False,
            "stderr_excerpt": "",
            "stderr_truncated": False,
            "raw_stdout": "x" * 1_000_000,
        },
    ],
)
def test_scorer_rejects_missing_or_unbounded_diagnostics(diagnostics):
    row = _raw_row()
    row["diagnostics"] = diagnostics

    scored = score_result(row)

    assert scored["row_valid"] is False


def test_parse_event_stream_rejects_incomplete_tool_call():
    stdout = "\n".join(
        [
            json.dumps({
                "type": "tool.execution_start",
                "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"},
            }),
            json.dumps({"type": "result", "exitCode": 0}),
        ]
    )

    parsed = parse_event_stream(stdout)

    assert parsed["observed_tools"] == ["foundry_docs-search_docs"]
    assert "missing completion evidence" in parsed["parse_error"]


def test_parse_event_stream_rejects_non_object_events_and_unknown_tool_outcomes():
    stdout = "\n".join(
        [
            "[]",
            json.dumps({
                "type": "tool.execution_start",
                "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"},
            }),
            json.dumps({
                "type": "tool.execution_complete",
                "data": {"toolCallId": "call-1"},
            }),
            json.dumps({"type": "assistant.message", "data": {"content": "answer"}}),
            json.dumps({"type": "result", "exitCode": 0}),
        ]
    )

    parsed = parse_event_stream(stdout)

    assert "event must be a JSON object" in parsed["parse_error"]
    assert "tool completion missing Boolean success" in parsed["parse_error"]


@pytest.mark.parametrize(
    "events",
    [
        [
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"}},
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"}},
        ],
        [
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "call-1", "success": True}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "call-1", "success": True}},
        ],
        [
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"}},
            {
                "type": "tool.execution_complete",
                "data": {
                    "toolCallId": "call-1",
                    "toolName": "foundry_docs-get_doc",
                    "success": True,
                },
            },
        ],
    ],
)
def test_parse_event_stream_rejects_malformed_tool_lifecycles(events):
    events.extend([
        {"type": "assistant.message", "data": {"content": "answer"}},
        {"type": "result", "exitCode": 0},
    ])

    parsed = parse_event_stream("\n".join(json.dumps(event) for event in events))

    assert parsed["parse_error"] is not None


def test_scorer_rejects_success_row_missing_required_evidence_fields():
    fabricated = {
        "scenario_id": "scenario-1",
        "server": "foundry-docs",
        "model": "model-1",
        "category": "getting-started",
        "response": "Use an agent.",
        "status": "success",
        "passed": True,
        "source_validated": True,
        "rubric": SCENARIO["rubric"],
    }

    scored = score_result(fabricated)

    assert scored["row_valid"] is False
    assert scored["scores"]["has_response"] is False


def test_scorer_rejects_and_sanitizes_malicious_persisted_identifiers():
    row = _raw_row()
    malicious = r"foundry_docs-search_docs token=LEAKME C:\Users\Alice\private " + ("x" * 500)
    row["observed_tools"] = [malicious]
    row["successful_tools"] = [malicious]
    row["event_parse_error"] = r"duplicate call token=PARSESECRET C:\Users\Bob\private"
    row["diagnostics"]["events"] = [{
        "event_type": "tool.execution_complete",
        "data": {
            "toolName": malicious,
            "toolCallId": r"call token=CALLSECRET C:\Users\Carol\private",
        },
    }]

    scored = score_result(row)
    persisted = json.dumps(scored)

    assert scored["row_valid"] is False
    assert scored["status"] == "invalid"
    for leaked in ("LEAKME", "Alice", "PARSESECRET", "Bob", "CALLSECRET", "Carol", "private"):
        assert leaked not in persisted
    assert all(len(identifier) <= 270 for identifier in scored["observed_tools"])
    assert "token=[REDACTED]" in persisted
    assert "<PATH>" in persisted


def test_scorer_projects_known_fields_and_rejects_unsanitized_diagnostics():
    row = _raw_row()
    row["extra_secret"] = r"token=TOPSECRET C:\Users\Victim\private"
    row["diagnostics"]["stdout_excerpt"] = r"token=DIAGSECRET C:\Users\Victim\private"

    scored = score_result(row)
    persisted = json.dumps(scored)

    assert scored["row_valid"] is False
    assert "extra_secret" not in scored
    for leaked in ("TOPSECRET", "DIAGSECRET", "Victim", "private"):
        assert leaked not in persisted
    assert "token=[REDACTED]" in persisted
    assert "<PATH>" in persisted


def test_scorer_sanitizes_malformed_nested_retained_fields():
    row = _raw_row()
    row["question"] = {"nested": r"token=LEAKME C:\Users\Alice\private"}
    row["event_parse_error"] = {"nested": r"token=PARSELEAK C:\Users\Bob\private"}
    row["observed_tools"] = {"nested": r"token=TOOLLEAK C:\Users\Carol\private"}

    scored = score_result(row)
    persisted = json.dumps(scored)

    assert scored["row_valid"] is False
    for leaked in ("LEAKME", "Alice", "PARSELEAK", "Bob", "TOOLLEAK", "Carol", "private"):
        assert leaked not in persisted
    assert "token=[REDACTED]" in persisted
    assert "<PATH>" in persisted
    assert scored["observed_tools"] == []


def test_scorer_rejects_non_string_diagnostic_identifier():
    row = _raw_row()
    row["diagnostics"]["events"] = [{
        "event_type": "tool.execution_complete",
        "data": {"toolCallId": 123, "toolName": "foundry_docs-search_docs"},
    }]

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored["status"] == "invalid"
    assert "diagnostics.events[0].data.toolCallId must be a string identifier" in scored["failure_reason"]


@pytest.mark.parametrize(
    "malformed",
    [
        None,
        {"server": "foundry-docs", "response": "answer"},
        {**_raw_row(), "response": ["not", "text"]},
        {**_raw_row(), "category": None},
        {**_raw_row(), "status": ["success"]},
        {**_raw_row(), "rubric": {"must_mention": [None]}},
        {**_raw_row(), "tool_errors": "bad"},
        {**_raw_row(), "turns": []},
        {**_raw_row(), "response_time_seconds": "bad"},
    ],
)
def test_malformed_rows_become_invalid_diagnostics_without_crashing(malformed):
    scored = score_result(malformed)
    aggregates = aggregate_scores([scored])
    publication = validate_required_matrix(
        [scored],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
    )

    assert scored["row_valid"] is False
    assert aggregates["operational_metrics"]
    assert publication["allowed"] is False


def test_required_matrix_enforces_azure_server_policy():
    row = score_result(_raw_row())

    publication = validate_required_matrix(
        [row],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
        azure_required_servers={"foundry-docs"},
    )

    assert publication["allowed"] is False
    assert publication["invalid_rows"][0]["failure_reason"] == "azure_required_evidence_missing"
    assert row["status"] == "invalid"
    assert row["passed"] is False
    assert row["response"] == ""
    assert row["response_present"] is False
    assert row["row_valid"] is False
    assert row["scores"] == {
        "completeness": 0.0,
        "quality": 0.0,
        "doc_retrieval": 0.0,
        "response_length": 0,
        "has_response": False,
    }
    aggregates = aggregate_scores([row])
    assert aggregates["server_model_matrix"] == {}
    assert aggregates["server_averages"] == {}


def test_malformed_azure_tool_evidence_fails_closed_without_crashing():
    malformed = _raw_row(model="unexpected-model")
    malformed["successful_tools"] = [None]
    scored = score_result(malformed)

    publication = validate_required_matrix(
        [scored],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
        azure_required_servers={"foundry-docs"},
    )

    assert scored["row_valid"] is False
    assert scored["status"] == "invalid"
    assert scored["response"] == ""
    assert publication["allowed"] is False


def test_duplicate_azure_rows_are_all_excluded_from_aggregates():
    missing_azure = score_result(_raw_row())
    valid_azure_raw = _raw_row()
    valid_azure_raw["azure_required"] = True
    valid_azure_raw["azure_live_query_proven"] = True
    valid_azure_raw["selected_source_config"]["azure_required"] = True
    valid_azure = score_result(valid_azure_raw)
    assert valid_azure["row_valid"] is True

    publication = validate_required_matrix(
        [missing_azure, valid_azure],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
        azure_required_servers={"foundry-docs"},
    )
    aggregates = aggregate_scores([missing_azure, valid_azure])

    assert publication["allowed"] is False
    assert publication["duplicate_rows"] == ["scenario-1 / foundry-docs / model-1"]
    assert all(row["row_valid"] is False for row in (missing_azure, valid_azure))
    assert all(row["response"] == "" for row in (missing_azure, valid_azure))
    assert aggregates["server_model_matrix"] == {}
    assert aggregates["server_averages"] == {}


def test_unexpected_rows_are_invalidated_before_aggregation():
    unexpected = score_result(_raw_row(model="unexpected-model"))
    assert unexpected["row_valid"] is True

    publication = validate_required_matrix(
        [unexpected],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
        azure_required_servers={"foundry-docs"},
    )
    aggregates = aggregate_scores([unexpected])

    assert publication["allowed"] is False
    assert publication["unexpected_rows"] == ["scenario-1 / foundry-docs / unexpected-model"]
    assert unexpected["row_valid"] is False
    assert unexpected["response"] == ""
    assert unexpected["scores"]["has_response"] is False
    assert aggregates["server_model_matrix"] == {}
    assert aggregates["server_averages"] == {}


def test_unknown_server_row_and_required_matrix_fail_closed():
    unknown = _raw_row()
    unknown["server"] = "unknown-server"
    unknown["selected_source"] = "unknown-server"
    unknown["selected_source_config"] = {
        "name": "unknown",
        "type": "local",
        "endpoint": None,
        "command": "unknown",
        "tool_prefix": None,
        "azure_required": False,
    }
    unknown["observed_tools"] = ["unknown-search"]
    unknown["successful_tools"] = ["unknown-search"]

    scored = score_result(unknown)
    publication = validate_required_matrix(
        [scored],
        scenario_ids=["scenario-1"],
        servers=["unknown-server"],
        models=["model-1"],
    )
    aggregates = aggregate_scores([scored])

    assert scored["row_valid"] is False
    assert scored["status"] == "invalid"
    assert scored["response"] == ""
    assert publication["allowed"] is False
    assert publication["unknown_required_servers"] == ["unknown-server"]
    assert "unknown required server(s): unknown-server" in publication["failure_reasons"]
    assert aggregates["server_model_matrix"] == {}
    assert aggregates["server_averages"] == {}


def test_unknown_azure_required_server_blocks_otherwise_valid_matrix():
    valid = score_result(_raw_row())

    publication = validate_required_matrix(
        [valid],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
        azure_required_servers={"typo-server"},
    )

    assert publication["allowed"] is False
    assert publication["unknown_required_servers"] == ["typo-server"]
    assert "unknown required server(s): typo-server" in publication["failure_reasons"]


def test_required_matrix_sanitizes_unknown_selector_row_labels():
    selector = r"token=SERVERLEAK C:\Users\Alice\private"

    publication = validate_required_matrix(
        [],
        scenario_ids=["scenario-1"],
        servers=[selector],
        models=["model-1"],
        azure_required_servers={selector},
    )
    persisted = json.dumps(publication)

    assert publication["allowed"] is False
    assert "SERVERLEAK" not in persisted
    assert "Alice" not in persisted
    assert "private" not in persisted
    assert "token=[REDACTED]" in persisted
    assert "<PATH>" in persisted


def test_scorer_rejects_contradictory_source_descriptor_and_tool_evidence():
    row = _raw_row()
    row["selected_source_config"]["command"] = "different-command"
    row["observed_tools"] = ["foundry_docs-get_doc"]
    row["successful_tools"] = ["foundry_docs-search_docs"]

    scored = score_result(row)

    assert scored["row_valid"] is False


def test_scorer_rejects_contradictory_azure_descriptor():
    row = _raw_row()
    row["azure_required"] = True
    row["azure_live_query_proven"] = True
    row["selected_source_config"]["azure_required"] = False

    scored = score_result(row)

    assert scored["row_valid"] is False


@pytest.mark.parametrize(
    "events",
    [
        [
            {"type": "assistant.message", "data": {"content": "answer"}},
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "call-1", "success": True}},
            {"type": "result", "exitCode": 0},
        ],
        [
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "call-1", "success": True}},
            {"type": "assistant.message", "data": {"content": "answer"}},
            {"type": "result", "exitCode": 0},
            {"type": "assistant.message", "data": {"content": "late answer"}},
        ],
        [
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "call-1", "success": True}},
            {"type": "assistant.message", "data": {"content": "answer"}},
            {"type": "result", "exitCode": 0},
            {"type": "result", "exitCode": 0},
        ],
        [
            {"type": "tool.execution_start", "data": {"toolCallId": "call-1", "toolName": "foundry_docs-get_doc"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "call-1", "success": True}},
            {"type": "assistant.message", "data": {"content": "answer"}},
            {"type": "tool.execution_start", "data": {"toolCallId": "call-2", "toolName": "foundry_docs-search_docs"}},
            {"type": "tool.execution_complete", "data": {"toolCallId": "call-2", "success": True}},
            {"type": "result", "exitCode": 0},
        ],
    ],
)
def test_parse_event_stream_rejects_causally_invalid_sequences(events):
    parsed = parse_event_stream("\n".join(json.dumps(event) for event in events))

    assert parsed["parse_error"] is not None


def test_required_matrix_denominators_include_every_outcome():
    rows = [
        score_result(_raw_row(scenario_id="success", status="success")),
        score_result(_raw_row(scenario_id="invalid", status="invalid", response="", failure_reason="bad evidence")),
        score_result(_raw_row(scenario_id="error", status="error", response="", failure_reason="process failed")),
        score_result(_raw_row(scenario_id="timeout", status="timeout", response="", failure_reason="timed out")),
    ]

    publication = validate_required_matrix(
        rows,
        scenario_ids=["success", "invalid", "error", "timeout", "missing"],
        servers=["foundry-docs"],
        models=["model-1"],
    )

    assert publication["allowed"] is False
    assert publication["required_rows"] == 5
    assert publication["status_counts"] == {
        "success": 1,
        "invalid": 1,
        "error": 1,
        "timeout": 1,
        "missing": 1,
    }
    assert publication["response_counts"] == {"present": 1, "missing": 3}


def test_invalid_matrix_generates_diagnostics_without_comparative_scores():
    rows = [
        score_result(_raw_row()),
        score_result(_raw_row(scenario_id="scenario-2", status="invalid", failure_reason="unproven source")),
    ]
    publication = validate_required_matrix(
        rows,
        scenario_ids=["scenario-1", "scenario-2"],
        servers=["foundry-docs"],
        models=["model-1"],
    )
    aggregates = aggregate_scores(rows)
    aggregates["denominators"] = {
        "required_rows": publication["required_rows"],
        "observed_rows": publication["observed_rows"],
        "unique_observed_rows": publication["unique_observed_rows"],
        "status_counts": publication["status_counts"],
        "response_counts": publication["response_counts"],
    }

    report = generate_report({
        "metadata": {"run_id": "run-1", "timestamp": "2026-07-28T00:00:00Z"},
        "aggregates": aggregates,
        "publication": publication,
        "results": rows,
    })

    assert "Comparative publication blocked" in report
    assert "unproven source" in report
    assert "Scoreboard" not in report
    assert "Hypothesis Testing" not in report


def test_scorer_cli_writes_blocked_diagnostics_before_failing(tmp_path):
    raw_path = tmp_path / "raw.json"
    scenarios_path = tmp_path / "scenarios.json"
    output_path = tmp_path / "scored.json"
    raw_path.write_text(
        json.dumps({
            "metadata": {
                "run_id": r"run-1 token=RUNSECRET C:\Users\Alice\private",
                "servers": [r"foundry-docs token=SERVERSECRET C:\Users\Bob\private"],
                "models": [r"model-1 token=MODELSECRET C:\Users\Carol\private"],
                "extra_secret": r"token=EXTRASECRET C:\Users\Dana\private",
            },
            "results": [_raw_row()],
        }),
        encoding="utf-8",
    )
    scenarios_path.write_text(
        json.dumps([{"id": "scenario-1"}, {"id": "scenario-2"}]),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parents[1] / "scripts" / "eval_scorer.py"),
            str(raw_path),
            "--output",
            str(output_path),
            "--required-scenarios",
            str(scenarios_path),
            "--required-servers",
            "foundry-docs",
            "--required-models",
            "model-1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "=== Server Averages ===" not in proc.stdout
    assert "=== Server × Model Matrix ===" not in proc.stdout
    scored = json.loads(output_path.read_text(encoding="utf-8"))
    assert scored["publication"]["allowed"] is False
    assert scored["aggregates"]["denominators"]["status_counts"]["missing"] == 1
    persisted = json.dumps(scored["metadata"])
    for leaked in (
        "RUNSECRET",
        "Alice",
        "SERVERSECRET",
        "Bob",
        "MODELSECRET",
        "Carol",
        "EXTRASECRET",
        "Dana",
        "private",
    ):
        assert leaked not in persisted
    assert "extra_secret" not in scored["metadata"]
    assert "token=[REDACTED]" in persisted
    assert "<PATH>" in persisted
