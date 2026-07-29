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
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote_plus, urlsplit, urlunsplit

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
MAX_DIAGNOSTIC_EVENTS = 20
MAX_DIAGNOSTIC_EVENTS_CHARS = 50_000
MAX_DIAGNOSTIC_TEXT = 2_000
MAX_RESPONSE_TEXT = 50_000
MAX_STDOUT_EXCERPT = 12_000
MAX_STDERR_EXCERPT = 4_000
MAX_STDOUT_PARSE_BYTES = 128_000
MAX_STDOUT_PARSE_LINES = 500
MAX_STDOUT_LINE_BYTES = 64_000
MAX_IDENTIFIER_TEXT = 256
MAX_USAGE_METRIC = 10**15
MAX_ENCODED_TOKEN_BYTES = 8_192
MAX_ENCODED_DECODE_ITERATIONS = 8
MAX_ENCODED_DECODE_SECONDS = 0.02
_SECRET_KEY_PATTERN = re.compile(r"(?:api[_-]?key|authorization|credential|password|secret|token)", re.I)
_AUTHORIZATION_HEADER_PATTERN = re.compile(
    r"(?im)(authorization\s*:\s*)[^\r\n]+(?:\r?\n[ \t]+[^\r\n]*)*"
)
_AUTHORIZATION_ASSIGNMENT_PATTERN = re.compile(
    r"""(?imx)
    \{?
    (?:
        (?:\\)*["']?authorization(?:\\)*["']?\s*=\s*
        | (?:\\)*["']authorization(?:\\)*["']\s*:\s*
    )
    [^\r\n]+(?:\r?\n[ \t]+[^\r\n]*)*
    """
)
_SERIALIZED_AUTHORIZATION_KEY_PATTERN = re.compile(
    r"(?i)(?:\\?[\"'])authorization(?:\\?[\"'])\s*[:=]\s*"
)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"\b(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]+\b"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    (?P<prefix>
        ["']?[A-Z0-9_-]{0,128}
        (?:
            api[_-]?key|account[_-]?key|authorization|credential|password|secret|token
            |sig(?:nature)?|client[_-]?secret|access[_-]?token|refresh[_-]?token|id[_-]?token
        )
        ["']?\s*[:=]\s*
    )
    (?:
        "(?P<double>[^"]*)"
        | '(?P<single>[^']*)'
        | (?P<bare>[^\s,;}&?!\)#]+)
    )
    """
)
_OAUTH_CODE_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?<![A-Z0-9_-])(?P<prefix>code\s*[:=]\s*)(?P<bare>[^\s,;}&?!\)#]+)"
)
_EXACT_SECRET_ALIAS_PATTERN = re.compile(
    r"(?i)(?<![A-Z0-9_-])(?P<prefix>(?:pat|sas|sharedaccesskey)\s*[:=]\s*)(?P<bare>[^\s,;}&?!\)#]+)"
)
_ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"(?i)(?:\\\\|//)[^\\/\r\n]+[\\/][^,\r\n;\"']+"),
    re.compile(r"(?i)\b[A-Z]:[\\/][^,\r\n;\"']+"),
    re.compile(r"(?<![:/\w])/(?!/)[^,\r\n;\"']+"),
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


def _coerce_process_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _sanitize_text(value: str, max_chars: int = MAX_DIAGNOSTIC_TEXT) -> tuple[str, bool]:
    """Redact common secrets and local paths, then bound diagnostic text."""
    pre_redaction_limit = max_chars * 4
    truncated = len(value) > pre_redaction_limit
    sanitized = value[:pre_redaction_limit]
    sanitized = _redact_encoded_sensitive_tokens(sanitized)
    path_replacements = (
        (str(PROJECT_ROOT), "<PROJECT_ROOT>"),
        (str(Path.home()), "<HOME>"),
        (tempfile.gettempdir(), "<TEMP>"),
    )
    for path, replacement in path_replacements:
        if path:
            sanitized = re.sub(re.escape(path), replacement, sanitized, flags=re.I)

    sanitized = _redact_serialized_authorization(sanitized)
    sanitized = _AUTHORIZATION_HEADER_PATTERN.sub(r"\1[REDACTED]", sanitized)
    sanitized = _AUTHORIZATION_ASSIGNMENT_PATTERN.sub("Authorization=[REDACTED]", sanitized)
    sanitized = _SECRET_VALUE_PATTERNS[0].sub("[REDACTED]", sanitized)
    sanitized = _SECRET_VALUE_PATTERNS[1].sub(r"\1[REDACTED]", sanitized)
    sanitized = _SECRET_VALUE_PATTERNS[2].sub("[REDACTED]", sanitized)
    sanitized = _redact_secret_assignments(sanitized)
    for pattern in _ABSOLUTE_PATH_PATTERNS:
        sanitized = pattern.sub("<PATH>", sanitized)

    if len(sanitized) > max_chars:
        truncated = True
        sanitized = sanitized[:max_chars] + "...[truncated]"
    return sanitized, truncated


def _redact_serialized_authorization(value: str) -> str:
    """Redact quoted Authorization values, including double-escaped JSON strings."""
    cursor = 0
    while match := _SERIALIZED_AUTHORIZATION_KEY_PATTERN.search(value, cursor):
        value_start = match.end()
        opening_slashes = 0
        if value_start < len(value) and value[value_start] == "\\":
            opening_slashes = 1
            value_start += 1
        if value_start >= len(value) or value[value_start] not in {'"', "'"}:
            cursor = match.end()
            continue

        quote = value[value_start]
        value_content_start = value_start + 1
        scan = value_content_start
        while scan < len(value):
            if value[scan] == quote:
                slash_count = 0
                slash_index = scan - 1
                while slash_index >= value_content_start and value[slash_index] == "\\":
                    slash_count += 1
                    slash_index -= 1
                if slash_count == opening_slashes:
                    value = value[:value_content_start] + "[REDACTED]" + value[scan:]
                    cursor = value_content_start + len("[REDACTED]") + 1
                    break
            if value[scan] in "\r\n":
                value = value[:value_content_start] + "[REDACTED]" + value[scan:]
                cursor = value_content_start + len("[REDACTED]")
                break
            scan += 1
        else:
            value = value[:value_content_start] + "[REDACTED]"
            cursor = len(value)
    return value


def _redact_secret_assignments(value: str) -> str:
    def redact(match: re.Match) -> str:
        trailing = ""
        bare = match.groupdict().get("bare")
        secret_value = bare or match.groupdict().get("double") or match.groupdict().get("single") or ""
        if secret_value == "[REDACTED]":
            return match.group(0)
        if bare:
            while bare.endswith("."):
                trailing += "."
                bare = bare[:-1]
        return f"{match.group('prefix')}[REDACTED]{trailing}"

    value = _SECRET_ASSIGNMENT_PATTERN.sub(redact, value)
    value = _OAUTH_CODE_ASSIGNMENT_PATTERN.sub(redact, value)
    return _EXACT_SECRET_ALIAS_PATTERN.sub(redact, value)


def _sanitize_diagnostic_value(value: object, *, depth: int = 0) -> object:
    if depth >= 4:
        return "[truncated-depth]"
    if isinstance(value, dict):
        sanitized = {}
        for index, (key, child) in enumerate(value.items()):
            if index >= 20:
                sanitized["_truncated_fields"] = True
                break
            raw_key_text = str(key)
            key_text = _sanitize_text(raw_key_text)[0]
            lowered_key = key_text.casefold()
            if lowered_key in {"arguments", "input", "request", "headers", "env", "environment"}:
                sanitized[key_text] = "[OMITTED]"
                continue
            sanitized[key_text] = (
                "[REDACTED]"
                if _SECRET_KEY_PATTERN.search(raw_key_text)
                else _sanitize_diagnostic_value(child, depth=depth + 1)
            )
        return sanitized
    if isinstance(value, list):
        sanitized_items = [_sanitize_diagnostic_value(item, depth=depth + 1) for item in value[:20]]
        if len(value) > 20:
            sanitized_items.append("[truncated-items]")
        return sanitized_items
    if isinstance(value, str):
        return _sanitize_text(value)[0]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _sanitize_text(str(value))[0]


def _sanitize_identifier(value: object) -> str:
    return _sanitize_text(str(value), max_chars=MAX_IDENTIFIER_TEXT)[0]


def _sanitize_response_text(value: str) -> str:
    """Sanitize answer text without treating root-relative documentation links as local paths."""
    pre_redaction_limit = MAX_RESPONSE_TEXT * 4
    sanitized = value[:pre_redaction_limit]
    sanitized = _redact_encoded_sensitive_tokens(sanitized)
    sanitized = re.sub(
        r"(?i)(https?://)[^/\s@]+@",
        r"\1redacted-user@",
        sanitized,
    )
    sanitized = _redact_serialized_authorization(sanitized)
    sanitized = _AUTHORIZATION_HEADER_PATTERN.sub(r"\1[REDACTED]", sanitized)
    sanitized = _AUTHORIZATION_ASSIGNMENT_PATTERN.sub("Authorization=[REDACTED]", sanitized)
    sanitized = _SECRET_VALUE_PATTERNS[0].sub("[REDACTED]", sanitized)
    sanitized = _SECRET_VALUE_PATTERNS[1].sub(r"\1[REDACTED]", sanitized)
    sanitized = _SECRET_VALUE_PATTERNS[2].sub("[REDACTED]", sanitized)
    sanitized = _redact_secret_assignments(sanitized)
    protected_links: list[str] = []

    def protect_link(match: re.Match) -> str:
        raw_link = match.group(0)
        link = "<PATH>" if _RESPONSE_LOCAL_PATH_START.match(raw_link) else _sanitize_link_target(raw_link)
        if len(link) > 2_048:
            link = link[:2_048] + "...[truncated]"
        protected_links.append(link)
        return f"__ROOT_DOC_LINK_{len(protected_links) - 1}__"

    sanitized = re.sub(r"(?<=\]\()/(?!/)[^)\r\n]+(?=\))", protect_link, sanitized)
    sanitized = re.sub(r"https?://[^\s<>'\")]+", protect_link, sanitized, flags=re.I)
    sanitized = re.sub(
        r"(?<![:/\w~}%])/(?!/|home(?:/|\b)|tmp(?:/|\b)|var(?:/|\b)|etc(?:/|\b)|root(?:/|\b)|Users(?:/|\b)"
        r"|usr(?:/|\b)|opt(?:/|\b)|mnt(?:/|\b)|srv(?:/|\b)|bin(?:/|\b)|sbin(?:/|\b)|lib(?:64)?(?:/|\b)"
        r"|run(?:/|\b)|dev(?:/|\b)|proc(?:/|\b)|sys(?:/|\b)|workspace(?:/|\b)|app(?:/|\b)|data(?:/|\b)"
        r"|boot(?:/|\b)|private(?:/|\b)|media(?:/|\b))"
        r"[^\s,;!)]+",
        protect_link,
        sanitized,
        flags=re.I,
    )
    sanitized = _redact_response_local_paths(sanitized)
    for index, link in enumerate(protected_links):
        sanitized = sanitized.replace(f"__ROOT_DOC_LINK_{index}__", link)
    sanitized = sanitized.replace("https://redacted-user@", "https://[REDACTED]@")

    if len(sanitized) > MAX_RESPONSE_TEXT:
        sanitized = sanitized[:MAX_RESPONSE_TEXT] + "...[truncated]"
    return sanitized


def _redact_encoded_sensitive_tokens(value: str) -> str:
    encoded_token = re.compile(r"\S*%[0-9A-Fa-f]{2}\S*")
    lines = value.splitlines(keepends=True)
    redacted_lines = []
    index = 0
    while index < len(lines):
        line = lines[index]
        decoded = _bounded_stable_decode(line.rstrip("\r\n"))
        redacted_lines.append(_redact_encoded_authorization_line(line))
        if decoded is not None:
            key_only = bool(
                re.search(
                    r"""(?ix)\{?(?:\\)*["']?authorization(?:\\)*["']?\s*[:=]\s*$""",
                    decoded,
                )
            )
            if key_only:
                redacted_lines[-1] = "[REDACTED]" + line[len(line.rstrip("\r\n")):]
                index += 1
                while index < len(lines) and lines[index].startswith((" ", "\t")):
                    index += 1
                continue
        index += 1
    value = "".join(redacted_lines)

    def inspect(match: re.Match) -> str:
        original = match.group(0)
        trailing = ""
        core = original
        while core and core[-1] in ".,;!?)]":
            trailing = core[-1] + trailing
            core = core[:-1]
        if len(core.encode("utf-8", errors="replace")) > MAX_ENCODED_TOKEN_BYTES:
            return "[REDACTED]" + trailing
        decoded = core
        deadline = time.monotonic() + MAX_ENCODED_DECODE_SECONDS
        stable = False
        for _ in range(MAX_ENCODED_DECODE_ITERATIONS):
            if time.monotonic() > deadline:
                return "[REDACTED]" + trailing
            next_value = unquote_plus(decoded)
            if len(next_value.encode("utf-8", errors="replace")) > MAX_ENCODED_TOKEN_BYTES:
                return "[REDACTED]" + trailing
            if next_value == decoded:
                stable = True
                break
            decoded = next_value
        if not stable:
            return "[REDACTED]" + trailing
        if decoded.lower().startswith(("http://", "https://")):
            sanitized_url = _sanitize_link_target(decoded)
            return sanitized_url + trailing if sanitized_url != decoded else original
        if _RESPONSE_LOCAL_PATH_START.search(decoded):
            return "<PATH>" + trailing
        sanitized_decoded = _redact_serialized_authorization(decoded)
        sanitized_decoded = _AUTHORIZATION_HEADER_PATTERN.sub(r"\1[REDACTED]", sanitized_decoded)
        sanitized_decoded = _AUTHORIZATION_ASSIGNMENT_PATTERN.sub("Authorization=[REDACTED]", sanitized_decoded)
        sanitized_decoded = _SECRET_VALUE_PATTERNS[0].sub("[REDACTED]", sanitized_decoded)
        sanitized_decoded = _SECRET_VALUE_PATTERNS[1].sub(r"\1[REDACTED]", sanitized_decoded)
        sanitized_decoded = _SECRET_VALUE_PATTERNS[2].sub("[REDACTED]", sanitized_decoded)
        sanitized_decoded = _redact_secret_assignments(sanitized_decoded)
        if sanitized_decoded != decoded:
            return "[REDACTED]" + trailing
        return original

    return encoded_token.sub(inspect, value)


