#!/usr/bin/env python3
"""Validate Mintlify navigation and emit a deterministic publishable route inventory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

SCHEMA_VERSION = 1
DEFAULT_MAX_DIAGNOSTICS = 100
MAX_DIAGNOSTIC_STRING_LENGTH = 500
NAVIGATION_CONTAINER_KEYS = ("products", "versions", "languages", "dropdowns", "tabs", "anchors", "groups", "menu")
ASSET_SUFFIXES = {
    ".avif",
    ".csv",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".json",
    ".pdf",
    ".png",
    ".svg",
    ".txt",
    ".webp",
    ".yaml",
    ".yml",
    ".zip",
}
LINK_PATTERN = re.compile(
    r"""(?x)
    \[[^\]]*]\(
        (?P<markdown><[^>\n]+>|[^\s)]+)
        (?:\s+["'][^"']*["'])?
    \)
    |
    \bhref\s*=\s*["'](?P<href>[^"']+)["']
    |
    ^\[[^\]]+]:\s*(?P<reference><[^>\n]+>|[^\s]+)
    """,
    re.MULTILINE,
)
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\r?\n.*?\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)
JSX_COMMENT_PATTERN = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
FENCED_CODE_PATTERN = re.compile(
    r"^(?P<fence>`{3,}|~{3,})[^\r\n]*\r?\n.*?^(?P=fence)\s*$",
    re.DOTALL | re.MULTILINE,
)
INLINE_CODE_PATTERN = re.compile(r"(?<!`)`[^`\r\n]*`(?!`)")


@dataclass(frozen=True, slots=True)
class RouteEntry:
    route: str
    source_navigation_entry: str
    candidate_source_path: str

    def as_dict(self) -> dict[str, str]:
        return {
            "kind": "page",
            "sourceNavigationEntry": self.source_navigation_entry,
            "route": f"/{self.route}",
            "candidateSourcePath": self.candidate_source_path,
        }


class NavigationCollector:
    def __init__(self, docs_dir: Path, max_diagnostics: int) -> None:
        self.docs_dir = docs_dir
        self.max_diagnostics = max_diagnostics
        self.routes: list[RouteEntry] = []
        self.openapi: list[dict[str, Any]] = []
        self.aliases: list[dict[str, str]] = []
        self.external_navigation: list[dict[str, str]] = []
        self.diagnostics: list[dict[str, Any]] = []
        self.diagnostic_counts: dict[str, int] = {}
        self.total_diagnostics = 0

    def add_diagnostic(
        self,
        *,
        source_navigation_entry: str,
        route: str | None,
        failure_class: str,
        candidate_source_path: str | None,
        **details: Any,
    ) -> None:
        self.total_diagnostics += 1
        self.diagnostic_counts[failure_class] = self.diagnostic_counts.get(failure_class, 0) + 1
        if len(self.diagnostics) >= self.max_diagnostics:
            return
        diagnostic = {
            "sourceNavigationEntry": source_navigation_entry,
            "route": route,
            "failureClass": failure_class,
            "candidateSourcePath": candidate_source_path,
        }
        diagnostic.update(details)
        self.diagnostics.append({key: bounded_diagnostic_value(value) for key, value in diagnostic.items()})

    def collect(self, navigation: Any) -> None:
        if not isinstance(navigation, dict):
            self.add_diagnostic(
                source_navigation_entry="navigation",
                route=None,
                failure_class="invalid_navigation",
                candidate_source_path=None,
                detail="navigation must be an object",
            )
            return
        self._visit_container(navigation, "navigation")

    def collect_redirects(self, redirects: Any) -> None:
        if redirects is None:
            return
        if not isinstance(redirects, list):
            self.add_diagnostic(
                source_navigation_entry="redirects",
                route=None,
                failure_class="invalid_route_alias",
                candidate_source_path=None,
                detail="redirects must be an array",
            )
            return

        route_entries = {entry.route: entry for entry in self.routes}
        raw_aliases: dict[str, tuple[str, str]] = {}
        for index, redirect in enumerate(redirects):
            entry_path = f"redirects[{index}]"
            if not isinstance(redirect, dict):
                self.add_diagnostic(
                    source_navigation_entry=entry_path,
                    route=repr(redirect),
                    failure_class="invalid_route_alias",
                    candidate_source_path=None,
                    detail="redirect entries must be objects",
                )
                continue
            source = redirect.get("source")
            destination = redirect.get("destination")
            source_route = normalize_root_route(source)
            destination_route = normalize_root_route(destination, allow_fragment=True)
            candidate = candidate_source_path(self.docs_dir, destination_route or str(destination))
            if source_route is None or destination_route is None:
                self.add_diagnostic(
                    source_navigation_entry=entry_path,
                    route=source if isinstance(source, str) else repr(source),
                    failure_class="invalid_route_alias",
                    candidate_source_path=candidate,
                    detail="redirect source and destination must be root-relative routes",
                )
                continue
            if source_route in raw_aliases or source_route in route_entries:
                self.add_diagnostic(
                    source_navigation_entry=entry_path,
                    route=f"/{source_route}",
                    failure_class="invalid_route_alias",
                    candidate_source_path=candidate,
                    detail="redirect source must be unique and cannot shadow a publishable route",
                )
                continue
            raw_aliases[source_route] = (destination_route, entry_path)

        for source_route, (destination_route, entry_path) in raw_aliases.items():
            resolved_route = self._resolve_alias(destination_route, raw_aliases)
            candidate = candidate_source_path(self.docs_dir, resolved_route or destination_route)
            if resolved_route is None or resolved_route not in route_entries:
                self.add_diagnostic(
                    source_navigation_entry=entry_path,
                    route=f"/{source_route}",
                    failure_class="invalid_route_alias",
                    candidate_source_path=candidate,
                    destination=f"/{destination_route}",
                    detail="redirect destination must resolve to a publishable route without a cycle",
                )
                continue
            self.aliases.append(
                {
                    "kind": "alias",
                    "sourceNavigationEntry": entry_path,
                    "route": f"/{source_route}",
                    "destination": f"/{destination_route}",
                    "candidateSourcePath": candidate,
                }
            )

    @staticmethod
    def _resolve_alias(route: str, aliases: dict[str, tuple[str, str]]) -> str | None:
        seen: set[str] = set()
        current = route
        while current in aliases:
            if current in seen:
                return None
            seen.add(current)
            current = aliases[current][0]
        return current

    def _visit_container(self, container: dict[str, Any], path: str) -> None:
        href = container.get("href")
        if href is not None:
            self._collect_href(href, f"{path}.href")

        if "root" in container:
            root = container["root"]
            if isinstance(root, str):
                self._collect_route(root, f"{path}.root")
            else:
                self.add_diagnostic(
                    source_navigation_entry=f"{path}.root",
                    route=repr(root),
                    failure_class="invalid_route_target",
                    candidate_source_path=None,
                    detail="navigation root must be a route string",
                )

        if "openapi" in container:
            self._collect_openapi(container["openapi"], f"{path}.openapi")

        if "pages" in container:
            self._visit_pages(container["pages"], f"{path}.pages")

        for key in NAVIGATION_CONTAINER_KEYS:
            if key not in container:
                continue
            children = container[key]
            child_path = f"{path}.{key}"
            if not isinstance(children, list):
                self.add_diagnostic(
                    source_navigation_entry=child_path,
                    route=None,
                    failure_class="invalid_navigation",
                    candidate_source_path=None,
                    detail=f"{key} must be an array",
                )
                continue
            for index, child in enumerate(children):
                entry_path = f"{child_path}[{index}]"
                if not isinstance(child, dict):
                    self.add_diagnostic(
                        source_navigation_entry=entry_path,
                        route=None,
                        failure_class="invalid_navigation",
                        candidate_source_path=None,
                        detail=f"{key} entries must be objects",
                    )
                    continue
                self._visit_container(child, entry_path)

    def _visit_pages(self, pages: Any, path: str) -> None:
        if not isinstance(pages, list):
            self.add_diagnostic(
                source_navigation_entry=path,
                route=None,
                failure_class="invalid_navigation",
                candidate_source_path=None,
                detail="pages must be an array",
            )
            return
        for index, item in enumerate(pages):
            entry_path = f"{path}[{index}]"
            if isinstance(item, str):
                self._collect_route(item, entry_path)
            elif isinstance(item, dict):
                self._visit_container(item, entry_path)
            else:
                self.add_diagnostic(
                    source_navigation_entry=entry_path,
                    route=repr(item),
                    failure_class="invalid_route_target",
                    candidate_source_path=None,
                    detail="page entries must be route strings or navigation objects",
                )

    def _collect_route(self, raw_route: str, entry_path: str) -> None:
        route = normalize_route(raw_route)
        candidate = candidate_source_path(self.docs_dir, route or raw_route)
        if route is None:
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=raw_route,
                failure_class="invalid_route_target",
                candidate_source_path=candidate,
                detail="routes must be extensionless relative URL paths without query strings, fragments, or traversal",
            )
            return

        entry = RouteEntry(route, entry_path, candidate)
        self.routes.append(entry)
        source_path = self.docs_dir / f"{route}.mdx"
        if not source_path.is_file():
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=f"/{route}",
                failure_class="missing_source_page",
                candidate_source_path=candidate,
            )
            return
        if is_empty_page(source_path):
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=f"/{route}",
                failure_class="empty_navigable_page",
                candidate_source_path=candidate,
            )

    def _collect_openapi(self, value: Any, entry_path: str) -> None:
        source: str | None = None
        directory: str | None = None
        if isinstance(value, str):
            source = value
        elif isinstance(value, dict):
            source = value.get("source")
            directory = value.get("directory")

        candidate = candidate_config_path(self.docs_dir, source) if isinstance(source, str) else None
        if not isinstance(source, str) or not source or normalize_file_reference(source) is None:
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=directory,
                failure_class="invalid_route_target",
                candidate_source_path=candidate,
                detail="openapi entries require a relative source path",
            )
            return
        if directory is not None and normalize_route(directory) is None:
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=directory,
                failure_class="invalid_route_target",
                candidate_source_path=candidate,
                detail="openapi directory must be an extensionless relative route",
            )
            return

        self.openapi.append(
            {
                "kind": "openapi",
                "sourceNavigationEntry": entry_path,
                "route": f"/{directory}" if directory else None,
                "candidateSourcePath": candidate,
            }
        )
        source_path = self.docs_dir / PurePosixPath(source)
        if not source_path.is_file():
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=f"/{directory}" if directory else None,
                failure_class="missing_openapi_source",
                candidate_source_path=candidate,
            )

    def _collect_href(self, value: Any, entry_path: str) -> None:
        if not isinstance(value, str) or not value:
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=repr(value),
                failure_class="invalid_route_target",
                candidate_source_path=None,
                detail="navigation href must be a non-empty URL string",
            )
            return
        parsed = urlsplit(value)
        if parsed.scheme or value.startswith("//"):
            self.external_navigation.append(
                {
                    "kind": "external",
                    "sourceNavigationEntry": entry_path,
                    "route": value,
                    "candidateSourcePath": "",
                }
            )
            return
        route = normalize_route(parsed.path.lstrip("/"))
        candidate = candidate_source_path(self.docs_dir, route or value)
        if not value.startswith("/") or route is None:
            self.add_diagnostic(
                source_navigation_entry=entry_path,
                route=value,
                failure_class="invalid_route_target",
                candidate_source_path=candidate,
                detail="internal navigation href values must be root-relative routes",
            )
            return
        self._collect_route(route, entry_path)


def normalize_route(value: str) -> str | None:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or value.startswith("/"):
        return None
    path = PurePosixPath(parsed.path)
    if path.suffix or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def bounded_diagnostic_value(value: Any) -> Any:
    if isinstance(value, str) and len(value) > MAX_DIAGNOSTIC_STRING_LENGTH:
        return value[: MAX_DIAGNOSTIC_STRING_LENGTH - 3] + "..."
    return value


def normalize_file_reference(value: str) -> str | None:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value or value.startswith("/"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return None
    path = PurePosixPath(parsed.path)
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def normalize_root_route(value: Any, *, allow_fragment: bool = False) -> str | None:
    if not isinstance(value, str) or not value.startswith("/") or value.startswith("//") or "\\" in value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or (parsed.fragment and not allow_fragment):
        return None
    route = parsed.path.lstrip("/")
    return normalize_route(route)


def candidate_source_path(docs_dir: Path, route: str) -> str:
    return (PurePosixPath(docs_dir.name) / f"{route.lstrip('/')}.mdx").as_posix()


def candidate_config_path(docs_dir: Path, relative_path: str) -> str:
    return (PurePosixPath(docs_dir.name) / relative_path).as_posix()


def is_empty_page(path: Path) -> bool:
    content = path.read_text(encoding="utf-8-sig", errors="replace")
    body = FRONT_MATTER_PATTERN.sub("", content, count=1)
    body = JSX_COMMENT_PATTERN.sub("", body)
    body = HTML_COMMENT_PATTERN.sub("", body)
    return not body.strip()


def _resolve_internal_link(source_route: str, raw_link: str) -> str | None:
    link = raw_link[1:-1] if raw_link.startswith("<") and raw_link.endswith(">") else raw_link
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc or link.startswith(("#", "//")):
        return None
    path = parsed.path
    if not path or "\\" in path or PurePosixPath(path).suffix.lower() in ASSET_SUFFIXES:
        return None

    if path.startswith("/"):
        parts = list(PurePosixPath(path.lstrip("/")).parts)
    else:
        parts = list((PurePosixPath(source_route).parent / path).parts)

    normalized_parts: list[str] = []
    for part in parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized_parts:
                return ""
            normalized_parts.pop()
            continue
        normalized_parts.append(part)
    if not normalized_parts:
        return ""

    suffix = PurePosixPath(normalized_parts[-1]).suffix.lower()
    if suffix in {".md", ".mdx"}:
        normalized_parts[-1] = normalized_parts[-1][: -len(suffix)]
    return "/".join(normalized_parts).rstrip("/")


def _validate_internal_links(collector: NavigationCollector, routes_to_scan: set[str] | None = None) -> None:
    route_entries: dict[str, RouteEntry] = {}
    for entry in collector.routes:
        route_entries.setdefault(entry.route, entry)
    valid_routes = set(route_entries)
    valid_routes.update(alias["route"].lstrip("/") for alias in collector.aliases)
    valid_routes.add("")

    for route, entry in route_entries.items():
        if routes_to_scan is not None and route not in routes_to_scan:
            continue
        source_path = collector.docs_dir / f"{route}.mdx"
        if not source_path.is_file():
            continue
        content = source_path.read_text(encoding="utf-8-sig", errors="replace")
        content = FENCED_CODE_PATTERN.sub("", content)
        content = INLINE_CODE_PATTERN.sub("", content)
        content = JSX_COMMENT_PATTERN.sub("", content)
        content = HTML_COMMENT_PATTERN.sub("", content)
        seen: set[tuple[str, str]] = set()
        for match in LINK_PATTERN.finditer(content):
            raw_link = match.group("markdown") or match.group("href") or match.group("reference")
            target = _resolve_internal_link(route, raw_link)
            if target is None or target in valid_routes:
                continue
            key = (raw_link, target)
            if key in seen:
                continue
            seen.add(key)
            collector.add_diagnostic(
                source_navigation_entry=entry.source_navigation_entry,
                route=f"/{target}" if target else "/",
                failure_class="stale_internal_link",
                candidate_source_path=candidate_source_path(collector.docs_dir, target),
                sourcePage=entry.candidate_source_path,
                link=raw_link,
            )


def validate_navigation(
    docs_dir: Path,
    navigation_path: Path,
    *,
    changed_files: set[str] | None = None,
    base_navigation_path: Path | None = None,
    max_diagnostics: int = DEFAULT_MAX_DIAGNOSTICS,
) -> dict[str, Any]:
    config = json.loads(navigation_path.read_text(encoding="utf-8"))
    collector = NavigationCollector(docs_dir, max_diagnostics)
    collector.collect(config.get("navigation"))
    collector.collect_redirects(config.get("redirects"))
    routes_to_scan: set[str] | None = None
    if changed_files is not None:
        docs_prefix = f"{docs_dir.name}/"
        routes_to_scan = {
            path[len(docs_prefix) : -len(".mdx")]
            for path in changed_files
            if path.startswith(docs_prefix) and path.endswith(".mdx")
        }
        if base_navigation_path is not None and base_navigation_path.is_file():
            base_config = json.loads(base_navigation_path.read_text(encoding="utf-8"))
            base_collector = NavigationCollector(docs_dir, 0)
            base_collector.collect(base_config.get("navigation"))
            base_routes = {entry.route for entry in base_collector.routes}
            routes_to_scan.update(entry.route for entry in collector.routes if entry.route not in base_routes)
    if collector.total_diagnostics:
        routes_to_scan = set()
    _validate_internal_links(collector, routes_to_scan)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "failed" if collector.total_diagnostics else "passed",
        "navigationSource": candidate_config_path(docs_dir, navigation_path.name),
        "routes": [entry.as_dict() for entry in collector.routes],
        "openapi": collector.openapi,
        "aliases": collector.aliases,
        "externalNavigation": collector.external_navigation,
        "diagnosticSummary": {
            "total": collector.total_diagnostics,
            "counts": dict(sorted(collector.diagnostic_counts.items())),
            "truncated": collector.total_diagnostics > len(collector.diagnostics),
        },
        "diagnostics": collector.diagnostics,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=Path("docs-vnext"))
    parser.add_argument("--navigation", type=Path)
    parser.add_argument("--output", type=Path, default=Path("tests/eval_results/docs-vnext-route-inventory.json"))
    parser.add_argument("--changed-files-file", type=Path)
    parser.add_argument("--base-navigation", type=Path)
    parser.add_argument("--max-diagnostics", type=int, default=DEFAULT_MAX_DIAGNOSTICS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    navigation_path = args.navigation or args.docs_dir / "docs.json"
    try:
        changed_files = None
        if args.changed_files_file:
            changed_files = {
                line.strip().replace("\\", "/")
                for line in args.changed_files_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            }
        result = validate_navigation(
            args.docs_dir,
            navigation_path,
            changed_files=changed_files,
            base_navigation_path=args.base_navigation,
            max_diagnostics=args.max_diagnostics,
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Navigation validation could not run: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = result["diagnosticSummary"]
    print(
        f"docs-vnext navigation: {result['status']} "
        f"({len(result['routes'])} routes, {summary['total']} diagnostics); inventory: {args.output}",
        file=sys.stderr,
    )
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
