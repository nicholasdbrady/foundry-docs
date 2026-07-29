#!/usr/bin/env python3
"""Verify every publishable docs-vnext route against the hosted site."""

from __future__ import annotations

import argparse
import concurrent.futures
import html
from http.client import HTTPException
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen

SCHEMA_VERSION = 1
DEFAULT_MAX_DIAGNOSTICS = 100
DEFAULT_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
DEFAULT_MIN_CONTENT_CHARACTERS = 80
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_WORKERS = 16
MAX_DIAGNOSTIC_STRING_LENGTH = 500
IGNORED_HTML_TAGS = {"script", "style", "svg", "noscript", "template"}
CONTENT_HTML_TAGS = {"main", "article"}
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\r?\n(?P<body>.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)
FENCED_CODE_PATTERN = re.compile(r"(?ms)^(`{3,}|~{3,}).*?^\1\s*$")
JSX_COMMENT_PATTERN = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[([^\]]*)]\([^)]+\)")
MARKDOWN_MARKUP_PATTERN = re.compile(r"[*_`~>#|{}\[\]()]")
JSX_TAG_PATTERN = re.compile(r"<[^>]+>")
MAX_SOURCE_MARKERS = 32


@dataclass(frozen=True, slots=True)
class RouteTarget:
    kind: str
    route: str
    source_navigation_entry: str
    candidate_source_path: str
    markers: tuple[str, ...]
    expected_json: str | None = None


@dataclass(frozen=True, slots=True)
class HttpResult:
    status_code: int | None
    body: str
    final_url: str
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RouteResult:
    target: RouteTarget
    response_status: int | None
    final_url: str
    failure_class: str | None = None
    detail: str | None = None


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._content_depth = 0
        self._all_parts: list[str] = []
        self._content_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if self._ignored_depth:
            self._ignored_depth += 1
            return
        if tag in IGNORED_HTML_TAGS:
            self._ignored_depth = 1
            return
        if tag in CONTENT_HTML_TAGS:
            self._content_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._ignored_depth:
            self._ignored_depth -= 1
            return
        if tag in CONTENT_HTML_TAGS and self._content_depth:
            self._content_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        self._all_parts.append(data)
        if self._content_depth:
            self._content_parts.append(data)

    @property
    def all_text(self) -> str:
        return " ".join(self._all_parts)

    @property
    def content_text(self) -> str:
        return " ".join(self._content_parts)


class DiagnosticCollector:
    def __init__(self, max_diagnostics: int) -> None:
        self.max_diagnostics = max_diagnostics
        self.total = 0
        self.counts: Counter[str] = Counter()
        self.diagnostics: list[dict[str, Any]] = []

    def add(
        self,
        *,
        failure_class: str,
        route: str | None,
        source_navigation_entry: str,
        candidate_source_path: str | None,
        response_status: int | None = None,
        detail: str | None = None,
    ) -> None:
        self.total += 1
        self.counts[failure_class] += 1
        if len(self.diagnostics) >= self.max_diagnostics:
            return
        diagnostic: dict[str, Any] = {
            "route": route,
            "sourceNavigationEntry": source_navigation_entry,
            "candidateSourcePath": candidate_source_path,
            "responseStatus": response_status,
            "failureClass": failure_class,
        }
        if detail:
            diagnostic["detail"] = bounded_value(detail)
        self.diagnostics.append(diagnostic)

    def summary(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "counts": dict(sorted(self.counts.items())),
            "truncated": self.total > len(self.diagnostics),
        }


Fetcher = Callable[[str, float, int], HttpResult]


def bounded_value(value: Any) -> Any:
    if isinstance(value, str) and len(value) > MAX_DIAGNOSTIC_STRING_LENGTH:
        return value[: MAX_DIAGNOSTIC_STRING_LENGTH - 3] + "..."
    return value