def _redact_encoded_authorization_line(line: str) -> str:
    if "%" not in line:
        return line
    core = line.rstrip("\r\n")
    newline = line[len(core):]
    if len(core.encode("utf-8", errors="replace")) > MAX_ENCODED_TOKEN_BYTES:
        return "[REDACTED]" + newline
    decoded = _bounded_stable_decode(core)
    if decoded is None:
        return "[REDACTED]" + newline
    if (
        _AUTHORIZATION_HEADER_PATTERN.search(decoded)
        or _AUTHORIZATION_ASSIGNMENT_PATTERN.search(decoded)
        or _SERIALIZED_AUTHORIZATION_KEY_PATTERN.search(decoded)
    ):
        return "[REDACTED]" + newline
    return line


def _bounded_stable_decode(value: str) -> str | None:
    if len(value.encode("utf-8", errors="replace")) > MAX_ENCODED_TOKEN_BYTES:
        return None
    decoded = value
    deadline = time.monotonic() + MAX_ENCODED_DECODE_SECONDS
    for _ in range(MAX_ENCODED_DECODE_ITERATIONS):
        if time.monotonic() > deadline:
            return None
        next_value = unquote_plus(decoded)
        if len(next_value.encode("utf-8", errors="replace")) > MAX_ENCODED_TOKEN_BYTES:
            return None
        if next_value == decoded:
            return decoded
        decoded = next_value
    return None


