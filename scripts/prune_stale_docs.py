#!/usr/bin/env python3
"""Remove stale MDX files that are no longer part of the published navigation.

Compares files on disk in the docs directory against the current
docs.json navigation tree (the source of truth for what's actually
published) and deletes any .mdx files that aren't referenced anywhere in
it. Falls back to manifest.json's flat doc list only if no docs.json is
present (e.g. for a docs directory without navigation).

manifest.json's flat "docs" list is not used as the primary source because
a page can be cross-listed under multiple TOC sections (see
"also_in_sections"): only one of its several possible output_path values
ends up in the flat list, while the others are only visible via
toc_hierarchy / docs.json. Comparing against docs.json avoids incorrectly
flagging those still-published pages as stale.

Usage:
    python scripts/prune_stale_docs.py [--docs-dir docs] [--nav-file docs/docs.json] [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

# Files that are manually maintained and should never be pruned,
# even if they don't appear in the navigation.
KEEP = {
    "api-sdk/sdk-api-reference",
}


def _collect_nav_pages(nav_json: dict) -> set[str]:
    """Recursively collect every page path referenced in a Mintlify docs.json."""
    pages: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, str):
            pages.add(node)
        elif isinstance(node, dict):
            for key in ("tabs", "groups", "pages", "anchors", "children"):
                if key in node:
                    walk(node[key])
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(nav_json.get("navigation", {}))
    return pages


def _collect_manifest_paths(manifest: dict) -> set[str]:
    paths: set[str] = set()
    for doc in manifest.get("docs", []):
        op = doc.get("output_path", "")
        if op:
            paths.add(op)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs-dir", default="docs",
        help="Directory containing .mdx files (default: docs)",
    )
    parser.add_argument(
        "--nav-file", default=None,
        help="Path to docs.json navigation (default: <docs-dir>/docs.json)",
    )
    parser.add_argument(
        "--manifest", default="manifest.json",
        help="Path to manifest.json, used only if --nav-file is missing (default: manifest.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print files that would be removed without deleting them.",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    nav_file = Path(args.nav_file) if args.nav_file else docs_dir / "docs.json"

    if nav_file.exists():
        known_paths = _collect_nav_pages(json.load(open(nav_file)))
    else:
        known_paths = _collect_manifest_paths(json.load(open(args.manifest)))

    # Walk the docs directory and find .mdx files that aren't published.
    # Use as_posix() so this comparison is correct on Windows too, where
    # relative_to() yields backslash-separated paths that would otherwise
    # never match the forward-slash paths in the navigation/manifest.
    stale: list[Path] = []
    for mdx_file in sorted(docs_dir.rglob("*.mdx")):
        rel = mdx_file.relative_to(docs_dir).with_suffix("").as_posix()
        if rel not in known_paths and rel not in KEEP:
            stale.append(mdx_file)

    if not stale:
        print("No stale files found.", file=sys.stderr)
        return

    verb = "Would remove" if args.dry_run else "Removing"
    for path in stale:
        rel = str(path.relative_to(docs_dir))
        print(f"  {verb}: {rel}", file=sys.stderr)
        if not args.dry_run:
            path.unlink()

    # Clean up empty directories
    if not args.dry_run:
        for dirpath in sorted(docs_dir.rglob("*"), reverse=True):
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                dirpath.rmdir()
                print(f"  Removed empty dir: {dirpath.relative_to(docs_dir)}", file=sys.stderr)

    print(
        f"\n{'Would remove' if args.dry_run else 'Removed'} {len(stale)} stale file(s).",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