def normalize_text(value: str) -> str:
    unescaped = html.unescape(value).lower()
    return " ".join(re.sub(r"[^\w]+", " ", unescaped, flags=re.UNICODE).split())


def normalize_origin(value: str, *, require_origin_only: bool = False) -> str | None:
    if not value:
        return None
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        return None
    if require_origin_only and (parts.path not in {"", "/"} or parts.query or parts.fragment):
        return None
    default_port = 80 if parts.scheme == "http" else 443
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{parts.scheme.lower()}://{parts.hostname.lower()}{port_suffix}"


def mintlify_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    normalized = normalized.replace(" ", "-")
    normalized = re.sub(r"[^a-z0-9_`\[\]-]", "", normalized)
    return re.sub(r"-+", "-", normalized).strip("-")


def openapi_summary_marker(value: str) -> str:
    value = MARKDOWN_LINK_PATTERN.sub(r"\1", value)
    value = MARKDOWN_MARKUP_PATTERN.sub(" ", value)
    return " ".join(value.split())


def _front_matter_value(front_matter: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", front_matter)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value


def source_markers(source_path: Path) -> tuple[str, ...]:
    text = source_path.read_text(encoding="utf-8")
    front_matter_match = FRONT_MATTER_PATTERN.match(text)
    front_matter = front_matter_match.group("body") if front_matter_match else ""
    body = text[front_matter_match.end() :] if front_matter_match else text
    body = JSX_COMMENT_PATTERN.sub(" ", FENCED_CODE_PATTERN.sub(" ", body))

    markers: list[str] = []
    for key in ("title", "description"):
        value = _front_matter_value(front_matter, key)
        if value and len(normalize_text(value)) >= 12:
            markers.append(value)

    body_markers: list[str] = []
    for paragraph in re.split(r"\n\s*\n", body):
        candidate = " ".join(line.strip() for line in paragraph.splitlines())
        if not candidate or candidate.startswith(("import ", "export ")):
            continue
        candidate = JSX_TAG_PATTERN.sub(" ", candidate)
        candidate = MARKDOWN_LINK_PATTERN.sub(r"\1", candidate)
        candidate = MARKDOWN_MARKUP_PATTERN.sub(" ", candidate)
        candidate = " ".join(candidate.split())
        if len(normalize_text(candidate)) >= 40:
            body_markers.append(candidate[:240])

    if len(body_markers) > MAX_SOURCE_MARKERS:
        last_index = len(body_markers) - 1
        indexes = {round(position * last_index / (MAX_SOURCE_MARKERS - 1)) for position in range(MAX_SOURCE_MARKERS)}
        body_markers = [body_markers[index] for index in sorted(indexes)]
    markers.extend(body_markers)

    return tuple(dict.fromkeys(markers))


def load_targets(
    inventory_path: Path,
    repository_root: Path,
) -> tuple[dict[str, Any], list[RouteTarget], dict[str, int]]:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if inventory.get("schemaVersion") != 1:
        raise ValueError("route inventory schemaVersion must be 1")
    if inventory.get("status") != "passed":
        raise ValueError(f"route inventory status must be passed, got {inventory.get('status')!r}")
    routes = inventory.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ValueError("route inventory must contain at least one route")

    targets: list[RouteTarget] = []
    seen: dict[str, str] = {}
    page_entries = 0
    for entry in routes:
        if not isinstance(entry, dict) or entry.get("kind") != "page":
            raise ValueError("route inventory contains a non-page route entry")
        route = entry.get("route")
        source_entry = entry.get("sourceNavigationEntry")
        candidate = entry.get("candidateSourcePath")
        if not all(isinstance(value, str) and value for value in (route, source_entry, candidate)):
            raise ValueError("route inventory contains an incomplete route entry")
        if not route.startswith("/"):
            raise ValueError(f"route inventory contains an invalid route: {route!r}")
        page_entries += 1
        if route in seen:
            if seen[route] != candidate:
                raise ValueError(
                    f"route inventory maps {route!r} to both {seen[route]!r} and {candidate!r}"
                )
            continue
        seen[route] = candidate
        source_path = repository_root / candidate
        if not source_path.is_file():
            raise ValueError(f"route source does not exist: {candidate}")
        targets.append(
            RouteTarget(
                kind="page",
                route=route,
                source_navigation_entry=source_entry,
                candidate_source_path=candidate,
                markers=source_markers(source_path),
            )
        )

    openapi_entries = inventory.get("openapi")
    if not isinstance(openapi_entries, list):
        raise ValueError("route inventory openapi must be an array")
    openapi_operations = 0
    for entry in openapi_entries:
        if not isinstance(entry, dict) or entry.get("kind") != "openapi":
            raise ValueError("route inventory contains an invalid OpenAPI entry")
        directory = entry.get("route")
        source_entry = entry.get("sourceNavigationEntry")
        candidate = entry.get("candidateSourcePath")
        if not all(isinstance(value, str) and value for value in (directory, source_entry, candidate)):
            raise ValueError("route inventory contains an incomplete OpenAPI entry")
        if not directory.startswith("/"):
            raise ValueError(f"OpenAPI directory must be root-relative: {directory!r}")
        source_path = repository_root / candidate
        if not source_path.is_file():
            raise ValueError(f"OpenAPI source does not exist: {candidate}")
        try:
            specification = json.loads(source_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"OpenAPI source is not valid JSON: {candidate}: {exc}") from exc
        hosted_source_route = "/" + PurePosixPath(candidate).relative_to("docs-vnext").as_posix()
        canonical_specification = json.dumps(specification, sort_keys=True, separators=(",", ":"))
        if hosted_source_route not in seen:
            seen[hosted_source_route] = candidate
            targets.append(
                RouteTarget(
                    kind="openapi_source",
                    route=hosted_source_route,
                    source_navigation_entry=source_entry,
                    candidate_source_path=candidate,
                    markers=(),
                    expected_json=canonical_specification,
                )
            )

        paths = specification.get("paths")
        if not isinstance(paths, dict):
            raise ValueError(f"OpenAPI source paths must be an object: {candidate}")
        for operation_path, path_item in paths.items():
            if not isinstance(operation_path, str) or not isinstance(path_item, dict):
                raise ValueError(f"OpenAPI source contains an invalid path item: {candidate}")
            for method, operation in path_item.items():
                method_lower = method.lower()
                if method_lower not in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}:
                    continue
                if not isinstance(operation, dict):
                    raise ValueError(f"OpenAPI operation must be an object: {candidate} {method} {operation_path}")
                if operation.get("x-excluded") is True:
                    continue
                tags = operation.get("tags")
                tag = tags[0] if isinstance(tags, list) and tags and isinstance(tags[0], str) else "default"
                summary = operation.get("summary")
                if isinstance(summary, str) and summary.strip():
                    route_label = summary
                    summary_marker = openapi_summary_marker(summary)
                else:
                    static_segments = [
                        segment
                        for segment in operation_path.split("/")
                        if segment and not (segment.startswith("{") and segment.endswith("}"))
                    ]
                    route_label = f"{method_lower} {' '.join(static_segments)}"
                    summary_marker = f"{method_lower.upper()} {operation_path}"
                operation_route = (
                    f"{directory.rstrip('/')}/{mintlify_slug(tag)}/{mintlify_slug(route_label)}"
                )
                openapi_operations += 1
                if operation_route in seen:
                    continue
                seen[operation_route] = f"{candidate} {method_lower.upper()} {operation_path}"
                targets.append(
                    RouteTarget(
                        kind="openapi_operation",
                        route=operation_route,
                        source_navigation_entry=f"{source_entry}[{method_lower.upper()} {operation_path}]",
                        candidate_source_path=candidate,
                        markers=(summary_marker, f"{method_lower.upper()} {operation_path}"),
                    )
                )

    return inventory, targets, {
        "pageEntries": page_entries,
        "uniquePageRoutes": len({entry["route"] for entry in routes}),
        "openapiSources": len(openapi_entries),
        "openapiOperations": openapi_operations,
        "requiredTargets": len(targets),
    }


