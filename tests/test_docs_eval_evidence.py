"""Process-boundary and publication-gate tests for documentation evaluation evidence."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

import pytest
from fastmcp import Client

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import run_docs_eval  # noqa: E402
from eval_report import generate_report  # noqa: E402
from eval_scorer import (  # noqa: E402
    _sanitize_metadata,
    aggregate_scores,
    score_result as _score_result,
    validate_trusted_scenarios,
    validate_required_matrix,
    validate_row_schema,
)
from foundry_docs_mcp._server_factory import DOCS_CONFIG, build_server  # noqa: E402
from run_docs_eval import (  # noqa: E402
    MCP_SERVERS,
    _sanitize_response_text,
    _sanitize_text,
    build_mcp_config,
    compare_results,
    parse_event_stream,
    run_evaluation,
    run_single_eval,
    select_servers,
    serialized_diagnostic_events_size,
)


SCENARIO = {
    "id": "scenario-1",
    "category": "getting-started",
    "question": "How do I create an agent?",
    "rubric": {
        "must_mention": ["agent"],
        "quality_criteria": ["step-by-step"],
        "expected_docs": ["agent"],
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
        "question": SCENARIO["question"],
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


def score_result(result, trusted_scenarios=None):
    if trusted_scenarios is None:
        scenario_id = result.get("scenario_id") if isinstance(result, dict) else SCENARIO["id"]
        trusted_scenarios = {
            scenario_id: {
                "id": scenario_id,
                "question": SCENARIO["question"],
                "category": SCENARIO["category"],
                "rubric": SCENARIO["rubric"],
            }
        }
    return _score_result(result, trusted_scenarios)


def _trusted_definitions(*scenario_ids):
    return [
        {
            "id": scenario_id,
            "question": SCENARIO["question"],
            "category": SCENARIO["category"],
            "rubric": SCENARIO["rubric"],
        }
        for scenario_id in scenario_ids
    ]


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


def test_success_response_is_sanitized_in_raw_and_scored_rows(monkeypatch):
    response = r"Useful answer. token=LEAKME See C:\Users\Alice\private for details."
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=_event_stream(response=response),
            stderr="",
        ),
    )

    raw_row = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )
    scored_row = score_result(raw_row)

    assert raw_row["status"] == "success"
    assert scored_row["row_valid"] is True
    assert raw_row["response"].startswith("Useful answer.")
    for row in (raw_row, scored_row):
        persisted = json.dumps(row)
        assert "LEAKME" not in persisted
        assert "Alice" not in persisted
        assert "private" not in persisted
        assert "token=[REDACTED]" in persisted
        assert "<PATH>" in persisted


def test_scorer_cli_requires_trusted_scenario_file_before_scoring(tmp_path):
        raw_path = tmp_path / "raw.json"
        output_path = tmp_path / "scored.json"
        raw_path.write_text(
            json.dumps({"metadata": {}, "results": [_raw_row()]}),
            encoding="utf-8",
        )

        proc = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parents[1] / "scripts" / "eval_scorer.py"),
                str(raw_path),
                "--output",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert proc.returncode == 2
        assert "--required-scenarios" in proc.stderr
        assert not output_path.exists()


def test_success_response_preserves_root_relative_documentation_link(monkeypatch):
    response = (
        "Use agents. See [agent docs](/concepts/agents) for prerequisites. "
        "Then configure managed identity."
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=_event_stream(response=response),
            stderr="",
        ),
    )

    raw_row = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )
    scored_row = score_result(raw_row)

    assert raw_row["status"] == "success"
    assert raw_row["response"] == response
    assert scored_row["row_valid"] is True
    assert scored_row["response"] == response


def test_success_response_preserves_bare_route_and_https_url_but_redacts_sensitive_query():
    response = (
        "See /concepts/agents and https://learn.microsoft.com/en-us/azure/ai. "
        "Do not expose [private](/concepts/agents?token=LEAKME&view=foundry). "
        "Signed: https://host/path?sig=SUPERSECRET&se=2099-01-01. "
        "Bare: /concepts/agents?sig=BARESECRET&view=foundry. "
        "OAuth: https://host/path?access_token=OAUTHSECRET&view=foundry."
    )

    sanitized = _sanitize_response_text(response)

    assert "/concepts/agents" in sanitized
    assert "https://learn.microsoft.com/en-us/azure/ai" in sanitized
    assert "LEAKME" not in sanitized
    assert "token=[REDACTED]" in sanitized
    assert "view=foundry" in sanitized
    assert "SUPERSECRET" not in sanitized
    assert "sig=[REDACTED]&se=2099-01-01" in sanitized
    assert "BARESECRET" not in sanitized
    assert "/concepts/agents?sig=[REDACTED]&view=foundry." in sanitized
    assert "OAUTHSECRET" not in sanitized
    assert "access_token=[REDACTED]&view=foundry." in sanitized
    assert _sanitize_response_text(sanitized) == sanitized


def test_success_response_redacts_confirmed_unix_local_paths_and_bounds_long_routes():
    response = "Read /etc/private.conf and /home/alice/private before [docs](/" + ("x" * 200_000) + ")."

    sanitized = _sanitize_response_text(response)

    assert "/etc/private.conf" not in sanitized
    assert "/home/alice/private" not in sanitized
    assert sanitized.count("<PATH>") == 2
    assert len(sanitized) <= 50_000 + len("...[truncated]")


def test_success_response_preserves_sentence_and_os_named_root_link():
    response = (
        r"Read C:\Users\Alice\private. This sentence must remain intact. "
        r"Also read C:\Users\Alice\other! Keep this too. "
        "See [home docs](/home/overview)."
    )

    sanitized = _sanitize_response_text(response)

    assert sanitized == (
        "Read <PATH>. This sentence must remain intact. "
        "Also read <PATH>! Keep this too. "
        "See [home docs](<PATH>)."
    )


def test_success_response_path_match_stops_before_unrecognized_prose():
    response = r"The file C:\Users\Alice\private should remain secret while this prose survives."

    sanitized = _sanitize_response_text(response)

    assert sanitized == "The file <PATH> should remain secret while this prose survives."


def test_success_response_stops_unquoted_path_after_filename_component():
    response = (
        r"The file is at C:\Users\Alice\secret.txt locally. "
        "The export is /home/alice/Customer SSN.csv now."
    )

    sanitized = _sanitize_response_text(response)

    assert sanitized == "The file is at <PATH> locally. The export is <PATH> now."


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (
            r"Open C:\Users\Alice\Customer SSN.csv and continue.",
            "Open <PATH> and continue.",
        ),
        (
            r"Open C:\Users\O'Connor\Customer SSN.csv and continue.",
            "Open <PATH> and continue.",
        ),
        (
            "Open $HOME/private.txt and ${HOME}/fourth.txt and ~/other.txt and %USERPROFILE%\\third.txt.",
            "Open <PATH> and <PATH> and <PATH> and <PATH>.",
        ),
        (
            r"Open C:\Program Files and \\server\share\Customer Data and $HOME/Customer Data.",
            "Open <PATH> and <PATH> and <PATH>.",
        ),
        (
            r"Open C:\Users\Alice\Customer Data using Explorer.",
            "Open <PATH> using Explorer.",
        ),
        (
            r"Open C:\Users\Alice\Customer SSN exists nearby.",
            "Open <PATH> exists nearby.",
        ),
        (
            r"Open C:\Users\Alice\Customer Sensitive Data.csv and /home/alice/Customer Sensitive Data.csv.",
            "Open <PATH> and <PATH>.",
        ),
        (
            "Open ~alice/private.txt and /app/Customer Data/config.json and /data/private.bin.",
            "Open <PATH> and <PATH> and <PATH>.",
        ),
    ],
)
def test_success_response_redacts_unquoted_paths_with_spaces_apostrophes_and_home_aliases(response, expected):
    assert _sanitize_response_text(response) == expected


def test_success_response_redacts_entire_quoted_local_path_with_spaces():
    response = r'Open "C:\Users\Alice\Customer SSN.csv" and continue.'

    sanitized = _sanitize_response_text(response)

    assert sanitized == 'Open "<PATH>" and continue.'


def test_success_response_redacts_single_quoted_path_with_apostrophe():
    response = r"Open 'C:\Users\O'Connor\Customer SSN.csv' and continue."

    sanitized = _sanitize_response_text(response)

    assert sanitized == "Open '<PATH>' and continue."


def test_success_response_redacts_complete_path_under_home_prefix():
    response = "Open \"C:\\Users\\nbrady\\O'Connor Customer SSN.csv\" and continue."

    sanitized = _sanitize_response_text(response)

    assert sanitized == 'Open "<PATH>" and continue.'


def test_success_response_unclosed_quoted_path_does_not_consume_later_prose():
    response = "Open \"C:\\Users\\Alice\\secret.txt\nKeep this paragraph and say \"done\"."

    sanitized = _sanitize_response_text(response)

    assert "secret.txt" not in sanitized
    assert "Keep this paragraph" in sanitized
    assert '"done"' in sanitized


def test_success_response_quoted_path_stops_before_arbitrary_following_word():
    response = r'Open "C:\Users\Alice\secret.txt" using the command "Open". Then continue.'

    sanitized = _sanitize_response_text(response)

    assert sanitized == 'Open "<PATH>" using the command "Open". Then continue.'


def test_success_response_redacts_complete_dotted_token_and_preserves_period():
    response = "Use token=header.payload.signature. Then continue."

    sanitized = _sanitize_response_text(response)

    assert sanitized == "Use token=[REDACTED]. Then continue."


def test_success_response_redacts_common_unix_roots_and_bare_oauth_sas_assignments():
    response = (
        "Read /opt/acme/private.conf and /usr/local/private and /workspace/private. "
        "Also read /boot/grub/grub.cfg and /private/etc/hosts. "
        "Use ?sv=2024-01-01&sig=SUPERSECRET and code=AUTHCODE123."
    )

    sanitized = _sanitize_response_text(response)

    assert sanitized == (
        "Read <PATH> and <PATH> and <PATH>. "
        "Also read <PATH> and <PATH>. "
        "Use ?sv=2024-01-01&sig=[REDACTED] and code=[REDACTED]."
    )


def test_signed_url_response_remains_valid_after_runner_and_scorer(monkeypatch):
    response = "Use https://host/path?sig=SECRET&view=foundry."
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=_event_stream(response=response),
            stderr="",
        ),
    )

    raw_row = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )
    scored_row = score_result(raw_row)

    assert raw_row["response"] == "Use https://host/path?sig=[REDACTED]&view=foundry."
    assert scored_row["row_valid"] is True
    assert scored_row["response"] == raw_row["response"]


def test_oauth_query_and_fragment_credentials_are_redacted():
    response = (
        "Open https://host/callback?code=AUTHCODE123&client_secret=CLIENTSECRET123"
        "#access_token=header.payload.signature&view=foundry."
    )

    sanitized = _sanitize_response_text(response)

    for secret in ("AUTHCODE123", "CLIENTSECRET123", "header.payload.signature"):
        assert secret not in sanitized
    assert "code=[REDACTED]" in sanitized
    assert "client_secret=[REDACTED]" in sanitized
    assert "access_token=[REDACTED]&view=foundry." in sanitized


def test_url_userinfo_aliases_and_nested_fragment_credentials_are_redacted():
    response = (
        "Open https://user:password@host/path?x-api-key=APISECRET&subscription-key=AZURESECRET"
        "#/callback?code=AUTHCODE&client_secret=CLIENTSECRET."
    )

    sanitized = _sanitize_response_text(response)

    for secret in ("user:password", "APISECRET", "AZURESECRET", "AUTHCODE", "CLIENTSECRET"):
        assert secret not in sanitized
    assert "https://[REDACTED]@host/path" in sanitized
    assert "x-api-key=[REDACTED]" in sanitized
    assert "subscription-key=[REDACTED]" in sanitized
    assert "#/callback?code=[REDACTED]&client_secret=[REDACTED]." in sanitized


def test_quoted_url_values_assertions_and_encoded_tokens_are_redacted():
    response = (
        'Open https://host/path?token="URLSECRET"&client_assertion=header.payload.signature'
        '&code_verifier=VERIFIER&ref=ghp%5FENCODEDSECRET.'
    )

    sanitized = _sanitize_response_text(response)

    for secret in ("URLSECRET", "header.payload.signature", "VERIFIER", "ghp%5FENCODEDSECRET"):
        assert secret not in sanitized
    assert "token=[REDACTED]" in sanitized
    assert "client_assertion=[REDACTED]" in sanitized
    assert "code_verifier=[REDACTED]" in sanitized
    assert "ref=[REDACTED]" in sanitized


def test_malformed_url_userinfo_is_redacted_before_url_parsing():
    response = "See https://user:URLSECRET@[broken/path"

    sanitized = _sanitize_response_text(response)

    assert "URLSECRET" not in sanitized
    assert "https://[REDACTED]@" in sanitized


def test_url_benign_parameter_values_and_fragments_still_redact_embedded_tokens():
    response = (
        "Open https://host/path?ref=ghp_QUERYSECRET123"
        "#section=ghp_FRAGMENTSECRET123."
    )

    sanitized = _sanitize_response_text(response)

    assert "ghp_QUERYSECRET123" not in sanitized
    assert "ghp_FRAGMENTSECRET123" not in sanitized
    assert "ref=[REDACTED]" in sanitized
    assert "#section=[REDACTED]." in sanitized


def test_strict_and_alias_credentials_are_redacted_without_corrupting_redaction_marker():
    response = (
        "jwt=headerheader.payloadpayload.signaturesig "
        "pat=PATSECRET sas=SASSECRET SharedAccessKey=SHAREDSECRET AccountKey=ACCOUNTSECRET "
        "token=[REDACTED] token=[REDACTED]LEAK"
    )

    sanitized = _sanitize_response_text(response)

    for secret in (
        "headerheader.payloadpayload.signaturesig",
        "PATSECRET",
        "SASSECRET",
        "SHAREDSECRET",
        "ACCOUNTSECRET",
        "[REDACTED]LEAK",
    ):
        assert secret not in sanitized
    assert "token=[REDACTED]" in sanitized


def test_malformed_https_url_fails_closed_without_crashing():
    response = "See https://[broken/path?token=LEAKME"

    sanitized = _sanitize_response_text(response)

    assert "LEAKME" not in sanitized
    assert "token=[REDACTED]" in sanitized


def test_noncredential_code_assignments_remain_usable():
    response = "status_code=404 errorCode=InvalidRequest language_code=en-US"

    assert _sanitize_response_text(response) == response


def test_secrets_in_https_path_components_are_redacted():
    response = "See https://host/token=LEAKME and https://host/github_pat_ABCDEF123456."

    sanitized = _sanitize_response_text(response)

    assert "LEAKME" not in sanitized
    assert "github_pat_ABCDEF123456" not in sanitized
    assert "https://host/token=[REDACTED]" in sanitized
    assert "https://host/[REDACTED]." in sanitized


def test_https_path_encoding_is_preserved_when_no_secret_is_present():
    response = "See https://host/a%2Fb+c."

    assert _sanitize_response_text(response) == response


def test_percent_encoded_credentials_and_local_paths_are_detected_recursively():
    response = (
        "Account %41ccountKey=ACCOUNTSECRET123 "
        "JWT jwt=headerheader%252Epayloadpayload%252Esignaturesig "
        "Path %252Fhome%252Falice%252Fsecret.txt "
        "Safe https://host/a%2Fb+c."
    )

    sanitized = _sanitize_response_text(response)

    for leaked in ("ACCOUNTSECRET123", "headerheader", "payloadpayload", "signaturesig", "secret.txt"):
        assert leaked not in sanitized
    assert "<PATH>" in sanitized
    assert "https://host/a%2Fb+c." in sanitized


def test_four_plus_layer_encoded_authorization_redacts_and_budget_exhaustion_fails_closed(monkeypatch):
    encoded = "Authorization=CustomScheme opaque-value"
    for _ in range(5):
        encoded = urllib.parse.quote_plus(encoded)
    response = f"upstream={encoded}"

    sanitized = _sanitize_response_text(response)
    assert "opaque-value" not in sanitized
    assert "[REDACTED]" in sanitized

    monkeypatch.setattr(run_docs_eval, "MAX_ENCODED_DECODE_ITERATIONS", 1)
    exhausted = _sanitize_response_text(response)
    assert encoded not in exhausted
    assert exhausted == "[REDACTED]"


@pytest.mark.parametrize(
    "response",
    [
        "Authorization%3A CustomScheme opaque-value",
        "%41uthorization=CustomScheme opaque-value",
    ],
)
def test_partially_encoded_authorization_redacts_complete_line(response):
    assert _sanitize_response_text(response) == "[REDACTED]"


@pytest.mark.parametrize(
    "response",
    [
        "Authorization%3A\n opaque-value",
        "Authorization%253A\r\n \r\n nonce=LEAKME",
        'upstream={%22Authorization%22%3A\n opaque-value}',
    ],
)
def test_folded_encoded_authorization_redacts_logical_header_block(response):
    sanitized = _sanitize_response_text(response)

    assert sanitized == "[REDACTED]\n" or sanitized == "[REDACTED]\r\n"
    assert "opaque-value" not in sanitized
    assert "LEAKME" not in sanitized


def test_encoded_credentials_and_paths_are_redacted_in_diagnostic_channels(monkeypatch):
    leaked = "token%3DSECRETVALUE %252Fhome%252Falice%252Fsecret.txt"
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            1,
            stdout="not-json",
            stderr=leaked,
        ),
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
        assert "SECRETVALUE" not in persisted
        assert "secret.txt" not in persisted
        assert "[REDACTED]" in persisted
        assert "<PATH>" in persisted


def test_markdown_os_paths_are_redacted_while_documentation_routes_survive():
    response = (
        "Read [passwd](/etc/passwd) and [env](/home/runner/work/repo/.env). "
        "Keep [agents](/concepts/agents)."
    )

    sanitized = _sanitize_response_text(response)

    assert sanitized == "Read [passwd](<PATH>) and [env](<PATH>). Keep [agents](/concepts/agents)."


def test_select_servers_rejects_unknown_mixed_and_empty_plural_selection():
    with pytest.raises(ValueError, match="unknown server"):
        select_servers(None, ["unknown"])
    with pytest.raises(ValueError, match="unknown server"):
        select_servers(None, ["foundry-docs", "unknown"])
    with pytest.raises(ValueError, match="requires at least one"):
        select_servers(None, [])
    with pytest.raises(ValueError, match="cannot be used together"):
        select_servers("foundry-docs", ["foundry-docs-vnext"])


@pytest.mark.parametrize(
    "extra_args",
    [
        ["--servers", "unknown", "--dry-run"],
        ["--servers", "foundry-docs", "unknown", "--dry-run"],
        ["--servers", "--dry-run"],
        ["--servers", "unknown"],
        ["--models", "--dry-run"],
    ],
)
def test_cli_plural_server_selection_fails_nonzero_before_execution(tmp_path, extra_args):
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parents[1] / "scripts" / "run_docs_eval.py"),
            "--scenarios",
            str(Path(__file__).parents[1] / "tests" / "docs_eval_scenarios.json"),
            "--output-dir",
            str(tmp_path),
            *extra_args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "Error:" in proc.stderr
    assert list(tmp_path.glob("run-*.json")) == []


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


def test_canonical_mcp_servers_loaded_diagnostic_scores_as_valid(monkeypatch):
    stdout = "\n".join([
        json.dumps({
            "type": "session.mcp_servers_loaded",
            "ephemeral": True,
            "data": {
                "servers": [
                    {
                        "name": "foundry_docs",
                        "status": "connected",
                        "source": "user",
                        "transport": "stdio",
                    }
                ]
            },
        }),
        json.dumps({
            "type": "tool.execution_start",
            "data": {"toolCallId": "call-1", "toolName": "foundry_docs-search_docs"},
        }),
        json.dumps({
            "type": "tool.execution_complete",
            "data": {"toolCallId": "call-1", "success": True},
        }),
        json.dumps({"type": "assistant.message", "data": {"content": "trusted answer"}}),
        json.dumps({"type": "result", "exitCode": 0}),
    ])
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

    assert raw_row["status"] == "success"
    assert raw_row["diagnostics"]["events"][0]["event_type"] == "session.mcp_servers_loaded"
    assert scored_row["row_valid"] is True
    assert scored_row["status"] == "success"


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
        "Authorization: Digest username=alice,\r\n nonce=LEAKME",
        "Authorization=Digest username=alice,\n\tnonce=LEAKME",
        "Authorization: Digest username=alice,\r\n \r\n nonce=LEAKME",
    ],
)
def test_folded_authorization_values_redact_indented_continuations(raw):
    sanitized, _truncated = _sanitize_text(raw)

    assert sanitized in {"Authorization: [REDACTED]", "Authorization=[REDACTED]"}
    assert "LEAKME" not in sanitized
    assert "nonce" not in sanitized


@pytest.mark.parametrize(
    "raw",
    [
        "Authorization=Basic credential",
        "Authorization=CustomScheme opaque credential",
        "Authorization=Digest username=alice, realm=private, nonce=SECRET",
        '"Authorization"=Digest username=alice, realm=private, nonce=SECRET',
        '"Authorization": Digest username=alice, realm=private, nonce=SECRET',
        r'{\"Authorization\":Digest username=alice, realm=private, nonce=SECRET}',
        'Authorization=Digest username="alice}", nonce="LEAKME"',
    ],
)
def test_unquoted_authorization_assignment_redacts_complete_value(raw):
    sanitized, _truncated = _sanitize_text(raw)

    assert sanitized == "Authorization=[REDACTED]"


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


@pytest.mark.parametrize(
    "response",
    [
        r'upstream={\\"Authorization\\":CustomScheme opaque-value}',
        r'upstream={\\\\\"Authorization\\\\\":Digest username=alice, nonce=LEAKME}',
        r'upstream={\\\\\\\\\"Authorization\\\\\\\\\":Digest username=alice, nonce=LEAKME}',
    ],
)
def test_deeply_escaped_authorization_is_clean_in_valid_raw_and_scored_rows(monkeypatch, response):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd,
            0,
            stdout=_event_stream(response=response),
            stderr=response,
        ),
    )

    raw_row = run_single_eval(
        SCENARIO,
        "foundry-docs",
        MCP_SERVERS["foundry-docs"],
        "model-1",
    )
    scored_row = score_result(raw_row)

    assert raw_row["status"] == "success"
    assert scored_row["row_valid"] is True
    for row in (raw_row, scored_row):
        persisted = json.dumps(row)
        assert "opaque-value" not in persisted
        assert "LEAKME" not in persisted
        assert "[REDACTED]" in persisted


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


def test_multiple_real_size_tool_results_over_128kb_remain_valid(monkeypatch):
    events = []
    for index in range(3):
        tool_call_id = f"call-{index}"
        events.append({
            "type": "tool.execution_start",
            "data": {
                "toolCallId": tool_call_id,
                "toolName": "foundry_docs-search_docs",
            },
        })
        completion = {
            "type": "tool.execution_complete",
            "data": {
                "toolCallId": tool_call_id,
                "success": True,
                "result": {"content": [{"type": "text", "text": ""}]},
            },
        }
        base_size = len(json.dumps(completion, separators=(",", ":")).encode())
        completion["data"]["result"]["content"][0]["text"] = "x" * (57_000 - base_size)
        events.append(completion)
    events.extend([
        {"type": "assistant.message", "data": {"content": "trusted answer"}},
        {"type": "result", "exitCode": 0},
    ])
    stdout = "\n".join(json.dumps(event, separators=(",", ":")) for event in events)
    assert 128_000 < len(stdout.encode()) < run_docs_eval.MAX_STDOUT_PARSE_BYTES
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


def test_total_stdout_budget_still_fails_closed():
    event = json.dumps({
        "type": "session.mcp_servers_loaded",
        "data": {"message": "x" * 63_000},
    }, separators=(",", ":"))
    assert len(event.encode()) < run_docs_eval.MAX_STDOUT_LINE_BYTES
    line_count = run_docs_eval.MAX_STDOUT_PARSE_BYTES // len((event + "\n").encode()) + 1
    stdout = "\n".join([event] * line_count)

    parsed = parse_event_stream(stdout)

    assert parsed["stdout_input_truncated"] is True
    assert f"stdout exceeds {run_docs_eval.MAX_STDOUT_PARSE_BYTES} byte pre-parse limit" in parsed["parse_error"]
    assert parsed["response"] == ""


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
    "invalid_value",
    [
        r"token=LEAKME C:\Users\Alice\private",
        float("nan"),
        float("inf"),
        -1,
    ],
)
def test_usage_metrics_discard_invalid_values_and_remain_strict_json(invalid_value):
    stdout = json.dumps({
        "type": "result",
        "exitCode": 0,
        "usage": {
            "premiumRequests": invalid_value,
            "totalApiDurationMs": invalid_value,
            "sessionDurationMs": invalid_value,
        },
    })

    parsed = parse_event_stream(stdout)

    assert parsed["premium_requests"] is None
    assert parsed["api_duration_ms"] is None
    assert parsed["session_duration_ms"] is None
    assert "must be a finite non-negative number" in parsed["parse_error"]
    assert "LEAKME" not in parsed["parse_error"]
    assert "Alice" not in parsed["parse_error"]
    json.dumps(parsed, allow_nan=False)


@pytest.mark.parametrize("usage", [None, False, [], "", 0])
def test_usage_rejects_every_falsy_non_object_value(usage):
    parsed = parse_event_stream(json.dumps({
        "type": "result",
        "exitCode": 0,
        "usage": usage,
    }))

    assert "result usage must be a JSON object" in parsed["parse_error"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("premium_requests", float("nan")),
        ("api_duration_ms", float("inf")),
        ("session_duration_ms", -1),
    ],
)
def test_scorer_rejects_nonfinite_usage_metrics(field, value):
    row = _raw_row()
    row[field] = value

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored[field] is None
    json.dumps(scored, allow_nan=False)


def test_cumulative_output_tokens_cannot_exceed_metric_bound():
    stdout = "\n".join([
        json.dumps({
            "type": "assistant.message",
            "data": {"content": "first", "outputTokens": 10**15},
        }),
        json.dumps({
            "type": "assistant.message",
            "data": {"content": "second", "outputTokens": 10**15},
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ])

    parsed = parse_event_stream(stdout)

    assert parsed["output_tokens"] == 10**15
    assert "cumulative output token count exceeds" in parsed["parse_error"]


@pytest.mark.parametrize("output_tokens", [None, False, "", 0.0])
def test_output_token_count_rejects_explicit_non_integer_values(output_tokens):
    parsed = parse_event_stream("\n".join([
        json.dumps({
            "type": "assistant.message",
            "data": {"content": "answer", "outputTokens": output_tokens},
        }),
        json.dumps({"type": "result", "exitCode": 0}),
    ]))

    assert parsed["output_tokens"] == 0
    assert "output token count must be a non-negative integer" in parsed["parse_error"]


def test_usage_metrics_reject_integer_beyond_aggregation_bound():
    parsed = parse_event_stream(json.dumps({
        "type": "result",
        "exitCode": 0,
        "usage": {"premiumRequests": 10**1_000},
    }))

    assert parsed["premium_requests"] is None
    assert "must be a finite non-negative number" in parsed["parse_error"]


def test_nonfinite_nested_diagnostic_value_is_normalized_for_strict_json():
    stdout = "\n".join([
        json.dumps({
            "type": "session.error",
            "data": {"errorType": "query", "message": "failed", "extra": float("nan")},
        }),
        json.dumps({"type": "result", "exitCode": 1}),
    ])

    parsed = parse_event_stream(stdout)

    assert parsed["diagnostic_events"][0]["data"]["extra"] is None
    json.dumps(parsed, allow_nan=False)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, 10**1_000])
def test_scorer_rejects_nonfinite_response_time(value):
    row = _raw_row()
    row["response_time_seconds"] = value

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored["operational"]["response_time_seconds"] is None
    assert scored["response_time_seconds"] is None
    json.dumps(scored, allow_nan=False)


@pytest.mark.parametrize("field", ["turns", "tool_calls", "tool_errors", "output_tokens"])
def test_invalid_count_metrics_are_removed_from_strict_scored_output(field):
    row = _raw_row()
    row[field] = float("nan")

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored[field] is None
    json.dumps(scored, allow_nan=False)


@pytest.mark.parametrize("field", ["turns", "tool_calls", "tool_errors", "output_tokens"])
def test_oversized_count_metrics_are_removed_from_operational_output(field):
    row = _raw_row()
    row[field] = 10**10_000

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored[field] is None
    assert scored["operational"][field] is None
    json.dumps(scored, allow_nan=False)


def test_oversized_source_config_and_metadata_counts_are_bounded():
    row = _raw_row()
    row["source_config_count"] = 10**10_000
    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored["source_config_count"] == 0
    json.dumps(scored, allow_nan=False)

    metadata = {
        "run_id": "run-1",
        "servers": ["foundry-docs"],
        "models": ["model-1"],
        "total_evaluations": 10**10_000,
    }
    # The scorer's metadata projection drops the oversized count before strict output.
    projected = _sanitize_metadata(metadata)
    assert "total_evaluations" not in projected
    json.dumps(projected, allow_nan=False)


def test_derived_tool_error_total_is_bounded():
    first = score_result(_raw_row())
    second = score_result(_raw_row(scenario_id="scenario-2"))
    first["operational"]["tool_errors"] = 10**15
    second["operational"]["tool_errors"] = 10**15

    aggregates = aggregate_scores([first, second])
    operational = aggregates["operational_metrics"]["foundry-docs"]

    assert operational["total_tool_errors"] is None
    assert operational["tool_errors_overflow"] is True
    json.dumps(aggregates, allow_nan=False)


@pytest.mark.parametrize("field", ["premium_requests", "api_duration_ms", "session_duration_ms"])
def test_scorer_rejects_usage_metric_above_bound(field):
    row = _raw_row()
    row[field] = 10**15 + 1

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert scored[field] is None
    json.dumps(scored, allow_nan=False)


def test_usage_metrics_accept_large_non_negative_integer_without_float_overflow():
    large_integer = 10**15
    stdout = json.dumps({
        "type": "result",
        "exitCode": 0,
        "usage": {"premiumRequests": large_integer},
    })

    parsed = parse_event_stream(stdout)

    assert parsed["premium_requests"] == large_integer
    assert parsed["parse_error"] is None
    json.dumps(parsed, allow_nan=False)

    invalid_row = {"premium_requests": large_integer}
    scored = score_result(invalid_row)
    assert scored["row_valid"] is False
    assert scored["premium_requests"] == large_integer
    json.dumps(scored, allow_nan=False)


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


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.pop("rubric"),
        lambda row: row.update({"rubric": {"must_mention": [], "quality_criteria": [], "expected_docs": []}}),
        lambda row: row.update({"rubric": {**row["rubric"], "must_mention": ["different"]}}),
        lambda row: row.update({"question": "different question"}),
        lambda row: row.update({"category": "different-category"}),
    ],
)
def test_scorer_rejects_missing_empty_or_mismatched_trusted_scenario_fields(mutation):
    row = _raw_row()
    mutation(row)
    trusted = validate_trusted_scenarios([{
        "id": SCENARIO["id"],
        "question": SCENARIO["question"],
        "category": SCENARIO["category"],
        "rubric": SCENARIO["rubric"],
    }])

    scored = score_result(row, trusted)

    assert scored["row_valid"] is False
    assert scored["status"] == "invalid"
    assert scored["response"] == ""
    assert scored["scores"]["completeness"] == 0.0


@pytest.mark.parametrize(
    "scenarios",
    [
        [{"id": "x", "question": "q", "category": "c", "rubric": {
            "must_mention": [], "quality_criteria": ["q"], "expected_docs": ["d"]
        }}],
        [{"id": "x", "question": "", "category": "c", "rubric": SCENARIO["rubric"]}],
        [{"id": "x", "question": "q", "category": "c", "rubric": {"must_mention": ["x"]}}],
        [{"id": " ", "question": " ", "category": " ", "rubric": {
            "must_mention": [" "], "quality_criteria": [" "], "expected_docs": [" "]
        }}],
    ],
)
def test_required_scenario_definitions_require_complete_trusted_fields(scenarios):
    with pytest.raises(ValueError):
        validate_trusted_scenarios(scenarios)


def test_trusted_scenario_ids_reject_sanitization_collisions():
    scenarios = [
        {
            "id": "token=abc",
            "question": "question one",
            "category": "category",
            "rubric": SCENARIO["rubric"],
        },
        {
            "id": "token=[REDACTED]",
            "question": "question two",
            "category": "category",
            "rubric": SCENARIO["rubric"],
        },
    ]

    with pytest.raises(ValueError, match="canonical form"):
        validate_trusted_scenarios(scenarios)


def test_trusted_scenario_validation_errors_do_not_leak_raw_id():
    scenario_id = r"token=LEAKME C:\Users\Alice\private"
    scenarios = [{
        "id": scenario_id,
        "question": "question",
        "category": "category",
        "rubric": SCENARIO["rubric"],
    }]

    with pytest.raises(ValueError) as exc_info:
        validate_trusted_scenarios(scenarios)

    error = str(exc_info.value)
    assert "LEAKME" not in error
    assert "Alice" not in error
    assert "private" not in error
    assert "token=[REDACTED]" in error
    assert "<PATH>" in error


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


def test_deep_diagnostic_identifier_nesting_fails_closed_without_recursion_error():
    nested: object = {"toolCallId": "safe-call"}
    for _ in range(995):
        nested = {"child": nested}
    row = _raw_row()
    row["diagnostics"]["events"] = [{"event_type": "status", "data": nested}]

    scored = score_result(row)

    assert scored["row_valid"] is False
    assert "exceeds maximum diagnostic nesting depth" in scored["failure_reason"]


def test_wide_diagnostic_identifier_mapping_is_bounded_lazily():
    row = _raw_row()
    row["diagnostics"]["events"] = [{
        "event_type": "status",
        "data": {f"field-{index}": "value" for index in range(100_000)},
    }]

    started = time.perf_counter()
    scored = score_result(row)
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0
    assert scored["row_valid"] is False
    assert "contains more than 20 fields" in scored["failure_reason"]


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


def test_non_azure_server_cannot_spoof_azure_evidence():
    spoofed = _raw_row(server="microsoft-learn")
    spoofed["azure_required"] = True
    spoofed["azure_live_query_proven"] = True
    spoofed["selected_source_config"]["azure_required"] = True

    scored = score_result(spoofed)
    publication = validate_required_matrix(
        [scored],
        scenario_ids=["scenario-1"],
        servers=["microsoft-learn"],
        models=["model-1"],
        azure_required_servers={"microsoft-learn"},
    )

    assert scored["row_valid"] is False
    assert scored["status"] == "invalid"
    assert scored["response"] == ""
    assert publication["allowed"] is False
    assert publication["unsupported_azure_required_servers"] == ["microsoft-learn"]
    assert (
        "Azure-required server(s) do not support Azure evidence: microsoft-learn"
        in publication["failure_reasons"]
    )


def test_azure_required_server_must_be_in_required_matrix():
    valid = score_result(_raw_row())

    publication = validate_required_matrix(
        [valid],
        scenario_ids=["scenario-1"],
        servers=["foundry-docs"],
        models=["model-1"],
        azure_required_servers={"foundry-docs-vnext"},
    )

    assert publication["allowed"] is False
    assert publication["azure_required_outside_matrix"] == ["foundry-docs-vnext"]
    assert (
        "Azure-required server(s) are outside the required server matrix: foundry-docs-vnext"
        in publication["failure_reasons"]
    )


def test_azure_required_server_must_be_in_implicit_effective_matrix():
    valid = score_result(_raw_row())

    publication = validate_required_matrix(
        [valid],
        azure_required_servers={"foundry-docs-vnext"},
    )

    assert publication["allowed"] is False
    assert publication["azure_required_outside_matrix"] == ["foundry-docs-vnext"]


@pytest.mark.parametrize(
    "selectors",
    [
        {"scenario_ids": ["scenario-1"]},
        {"servers": ["foundry-docs"]},
        {"models": ["model-1"]},
        {"scenario_ids": ["scenario-1"], "servers": ["foundry-docs"]},
        {"servers": ["foundry-docs"], "models": ["model-1"]},
    ],
)
def test_required_matrix_rejects_partial_selector_combinations(selectors):
    valid = score_result(_raw_row())

    publication = validate_required_matrix([valid], **selectors)

    assert publication["allowed"] is False
    assert publication["partial_required_selectors"] is True
    assert (
        "required scenario, server, and model selectors must be supplied together"
        in publication["failure_reasons"]
    )


def test_required_matrix_rejects_omitted_selector_triple():
    valid = score_result(_raw_row())

    publication = validate_required_matrix([valid])

    assert publication["allowed"] is False
    assert publication["partial_required_selectors"] is True
    assert (
        "required scenario, server, and model selectors must be supplied together"
        in publication["failure_reasons"]
    )


@pytest.mark.parametrize(
    ("scenario_ids", "servers", "models", "empty_name"),
    [
        ([], [], [], "scenarios"),
        ([], ["foundry-docs"], ["model-1"], "scenarios"),
        (["scenario-1"], [], ["model-1"], "servers"),
        (["scenario-1"], ["foundry-docs"], [], "models"),
    ],
)
def test_required_matrix_rejects_explicit_empty_selector_collections(
    scenario_ids,
    servers,
    models,
    empty_name,
):
    publication = validate_required_matrix(
        [],
        scenario_ids=scenario_ids,
        servers=servers,
        models=models,
    )

    assert publication["allowed"] is False
    assert empty_name in publication["empty_required_selectors"]
    assert "required selector collection(s) must not be empty" in publication["failure_reasons"][-1]


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


@pytest.mark.parametrize(
    ("scenarios", "servers", "models", "message"),
    [
        ([], None, None, "scenarios must not be empty"),
        ([SCENARIO], {}, None, "servers must not be empty"),
        ([SCENARIO], None, [], "models must not be empty"),
    ],
)
def test_run_evaluation_rejects_explicit_empty_collections(scenarios, servers, models, message):
    with pytest.raises(ValueError, match=message):
        run_evaluation(scenarios, servers=servers, models=models)


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
        json.dumps([
            {
                "id": "scenario-1",
                "question": SCENARIO["question"],
                "category": SCENARIO["category"],
                "rubric": SCENARIO["rubric"],
            },
            {
                "id": "scenario-2",
                "question": SCENARIO["question"],
                "category": SCENARIO["category"],
                "rubric": SCENARIO["rubric"],
            },
        ]),
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


def test_baseline_comparison_blocks_missing_current_required_rows(tmp_path, capsys):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({
            "results": [
                _raw_row(scenario_id="scenario-1", server="foundry-docs", model="model-1"),
                _raw_row(scenario_id="scenario-2", server="foundry-docs", model="model-1"),
            ]
        }),
        encoding="utf-8",
    )
    current = {"results": [_raw_row(scenario_id="scenario-1", server="foundry-docs", model="model-1")]}

    exit_code = compare_results(
        current,
        str(baseline_path),
        _trusted_definitions("scenario-1", "scenario-2"),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Baseline comparison blocked" in captured.err
    assert "No regressions detected" not in captured.out


def test_baseline_comparison_blocks_invalid_current_required_row(tmp_path, capsys):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({"results": [_raw_row()]}),
        encoding="utf-8",
    )
    invalid = _raw_row()
    invalid["status"] = "invalid"
    invalid["passed"] = False
    invalid["response"] = ""
    invalid["response_present"] = False
    invalid["failure_reason"] = "invalid evidence"

    exit_code = compare_results(
        {"results": [invalid]},
        str(baseline_path),
        _trusted_definitions("scenario-1"),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Baseline comparison blocked" in captured.err
    assert "No regressions detected" not in captured.out


def test_baseline_comparison_rejects_invalid_baseline_matrix(tmp_path, capsys):
    invalid_baseline = _raw_row()
    invalid_baseline["status"] = "invalid"
    invalid_baseline["passed"] = False
    invalid_baseline["response"] = ""
    invalid_baseline["response_present"] = False
    invalid_baseline["failure_reason"] = "invalid baseline evidence"
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({"results": [invalid_baseline]}),
        encoding="utf-8",
    )

    exit_code = compare_results(
        {"results": [_raw_row()]},
        str(baseline_path),
        _trusted_definitions("scenario-1"),
    )

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "invalid baseline matrix" in captured.err
    assert "No regressions detected" not in captured.out


def test_baseline_comparison_requires_every_trusted_scenario_in_baseline(tmp_path, capsys):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({"results": [_raw_row(scenario_id="scenario-1")]}),
        encoding="utf-8",
    )

    exit_code = compare_results(
        {"results": [_raw_row(scenario_id="scenario-1")]},
        str(baseline_path),
        _trusted_definitions("scenario-1", "scenario-2"),
    )

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "invalid baseline matrix" in captured.err
    assert "No regressions detected" not in captured.out


@pytest.mark.parametrize("baseline", [[], {"results": None}, {"results": 123}])
def test_baseline_comparison_rejects_malformed_baseline_shape(tmp_path, capsys, baseline):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    exit_code = compare_results(
        {"results": [_raw_row()]},
        str(baseline_path),
        _trusted_definitions("scenario-1"),
    )

    assert exit_code == 2
    assert "must be an object with a results array" in capsys.readouterr().err


def test_cli_main_baseline_comparison_fails_for_missing_required_current_row(
    tmp_path,
    monkeypatch,
    capsys,
):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({
            "results": [
                _raw_row(scenario_id="scenario-1"),
                _raw_row(scenario_id="scenario-2"),
            ]
        }),
        encoding="utf-8",
    )
    output_dir = tmp_path / "results"
    args = argparse.Namespace(
        scenarios=str(Path(__file__).parents[1] / "tests" / "docs_eval_scenarios.json"),
        output_dir=str(output_dir),
        server="foundry-docs",
        servers=None,
        models=["model-1"],
        timeout=3,
        require_azure=False,
        dry_run=False,
        baseline=str(baseline_path),
    )
    monkeypatch.setattr(run_docs_eval, "_parse_args", lambda: args)
    monkeypatch.setattr(
        run_docs_eval,
        "load_scenarios",
        lambda path: [
            SCENARIO,
            {**SCENARIO, "id": "scenario-2"},
        ],
    )
    monkeypatch.setattr(
        run_docs_eval,
        "run_evaluation",
        lambda scenarios, servers, models, timeout, require_azure: {
            "metadata": {
                "run_id": "current-run",
                "timestamp": "2026-07-29T00:00:00Z",
                "scenarios_count": 1,
                "servers": ["foundry-docs"],
                "models": ["model-1"],
                "total_evaluations": 1,
                "completed": 1,
            },
            "results": [_raw_row(scenario_id="scenario-1")],
        },
    )

    with pytest.raises(SystemExit) as exc_info:
        run_docs_eval.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Baseline comparison blocked" in captured.err
    assert "No regressions detected" not in captured.out