def _sanitize_link_target(target: str) -> str:
    trailing = ""
    while target and target[-1] in ".,;!?":
        trailing = target[-1] + trailing
        target = target[:-1]
    try:
        parsed = urlsplit(target)
    except ValueError:
        fallback = _redact_serialized_authorization(target)
        fallback = _SECRET_VALUE_PATTERNS[0].sub("[REDACTED]", fallback)
        fallback = _SECRET_VALUE_PATTERNS[1].sub(r"\1[REDACTED]", fallback)
        fallback = _redact_secret_assignments(fallback)
        return fallback[:2_048] + ("...[truncated]" if len(fallback) > 2_048 else "") + trailing
    sensitive_keys = {
        "api_key",
        "apikey",
        "authorization",
        "client_assertion",
        "code_verifier",
        "client_assertion",
        "client_secret",
        "code_verifier",
        "code",
        "credential",
        "id_token",
        "key",
        "password",
        "secret",
        "sig",
        "signature",
        "subscription_key",
        "token",
        "x_api_key",
    }

    def sanitize_url_component(component: str) -> str:
        decoded = unquote_plus(component)
        sanitized_component = _redact_serialized_authorization(decoded)
        sanitized_component = _SECRET_VALUE_PATTERNS[0].sub("[REDACTED]", sanitized_component)
        sanitized_component = _SECRET_VALUE_PATTERNS[1].sub(r"\1[REDACTED]", sanitized_component)
        sanitized_component = _SECRET_VALUE_PATTERNS[2].sub("[REDACTED]", sanitized_component)
        sanitized_component = _redact_secret_assignments(sanitized_component)
        return component if sanitized_component == decoded else sanitized_component

    def sanitize_parameters(parameters: str) -> str:
        parts = []
        for part in parameters.split("&") if parameters else []:
            key, separator, value = part.partition("=")
            normalized_key = unquote_plus(key).casefold().replace("-", "_")
            is_sensitive = (
                normalized_key in sensitive_keys
                or normalized_key.endswith("_token")
                or normalized_key.endswith("_key")
            )
            decoded_value = unquote_plus(value)
            sanitized_value = sanitize_url_component(decoded_value)
            embedded_secret = sanitized_value != decoded_value
            parts.append(
                f"{key}{separator}[REDACTED]"
                if separator and (is_sensitive or embedded_secret)
                else (
                    f"{key}{separator}{value}"
                    if separator
                    else sanitize_url_component(part)
                )
            )
        return "&".join(parts)

    netloc = parsed.netloc
    if "@" in netloc:
        _userinfo, host = netloc.rsplit("@", 1)
        netloc = f"[REDACTED]@{host}"
    fragment = parsed.fragment
    if "?" in fragment:
        fragment_path, fragment_query = fragment.split("?", 1)
        fragment = f"{fragment_path}?{sanitize_parameters(fragment_query)}"
    else:
        fragment = sanitize_parameters(fragment)

    return urlunsplit(
        (
            parsed.scheme,
            sanitize_url_component(netloc),
            sanitize_url_component(parsed.path),
            sanitize_parameters(parsed.query),
            fragment,
        )
    ) + trailing