def fetch_url(url: str, timeout_seconds: float, max_response_bytes: int) -> HttpResult:
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "foundry-docs-hosted-route-smoke/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - caller controls the trusted base URL
            try:
                body_bytes = response.read(max_response_bytes + 1)
                charset = response.headers.get_content_charset() or "utf-8"
                body = body_bytes[:max_response_bytes].decode(charset, errors="replace")
            except (HTTPException, LookupError, OSError) as exc:
                return HttpResult(
                    status_code=response.status,
                    body="",
                    final_url=response.geturl(),
                    error=f"{type(exc).__name__}: {exc}",
                )
            return HttpResult(
                status_code=response.status,
                body=body,
                final_url=response.geturl(),
                error=(
                    f"response exceeded maximum inspection size ({max_response_bytes} bytes)"
                    if len(body_bytes) > max_response_bytes
                    else None
                ),
            )
    except HTTPError as exc:
        try:
            body_bytes = exc.read(max_response_bytes)
            charset = exc.headers.get_content_charset() or "utf-8"
            body = body_bytes.decode(charset, errors="replace")
        except (HTTPException, LookupError, OSError) as read_exc:
            return HttpResult(
                status_code=exc.code,
                body="",
                final_url=exc.geturl(),
                error=f"{type(read_exc).__name__}: {read_exc}",
            )
        return HttpResult(
            status_code=exc.code,
            body=body,
            final_url=exc.geturl(),
            error=None,
        )
    except (HTTPException, TimeoutError, URLError, OSError) as exc:
        return HttpResult(status_code=None, body="", final_url=url, error=f"{type(exc).__name__}: {exc}")


def _same_origin(expected: str, observed: str) -> bool:
    expected_origin = normalize_origin(expected)
    observed_origin = normalize_origin(observed)
    return expected_origin is not None and expected_origin == observed_origin


def _deployment_diagnostics(
    collector: DiagnosticCollector,
    *,
    expected_source_sha: str,
    deployed_source_sha: str,
    deployment_state: str,
    expected_environment: str,
    deployment_environment: str,
    base_url: str,
    observed_base_url: str,
    conflicting_environment: str,
    conflicting_source_sha: str,
    conflicting_base_url: str,
) -> None:
    if deployment_environment != expected_environment:
        collector.add(
            failure_class="deployment_environment_mismatch",
            route=None,
            source_navigation_entry="deployment",
            candidate_source_path=None,
            detail=f"expected environment {expected_environment!r}, observed {deployment_environment!r}",
        )
    if deployment_state != "success":
        if deployment_state == "missing":
            failure_class = "deployment_missing"
        elif deployment_state in {"failure", "error"}:
            failure_class = "deployment_failed"
        else:
            failure_class = "deployment_incomplete"
        collector.add(
            failure_class=failure_class,
            route=None,
            source_navigation_entry="deployment",
            candidate_source_path=None,
            detail=f"latest deployment state is {deployment_state!r}",
        )
    if not deployed_source_sha:
        collector.add(
            failure_class="deployment_missing",
            route=None,
            source_navigation_entry="deployment",
            candidate_source_path=None,
            detail="no deployed source SHA was reported",
        )
    elif expected_source_sha and deployed_source_sha != expected_source_sha:
        collector.add(
            failure_class="stale_deployment",
            route=None,
            source_navigation_entry="deployment",
            candidate_source_path=None,
            detail=f"expected source SHA {expected_source_sha}, deployed source SHA {deployed_source_sha}",
        )
    if not observed_base_url:
        collector.add(
            failure_class="deployment_url_missing",
            route=None,
            source_navigation_entry="deployment",
            candidate_source_path=None,
            detail="deployment did not report environment_url",
        )
    elif normalize_origin(observed_base_url) is None or not _same_origin(base_url, observed_base_url):
        collector.add(
            failure_class="deployment_url_mismatch",
            route=None,
            source_navigation_entry="deployment",
            candidate_source_path=None,
            detail=f"expected hosted origin {base_url!r}, deployment reported {observed_base_url!r}",
        )
    if conflicting_base_url and _same_origin(base_url, conflicting_base_url):
        collector.add(
            failure_class="deployment_host_collision",
            route=None,
            source_navigation_entry="deployment",
            candidate_source_path=None,
            detail=(
                f"{expected_environment!r} and {conflicting_environment!r} report the same hosted origin; "
                f"conflicting source SHA is {conflicting_source_sha or 'unknown'}"
            ),
        )