_RESPONSE_LOCAL_PATH_START = re.compile(
    r"""(?ix)
    (?:
        [A-Z]:[\\/]
        | (?<!:)\\\\[^\\/\r\n]+[\\/]
        | (?<!:)//[^/\r\n]+/
        | /(?:home|tmp|var|etc|root|Users)(?:/|$)
        | /(?:usr|opt|mnt|srv|bin|sbin|lib|lib64|run|dev|proc|sys)(?:/|$)
        | /(?:workspace|boot|private|media|app|data)(?:/|$)
        | \$HOME[\\/]
        | \$\{HOME\}[\\/]
        | ~[A-Za-z0-9._-]*[\\/]
        | %USERPROFILE%[\\/]
    )
    """
)


def _redact_response_local_paths(value: str) -> str:
    value = _redact_quoted_response_paths(value)
    cursor = 0
    while match := _RESPONSE_LOCAL_PATH_START.search(value, cursor):
        end = _scan_unquoted_path_end(value, match.start(), match.end())
        if end <= match.start():
            cursor = match.end()
            continue
        value = value[:match.start()] + "<PATH>" + value[end:]
        cursor = match.start() + len("<PATH>")
    return value


def _redact_quoted_response_paths(value: str) -> str:
    cursor = 0
    while cursor < len(value):
        if value[cursor] not in {'"', "'"}:
            cursor += 1
            continue
        quote = value[cursor]
        start_match = _RESPONSE_LOCAL_PATH_START.match(value, cursor + 1)
        if not start_match:
            cursor += 1
            continue
        scan = start_match.end()
        while scan < len(value) and value[scan] not in "\r\n":
            if value[scan] == quote:
                following = value[scan + 1] if scan + 1 < len(value) else ""
                if not following or following.isspace() or following in ".,;:!?)]}":
                    value = value[:cursor + 1] + "<PATH>" + value[scan:]
                    cursor += len('"<PATH>"')
                    break
            scan += 1
        else:
            cursor += 1
            continue
    return value


def _scan_unquoted_path_end(value: str, start: int, prefix_end: int) -> int:
    scan = prefix_end
    while scan < len(value):
        char = value[scan]
        if char in "\r\n,;!?\"()[]{}":
            break
        if char == "." and (scan + 1 == len(value) or value[scan + 1].isspace()):
            break
        if char.isspace():
            final_component = re.split(r"[\\/]", value[start:scan])[-1]
            if "." in final_component:
                break
            token_start = scan + 1
            token_end = token_start
            while token_end < len(value) and not value[token_end].isspace():
                if value[token_end] in "\r\n,;!?\"()[]{}":
                    break
                token_end += 1
            token = value[token_start:token_end]
            previous = value[scan - 1] if scan > start else ""
            following = value[token_end:]
            if re.fullmatch(
                r"(?i)(?:and|or|before|then|for|from|with|at|in|on|to|using|should|must|via|exists)",
                token,
            ):
                break
            extension_ahead = bool(
                re.match(
                    r"(?i)^\s+(?:(?!\s+(?:and|or|before|then|for|from|with|at|in|on|to|using|should|must|via)\b)"
                    r"[^,;!?\"()\[\]{}])*\.[A-Za-z0-9]{1,10}(?=\s|[.,;!?]|$)",
                    following,
                )
            )
            next_is_boundary = (
                not following
                or following[0] in ".,;!?\"()[]{}"
                or bool(
                    re.match(
                        r"\s+(?:and|or|before|then|for|from|with|at|in|on|to|using|should|must|via|exists)\b",
                        following,
                        flags=re.I,
                    )
                )
            )
            if (
                previous not in "\\/"
                and not any(separator in token for separator in ("\\", "/"))
                and "." not in token
                and not extension_ahead
                and not next_is_boundary
            ):
                break
        scan += 1
    return scan