def _probe_route(
    target: RouteTarget,
    *,
    base_url: str,
    timeout_seconds: float,
    max_response_bytes: int,
    min_content_characters: int,
    fetcher: Fetcher,
) -> RouteResult:
    url = urljoin(base_url.rstrip("/") + "/", quote(target.route.lstrip("/"), safe="/-._~"))
    response = fetcher(url, timeout_seconds, max_response_bytes)
    if response.final_url and not _same_origin(base_url, response.final_url):
        return RouteResult(
            target,
            response.status_code,
            response.final_url,
            "cross_origin_redirect",
            f"hosted route redirected to a different origin: {response.final_url}",
        )
    if response.status_code is None:
        return RouteResult(target, None, response.final_url, "route_unavailable", response.error)
    if response.status_code == 404:
        return RouteResult(target, 404, response.final_url, "route_missing", "hosted route returned 404")
    if response.status_code >= 500:
        return RouteResult(
            target,
            response.status_code,
            response.final_url,
            "route_server_error",
            "hosted route returned a server error",
        )
    if response.status_code < 200 or response.status_code >= 300:
        return RouteResult(
            target,
            response.status_code,
            response.final_url,
            "route_http_error",
            "hosted route did not return a successful response",
        )
    if response.error:
        return RouteResult(
            target,
            response.status_code,
            response.final_url,
            "route_response_invalid",
            response.error,
        )

    if target.kind == "openapi_source":
        try:
            hosted_specification = json.loads(response.body)
        except json.JSONDecodeError as exc:
            return RouteResult(
                target,
                response.status_code,
                response.final_url,
                "openapi_source_invalid",
                f"hosted OpenAPI source is not valid JSON: {exc}",
            )
        hosted_canonical = json.dumps(hosted_specification, sort_keys=True, separators=(",", ":"))
        if hosted_canonical != target.expected_json:
            return RouteResult(
                target,
                response.status_code,
                response.final_url,
                "stale_openapi_source",
                "hosted OpenAPI source does not match the validated source inventory",
            )
        return RouteResult(target, response.status_code, response.final_url)

    parser = VisibleTextParser()
    try:
        parser.feed(response.body)
    except Exception as exc:  # noqa: BLE001 - malformed hosted HTML is a route failure
        return RouteResult(
            target,
            response.status_code,
            response.final_url,
            "route_response_invalid",
            f"{type(exc).__name__}: {exc}",
        )

    content_text = normalize_text(parser.content_text)
    if len(content_text) < min_content_characters:
        return RouteResult(
            target,
            response.status_code,
            response.final_url,
            "empty_content",
            f"hosted main content contained {len(content_text)} normalized characters",
        )

    document_text = normalize_text(parser.all_text)
    normalized_markers = [normalize_text(marker) for marker in target.markers if normalize_text(marker)]
    missing_markers = [marker for marker in normalized_markers if marker not in document_text]
    if missing_markers:
        return RouteResult(
            target,
            response.status_code,
            response.final_url,
            "stale_content",
            f"hosted content is missing {len(missing_markers)} of {len(normalized_markers)} distributed source markers",
        )
    return RouteResult(target, response.status_code, response.final_url)


def build_initial_report(base_url: str, *, max_diagnostics: int, detail: str) -> dict[str, Any]:
    collector = DiagnosticCollector(max_diagnostics)
    collector.add(
        failure_class="workflow_incomplete",
        route=None,
        source_navigation_entry="workflow",
        candidate_source_path=None,
        detail=detail,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "blocked",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baseUrl": base_url,
        "deployment": {},
        "targetSummary": {
            "pageEntries": 0,
            "uniquePageRoutes": 0,
            "openapiSources": 0,
            "openapiOperations": 0,
            "requiredTargets": 0,
        },
        "routeSummary": {"required": 0, "checked": 0, "passed": 0, "failed": 0},
        "diagnosticSummary": collector.summary(),
        "diagnostics": collector.diagnostics,
    }


def check_hosted_routes(
    *,
    inventory_path: Path,
    repository_root: Path,
    base_url: str,
    expected_source_sha: str,
    deployed_source_sha: str,
    deployment_state: str,
    expected_environment: str,
    deployment_environment: str,
    observed_base_url: str,
    conflicting_environment: str = "",
    conflicting_source_sha: str = "",
    conflicting_base_url: str = "",
    max_diagnostics: int = DEFAULT_MAX_DIAGNOSTICS,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    min_content_characters: int = DEFAULT_MIN_CONTENT_CHARACTERS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    workers: int = DEFAULT_WORKERS,
    fetcher: Fetcher = fetch_url,
) -> dict[str, Any]:
    collector = DiagnosticCollector(max_diagnostics)
    configured_origin = normalize_origin(base_url, require_origin_only=True)
    if configured_origin is None:
        failure_class = "host_configuration_missing" if not base_url else "host_configuration_invalid"
        collector.add(
            failure_class=failure_class,
            route=None,
            source_navigation_entry="configuration",
            candidate_source_path=None,
            detail=(
                "repository variable DOCS_VNEXT_BASE_URL is not configured"
                if not base_url
                else "DOCS_VNEXT_BASE_URL must be an HTTP(S) origin without a path, query, or fragment"
            ),
        )
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "blocked",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "baseUrl": base_url,
            "deployment": {},
            "targetSummary": {
                "pageEntries": 0,
                "uniquePageRoutes": 0,
                "openapiSources": 0,
                "openapiOperations": 0,
                "requiredTargets": 0,
            },
            "routeSummary": {"required": 0, "checked": 0, "passed": 0, "failed": 0},
            "diagnosticSummary": collector.summary(),
            "diagnostics": collector.diagnostics,
        }
    try:
        inventory, targets, target_summary = load_targets(inventory_path, repository_root)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        collector.add(
            failure_class="source_inventory_invalid",
            route=None,
            source_navigation_entry="navigation",
            candidate_source_path=str(inventory_path),
            detail=str(exc),
        )
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "blocked",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "baseUrl": base_url,
            "deployment": {},
            "targetSummary": {
                "pageEntries": 0,
                "uniquePageRoutes": 0,
                "openapiSources": 0,
                "openapiOperations": 0,
                "requiredTargets": 0,
            },
            "routeSummary": {"required": 0, "checked": 0, "passed": 0, "failed": 0},
            "diagnosticSummary": collector.summary(),
            "diagnostics": collector.diagnostics,
        }

    _deployment_diagnostics(
        collector,
        expected_source_sha=expected_source_sha,
        deployed_source_sha=deployed_source_sha,
        deployment_state=deployment_state,
        expected_environment=expected_environment,
        deployment_environment=deployment_environment,
        base_url=base_url,
        observed_base_url=observed_base_url,
        conflicting_environment=conflicting_environment,
        conflicting_source_sha=conflicting_source_sha,
        conflicting_base_url=conflicting_base_url,
    )
    deployment = {
        "expectedSourceSha": expected_source_sha,
        "deployedSourceSha": deployed_source_sha,
        "state": deployment_state,
        "expectedEnvironment": expected_environment,
        "environment": deployment_environment,
        "reportedBaseUrl": observed_base_url,
        "conflictingEnvironment": conflicting_environment,
        "conflictingSourceSha": conflicting_source_sha,
        "conflictingBaseUrl": conflicting_base_url,
    }
    if collector.total:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "blocked",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "baseUrl": base_url,
            "navigationSource": inventory.get("navigationSource"),
            "deployment": deployment,
            "targetSummary": target_summary,
            "routeSummary": {"required": len(targets), "checked": 0, "passed": 0, "failed": 0},
            "diagnosticSummary": collector.summary(),
            "diagnostics": collector.diagnostics,
        }

    preflight = fetcher(base_url.rstrip("/") + "/", timeout_seconds, max_response_bytes)
    if (
        preflight.status_code is None
        or not 200 <= preflight.status_code < 300
        or preflight.error is not None
        or (preflight.final_url and not _same_origin(base_url, preflight.final_url))
    ):
        collector.add(
            failure_class="host_unavailable",
            route=None,
            source_navigation_entry="host",
            candidate_source_path=None,
            response_status=preflight.status_code,
            detail=(
                preflight.error
                or (
                    f"host preflight redirected to a different origin: {preflight.final_url}"
                    if preflight.final_url and not _same_origin(base_url, preflight.final_url)
                    else "host preflight did not return a successful response"
                )
            ),
        )
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "blocked",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "baseUrl": base_url,
            "navigationSource": inventory.get("navigationSource"),
            "deployment": deployment,
            "targetSummary": target_summary,
            "routeSummary": {"required": len(targets), "checked": 0, "passed": 0, "failed": 0},
            "diagnosticSummary": collector.summary(),
            "diagnostics": collector.diagnostics,
        }

    probe = lambda target: _probe_route(  # noqa: E731 - executor map needs a single-argument callable
        target,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        min_content_characters=min_content_characters,
        fetcher=fetcher,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(probe, targets))

    failed = [result for result in results if result.failure_class]
    host_failure_classes = {"route_unavailable", "route_server_error"}
    infrastructure_statuses = {401, 403, 429}
    host_wide_failure = bool(failed) and len(failed) == len(results) and (
        all(result.failure_class in host_failure_classes for result in failed)
        or (
            len({result.response_status for result in failed}) == 1
            and failed[0].response_status in infrastructure_statuses
        )
    )
    if host_wide_failure:
        collector.add(
            failure_class="host_unavailable",
            route=None,
            source_navigation_entry="host",
            candidate_source_path=None,
            detail="every required route was unavailable or returned a server error",
        )
    for result in failed:
        collector.add(
            failure_class=result.failure_class or "route_failure",
            route=result.target.route,
            source_navigation_entry=result.target.source_navigation_entry,
            candidate_source_path=result.target.candidate_source_path,
            response_status=result.response_status,
            detail=result.detail,
        )

    status = "blocked" if host_wide_failure else ("failed" if failed else "passed")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": status,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baseUrl": base_url,
        "navigationSource": inventory.get("navigationSource"),
        "deployment": deployment,
        "targetSummary": target_summary,
        "routeSummary": {
            "required": len(targets),
            "checked": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
        },
        "diagnosticSummary": collector.summary(),
        "diagnostics": collector.diagnostics,
    }