def select_servers(server: str | None, servers: list[str] | None) -> dict:
    """Resolve an explicit server selection without silent fallback."""
    if server is not None and servers is not None:
        raise ValueError("--server and --servers cannot be used together")
    if server is not None:
        if server not in MCP_SERVERS:
            raise ValueError(f"unknown server '{_sanitize_identifier(server)}'")
        return {server: MCP_SERVERS[server]}
    if servers is not None:
        if not servers:
            raise ValueError("--servers requires at least one server")
        unknown = [name for name in servers if name not in MCP_SERVERS]
        if unknown:
            raise ValueError(
                "unknown server(s): " + ", ".join(_sanitize_identifier(name) for name in unknown)
            )
        return {name: MCP_SERVERS[name] for name in servers}
    return MCP_SERVERS


def _bounded_excerpt(value: str | bytes | None, max_chars: int) -> tuple[str, bool]:
    return _sanitize_text(_coerce_process_text(value), max_chars=max_chars)


def _bounded_stdout_excerpt(value: str | bytes | None) -> tuple[str, bool]:
    sanitized_lines = []
    lines, boundary_errors, boundary_truncated = _bounded_event_lines(value)
    per_line_truncated = boundary_truncated
    for _line_number, line in lines:
        try:
            parsed_line = json.loads(line)
        except (json.JSONDecodeError, ValueError, RecursionError):
            sanitized_line, truncated = _sanitize_text(line)
            sanitized_lines.append(sanitized_line)
            per_line_truncated = per_line_truncated or truncated
        else:
            per_line_truncated = per_line_truncated or _contains_oversized_diagnostic_value(parsed_line)
            sanitized_lines.append(json.dumps(_sanitize_diagnostic_value(parsed_line), ensure_ascii=True))
    excerpt, final_truncated = _sanitize_text("\n".join(sanitized_lines), max_chars=MAX_STDOUT_EXCERPT)
    return excerpt, per_line_truncated or final_truncated


def _bounded_event_lines(value: str | bytes | None) -> tuple[list[tuple[int, str]], list[str], bool]:
    """Bound bytes, lines, and per-line size before any JSON parsing."""
    is_bytes = isinstance(value, bytes)
    reader = io.BytesIO(value) if is_bytes else io.StringIO(value or "")
    accepted: list[tuple[int, str]] = []
    errors: list[str] = []
    total_bytes = 0
    truncated = False

    for line_number in range(1, MAX_STDOUT_PARSE_LINES + 1):
        line = reader.readline(MAX_STDOUT_LINE_BYTES + 1)
        if not line:
            break
        newline_markers = (b"\n", b"\r") if is_bytes else ("\n", "\r")
        if len(line) > MAX_STDOUT_LINE_BYTES and not line.endswith(newline_markers):
            errors.append(
                f"line {line_number}: event exceeds {MAX_STDOUT_LINE_BYTES} byte pre-parse limit"
            )
            truncated = True
            break
        line_bytes = len(line) if is_bytes else len(line.encode("utf-8", errors="replace"))
        if line_bytes > MAX_STDOUT_LINE_BYTES:
            errors.append(
                f"line {line_number}: event exceeds {MAX_STDOUT_LINE_BYTES} byte pre-parse limit"
            )
            truncated = True
            break
        if total_bytes + line_bytes > MAX_STDOUT_PARSE_BYTES:
            errors.append(f"stdout exceeds {MAX_STDOUT_PARSE_BYTES} byte pre-parse limit")
            truncated = True
            break
        total_bytes += line_bytes
        text_line = line.decode("utf-8", errors="replace") if is_bytes else line
        stripped = text_line.strip()
        if stripped:
            accepted.append((line_number, stripped))
    else:
        if reader.read(1):
            errors.append(f"stdout exceeds {MAX_STDOUT_PARSE_LINES} line pre-parse limit")
            truncated = True

    if not truncated and reader.read(1):
        errors.append("stdout contains data beyond the pre-parse budget")
        truncated = True
    return accepted, errors, truncated