def render_summary(report: dict[str, Any]) -> str:
    routes = report["routeSummary"]
    targets = report.get("targetSummary", {})
    lines = [
        "# docs-vnext hosted route readiness",
        "",
        f"- **Status:** {report['status']}",
        f"- **Hosted base URL:** {report['baseUrl']}",
        f"- **Page entries / unique routes:** {targets.get('pageEntries', 0)} / "
        f"{targets.get('uniquePageRoutes', 0)}",
        f"- **OpenAPI sources / operations:** {targets.get('openapiSources', 0)} / "
        f"{targets.get('openapiOperations', 0)}",
        f"- **Required hosted targets:** {routes['required']}",
        f"- **Checked:** {routes['checked']}",
        f"- **Passed:** {routes['passed']}",
        f"- **Failed:** {routes['failed']}",
    ]
    deployment = report.get("deployment", {})
    if deployment:
        lines.extend(
            [
                f"- **Expected source SHA:** `{deployment.get('expectedSourceSha', '')}`",
                f"- **Deployed source SHA:** `{deployment.get('deployedSourceSha', '')}`",
                f"- **Deployment state:** {deployment.get('state', '')}",
            ]
        )
    lines.extend(["", "## Diagnostics", ""])
    diagnostics = report.get("diagnostics", [])
    if not diagnostics:
        lines.append("No hosted readiness failures.")
    else:
        for diagnostic in diagnostics[:20]:
            route = diagnostic.get("route") or "(host/deployment)"
            status = diagnostic.get("responseStatus")
            status_text = f", HTTP {status}" if status is not None else ""
            lines.append(
                f"- `{diagnostic['failureClass']}`: `{route}`{status_text} "
                f"from `{diagnostic.get('candidateSourcePath') or diagnostic['sourceNavigationEntry']}`"
            )
        if report["diagnosticSummary"]["truncated"] or len(diagnostics) > 20:
            lines.append("- Additional diagnostics are available in the JSON artifact.")
    return "\n".join(lines) + "\n"


def write_outputs(report: dict[str, Any], output_path: Path, summary_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(render_summary(report), encoding="utf-8")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-source-sha", default="")
    parser.add_argument("--deployed-source-sha", default="")
    parser.add_argument("--deployment-state", default="missing")
    parser.add_argument("--expected-environment", default="staging - docs-vnext")
    parser.add_argument("--deployment-environment", default="")
    parser.add_argument("--observed-base-url", default="")
    parser.add_argument("--conflicting-environment", default="")
    parser.add_argument("--conflicting-source-sha", default="")
    parser.add_argument("--conflicting-base-url", default="")
    parser.add_argument("--output", type=Path, default=Path("tests/eval_results/docs-vnext-hosted-routes.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("tests/eval_results/docs-vnext-hosted-routes.md"))
    parser.add_argument("--max-diagnostics", type=int, default=DEFAULT_MAX_DIAGNOSTICS)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--initialize-output", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.initialize_output:
        report = build_initial_report(
            args.base_url,
            max_diagnostics=args.max_diagnostics,
            detail="Workflow did not reach hosted route verification.",
        )
    elif args.inventory is None:
        print("--inventory is required unless --initialize-output is used", file=sys.stderr)
        return 2
    else:
        report = check_hosted_routes(
            inventory_path=args.inventory,
            repository_root=args.repository_root,
            base_url=args.base_url,
            expected_source_sha=args.expected_source_sha,
            deployed_source_sha=args.deployed_source_sha,
            deployment_state=args.deployment_state,
            expected_environment=args.expected_environment,
            deployment_environment=args.deployment_environment,
            observed_base_url=args.observed_base_url,
            conflicting_environment=args.conflicting_environment,
            conflicting_source_sha=args.conflicting_source_sha,
            conflicting_base_url=args.conflicting_base_url,
            max_diagnostics=args.max_diagnostics,
            timeout_seconds=args.timeout_seconds,
            workers=args.workers,
        )
    write_outputs(report, args.output, args.summary_output)
    print(
        f"docs-vnext hosted routes: {report['status']} "
        f"({report['routeSummary']['passed']}/{report['routeSummary']['required']} passed); "
        f"report: {args.output}"
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