def _contains_oversized_diagnostic_value(value: object, *, depth: int = 0) -> bool:
    if depth >= 4:
        return True
    if isinstance(value, dict):
        return len(value) > 20 or any(
            len(str(key)) > MAX_DIAGNOSTIC_TEXT
            or _contains_oversized_diagnostic_value(child, depth=depth + 1)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return len(value) > 20 or any(
            _contains_oversized_diagnostic_value(item, depth=depth + 1)
            for item in value
        )
    return isinstance(value, str) and len(value) > MAX_DIAGNOSTIC_TEXT


def serialized_diagnostic_events_size(events: list[dict]) -> int:
    """Return the exact persisted JSON list-envelope size for diagnostics events."""
    return len(json.dumps(events, ensure_ascii=True, separators=(",", ":")))


def _empty_diagnostics() -> dict:
    return {
        "events": [],
        "events_truncated": False,
        "stdout_excerpt": "",
        "stdout_truncated": False,
        "stderr_excerpt": "",
        "stderr_truncated": False,
    }


def _build_diagnostics(
    parsed: dict | None,
    stdout: str | bytes | None,
    stderr: str | bytes | None,
    *,
    preserve_stdout: bool,
) -> dict:
    diagnostics = _empty_diagnostics()
    if parsed is not None:
        diagnostics["events"] = parsed["diagnostic_events"]
        diagnostics["events_truncated"] = parsed["diagnostic_events_truncated"]
    if preserve_stdout:
        diagnostics["stdout_excerpt"], diagnostics["stdout_truncated"] = _bounded_stdout_excerpt(stdout)
    diagnostics["stderr_excerpt"], diagnostics["stderr_truncated"] = _bounded_excerpt(
        stderr,
        MAX_STDERR_EXCERPT,
    )
    return diagnostics


def parse_event_stream(stdout: str | bytes) -> dict:
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
        "_observed_tools_raw": [],
        "_successful_tools_raw": [],
        "diagnostic_events": [],
        "diagnostic_events_truncated": False,
        "mcp_failure": None,
        "mcp_statuses": {},
        "session_failure": None,
        "stdout_input_truncated": False,
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
    mcp_statuses: dict[str, tuple[str, str | None]] = {}

    def add_diagnostic(event_type: str, data: dict) -> None:
        if len(metrics["diagnostic_events"]) >= MAX_DIAGNOSTIC_EVENTS:
            metrics["diagnostic_events_truncated"] = True
            return
        diagnostic = {
            "event_type": event_type,
            "data": _sanitize_diagnostic_value(data),
        }
        candidate_events = [*metrics["diagnostic_events"], diagnostic]
        if serialized_diagnostic_events_size(candidate_events) > MAX_DIAGNOSTIC_EVENTS_CHARS:
            metrics["diagnostic_events_truncated"] = True
            return
        metrics["diagnostic_events"].append(diagnostic)

    lines, boundary_errors, boundary_truncated = _bounded_event_lines(stdout)
    parse_errors.extend(boundary_errors)
    metrics["stdout_input_truncated"] = boundary_truncated

    for line_number, line in lines:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError, RecursionError):
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
            output_tokens = data["outputTokens"] if "outputTokens" in data else 0
            if type(output_tokens) is int and 0 <= output_tokens <= MAX_USAGE_METRIC:
                if metrics["output_tokens"] + output_tokens <= MAX_USAGE_METRIC:
                    metrics["output_tokens"] += output_tokens
                else:
                    parse_errors.append(
                        f"line {line_number}: cumulative output token count exceeds {MAX_USAGE_METRIC}"
                    )
            else:
                parse_errors.append(f"line {line_number}: output token count must be a non-negative integer")
        elif etype == "tool.execution_start":
            tool_call_id = data.get("toolCallId")
            tool_name = data.get("toolName")
            if not isinstance(tool_call_id, str) or not isinstance(tool_name, str):
                parse_errors.append(f"line {line_number}: tool start missing identity")
                continue
            if tool_call_id in started_tools:
                parse_errors.append(
                    f"line {line_number}: duplicate tool start for {_sanitize_identifier(tool_call_id)}"
                )
                continue
            started_tools[tool_call_id] = tool_name
            if tool_name not in metrics["_observed_tools_raw"]:
                metrics["_observed_tools_raw"].append(tool_name)
                metrics["observed_tools"].append(_sanitize_identifier(tool_name))
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
                parse_errors.append(
                    f"line {line_number}: duplicate tool completion for {_sanitize_identifier(tool_call_id)}"
                )
            elif tool_name != started_tools[tool_call_id]:
                parse_errors.append(
                    f"line {line_number}: tool completion name {_sanitize_identifier(tool_name)} does not match "
                    f"start name {_sanitize_identifier(started_tools[tool_call_id])}"
                )
            else:
                completed_tool_calls.add(tool_call_id)
                if tool_name not in metrics["_observed_tools_raw"]:
                    metrics["_observed_tools_raw"].append(tool_name)
                    metrics["observed_tools"].append(_sanitize_identifier(tool_name))
                if type(data.get("success")) is not bool:
                    parse_errors.append(f"line {line_number}: tool completion missing Boolean success")
                elif data["success"] is True and tool_name not in metrics["_successful_tools_raw"]:
                    metrics["_successful_tools_raw"].append(tool_name)
                    metrics["successful_tools"].append(_sanitize_identifier(tool_name))
                    last_successful_tool_line = line_number
            if data.get("success") is False:
                metrics["tool_errors"] += 1
                add_diagnostic(
                    etype,
                    {
                        "toolName": tool_name,
                        "success": False,
                        "error": data.get("error"),
                        "result": data.get("result"),
                    },
                )
        elif etype == "session.mcp_server_status_changed":
            add_diagnostic(etype, data)
            status = str(data.get("status") or data.get("state") or "").casefold()
            error = data.get("error") or data.get("message")
            raw_server = data.get("serverName") or data.get("server") or data.get("name") or "selected MCP server"
            server = _sanitize_text(str(raw_server))[0]
            mcp_statuses[server] = (status, _sanitize_text(str(error))[0] if error else None)
        elif etype == "session.mcp_servers_loaded":
            add_diagnostic(etype, data)
            servers = data.get("servers")
            if not isinstance(servers, list):
                parse_errors.append(f"line {line_number}: mcp_servers_loaded servers must be a list")
            else:
                for server_data in servers[:MAX_DIAGNOSTIC_EVENTS]:
                    if not isinstance(server_data, dict):
                        parse_errors.append(f"line {line_number}: MCP server summary must be an object")
                        continue
                    raw_name = server_data.get("name")
                    raw_status = server_data.get("status")
                    if not isinstance(raw_name, str) or not isinstance(raw_status, str):
                        parse_errors.append(f"line {line_number}: MCP server summary missing name or status")
                        continue
                    server = _sanitize_text(raw_name)[0]
                    status = raw_status.casefold()
                    error = server_data.get("error")
                    mcp_statuses[server] = (status, _sanitize_text(str(error))[0] if error else None)
        elif etype == "session.error":
            add_diagnostic(etype, data)
            error_type = data.get("errorType")
            message = data.get("message")
            if not isinstance(error_type, str) or not isinstance(message, str):
                parse_errors.append(f"line {line_number}: session.error missing errorType or message")
            else:
                metrics["session_failure"] = (
                    f"{_sanitize_text(error_type)[0]}: {_sanitize_text(message)[0]}"
                )
        elif etype == "result":
            if result_seen:
                parse_errors.append(f"line {line_number}: duplicate terminal result")
            result_seen = True
            metrics["result_exit_code"] = event.get("exitCode")
            usage = event["usage"] if "usage" in event else {}
            if isinstance(usage, dict):
                for key, metric_name in (
                    ("premiumRequests", "premium_requests"),
                    ("totalApiDurationMs", "api_duration_ms"),
                    ("sessionDurationMs", "session_duration_ms"),
                ):
                    value = usage.get(key)
                    if value is None:
                        continue
                    if (
                        not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or (isinstance(value, float) and not math.isfinite(value))
                        or value < 0
                        or value > MAX_USAGE_METRIC
                    ):
                        parse_errors.append(
                            f"line {line_number}: usage.{key} must be a finite non-negative number"
                        )
                        continue
                    metrics[metric_name] = value
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

    failing_mcp_statuses = []
    for server, (status, error) in mcp_statuses.items():
        if status != "connected":
            detail = error or f"status is {status or 'unknown'}"
            failing_mcp_statuses.append(f"{server}: {detail}")
    if failing_mcp_statuses:
        metrics["mcp_failure"] = "; ".join(failing_mcp_statuses)
    metrics["mcp_statuses"] = {
        server: {"status": status, "error": error}
        for server, (status, error) in mcp_statuses.items()
    }

    metrics["parse_error"] = "; ".join(dict.fromkeys(parse_errors)) or None

    return {"response": last_message_content, **metrics}


def validate_row_evidence(parsed: dict, tool_prefix: str, azure_required: bool) -> tuple[bool, str | None, bool]:
    """Validate selected-source and optional Azure evidence for one row."""
    if parsed["session_failure"]:
        return False, f"session_error: {parsed['session_failure']}", False
    selected_mcp_status = next(
        (
            status
            for server, status in parsed["mcp_statuses"].items()
            if server.casefold() == tool_prefix.casefold()
        ),
        None,
    )
    if selected_mcp_status and selected_mcp_status["status"] != "connected":
        detail = selected_mcp_status["error"] or f"status is {selected_mcp_status['status'] or 'unknown'}"
        return False, f"mcp_initialization_failure: {tool_prefix}: {detail}", False
    if parsed["parse_error"]:
        return False, f"event_parse_failure: {parsed['parse_error']}", False
    if parsed["tool_errors"]:
        return False, f"tool_error: {parsed['tool_errors']} tool execution(s) failed", False

    observed_tools = parsed["_observed_tools_raw"]
    cross_source_tools = [name for name in observed_tools if _source_for_tool(name) != tool_prefix]
    if cross_source_tools:
        sanitized_tools = [_sanitize_identifier(name) for name in cross_source_tools]
        return False, f"cross_source_tool_call: {', '.join(sanitized_tools)}", False
    if not observed_tools:
        return False, "source_selection_unproven: no documentation tool calls observed", False
    if not any(_source_for_tool(name) == tool_prefix for name in parsed["_successful_tools_raw"]):
        return False, "source_selection_unproven: no selected-source tool completed successfully", False
    if not parsed["response"]:
        return False, "missing_response: no assistant response event contained content", False

    azure_live_query_proven = (
        azure_required
        and any(
            _tool_matches_source(name, tool_prefix) and _is_search_tool(name)
            for name in parsed["_successful_tools_raw"]
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
        "diagnostics": _empty_diagnostics(),
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
            "diagnostics": _build_diagnostics(None, None, str(exc), preserve_stdout=False),
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
        parsed = parse_event_stream(_coerce_process_text(proc.stdout))
        response = parsed["response"]
        evidence_valid, failure_reason, azure_live_query_proven = validate_row_evidence(
            parsed,
            source_descriptor["tool_prefix"],
            source_descriptor["azure_required"],
        )
        if proc.returncode != 0:
            status = "error"
            process_failure = f"process_exit_code: {proc.returncode}"
            failure_reason = f"{failure_reason}; {process_failure}" if failure_reason else process_failure
        elif parsed["result_exit_code"] not in (0, None):
            status = "invalid"
            event_failure = f"event_result_exit_code: {parsed['result_exit_code']}"
            failure_reason = f"{failure_reason}; {event_failure}" if failure_reason else event_failure
        else:
            status = "success" if evidence_valid else "invalid"
        if status != "success":
            response = ""
        else:
            response = _sanitize_response_text(response)

        result.update({
            "response": response,
            "stderr": _bounded_excerpt(proc.stderr, MAX_STDERR_EXCERPT)[0],
            "exit_code": proc.returncode,
            "response_time_seconds": round(elapsed, 2),
            "status": status,
            "passed": status == "success",
            "response_present": status == "success" and bool(response),
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
            "diagnostics": _build_diagnostics(
                parsed,
                proc.stdout,
                proc.stderr,
                preserve_stdout=status != "success",
            ),
        })

    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start_time
        partial_stdout = exc.stdout
        partial_stderr = exc.stderr
        parsed = parse_event_stream(partial_stdout) if partial_stdout else None
        result.update({
            "response": "",
            "stderr": _bounded_excerpt(
                partial_stderr or f"Timed out after {timeout}s",
                MAX_STDERR_EXCERPT,
            )[0],
            "exit_code": -1,
            "response_time_seconds": round(elapsed, 2),
            "status": "timeout",
            "passed": False,
            "response_present": False,
            "failure_reason": f"timeout: exceeded {timeout}s",
            "observed_tools": parsed["observed_tools"] if parsed else [],
            "successful_tools": parsed["successful_tools"] if parsed else [],
            "turns": parsed["turns"] if parsed else 0,
            "tool_calls": parsed["tool_calls"] if parsed else 0,
            "tool_errors": parsed["tool_errors"] if parsed else 0,
            "output_tokens": parsed["output_tokens"] if parsed else 0,
            "premium_requests": parsed["premium_requests"] if parsed else None,
            "api_duration_ms": parsed["api_duration_ms"] if parsed else None,
            "session_duration_ms": parsed["session_duration_ms"] if parsed else None,
            "event_parse_error": parsed["parse_error"] if parsed else None,
            "diagnostics": _build_diagnostics(
                parsed,
                partial_stdout,
                partial_stderr,
                preserve_stdout=True,
            ),
        })
    except OSError as exc:
        elapsed = time.monotonic() - start_time
        sanitized_error = _sanitize_text(str(exc), max_chars=MAX_STDERR_EXCERPT)[0]
        result.update({
            "response": "",
            "stderr": sanitized_error,
            "exit_code": -1,
            "response_time_seconds": round(elapsed, 2),
            "status": "error",
            "passed": False,
            "failure_reason": f"process_launch_error: {sanitized_error}",
            "turns": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "output_tokens": 0,
            "premium_requests": None,
            "api_duration_ms": None,
            "session_duration_ms": None,
            "event_parse_error": None,
            "diagnostics": _build_diagnostics(None, None, sanitized_error, preserve_stdout=False),
        })

    return result


def run_evaluation(
    scenarios: list[dict] | None,
    servers: dict | None = None,
    models: list[str] | None = None,
    timeout: int = 120,
    require_azure: bool = False,
) -> dict:
    """Run the full evaluation matrix."""
    scenarios = load_scenarios(SCENARIOS_FILE) if scenarios is None else scenarios
    servers = MCP_SERVERS if servers is None else servers
    models = MODELS if models is None else models
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    if not servers:
        raise ValueError("servers must not be empty")
    if not models:
        raise ValueError("models must not be empty")

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

    from eval_scorer import score_result, validate_required_matrix

    if not isinstance(baseline, dict) or not isinstance(baseline.get("results"), list):
        print("Error: Baseline JSON must be an object with a results array", file=sys.stderr)
        return 2
    baseline_results = baseline["results"]
    baseline_scored = [score_result(row) for row in baseline_results]
    required_scenarios = sorted({
        row.get("scenario_id")
        for row in baseline_scored
        if isinstance(row, dict) and isinstance(row.get("scenario_id"), str)
    })
    required_servers = sorted({
        row.get("server")
        for row in baseline_scored
        if isinstance(row, dict) and isinstance(row.get("server"), str)
    })
    required_models = sorted({
        row.get("model")
        for row in baseline_scored
        if isinstance(row, dict) and isinstance(row.get("model"), str)
    })
    azure_required_servers = {
        row.get("server")
        for row in baseline_scored
        if isinstance(row, dict)
        and row.get("azure_required") is True
        and isinstance(row.get("server"), str)
    }
    baseline_publication = validate_required_matrix(
        baseline_scored,
        scenario_ids=required_scenarios,
        servers=required_servers,
        models=required_models,
        azure_required_servers=azure_required_servers,
    )
    if not baseline_publication["allowed"]:
        print(
            "Error: Baseline comparison blocked by invalid baseline matrix: "
            + "; ".join(baseline_publication["failure_reasons"]),
            file=sys.stderr,
        )
        return 2
    current_scored = [score_result(row) for row in current.get("results", [])]
    publication = validate_required_matrix(
        current_scored,
        scenario_ids=required_scenarios,
        servers=required_servers,
        models=required_models,
        azure_required_servers=azure_required_servers,
    )
    if not publication["allowed"]:
        print(
            "Error: Baseline comparison blocked by invalid or incomplete current matrix: "
            + "; ".join(publication["failure_reasons"]),
            file=sys.stderr,
        )
        return 1

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

    baseline_rates = _success_rates({"results": baseline_scored})
    current_rates = _success_rates({"results": current_scored})

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

    try:
        servers = select_servers(args.server, args.servers)
    except ValueError as exc:
        print(f"Error: {exc}. Available: {list(MCP_SERVERS.keys())}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.models is not None and not args.models:
        print("Error: --models requires at least one model", file=sys.stderr)
        raise SystemExit(1)
    models = args.models if args.models is not None else MODELS

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
        json.dump(output, f, indent=2, allow_nan=False)

    print(f"\nResults saved to {output_path}")
    print(f"Total evaluations: {output['metadata']['total_evaluations']}")

    if args.baseline:
        exit_code = compare_results(output, args.baseline)
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
