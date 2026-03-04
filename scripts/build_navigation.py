#!/usr/bin/env python3
"""Build Mintlify navigation from manifest TOC hierarchy.

Reads manifest.json (produced by extract_manifest.py), builds a recursive
navigation tree that preserves the full depth of the upstream toc.yml
hierarchy, and merges it into an existing docs.json template.

Usage:
    python scripts/build_navigation.py [--docs-dir docs-vnext] [--manifest manifest.json]
"""

import argparse
import json
import sys
from pathlib import Path


def _build_tree(pages: list, docs_dir: Path) -> dict:
    """Build an ordered tree from flat pages with hierarchy arrays.

    Each node has:
      '_pages': list of output_path strings (leaf pages at this level)
      '_children': OrderedDict-like dict of {group_name: child_node}
    Insertion order is preserved (Python 3.7+ dicts).
    """
    root: dict = {"_pages": [], "_children": {}}

    for page in pages:
        if page.get("category") in ("cross-repo", "external"):
            continue

        output_path = page.get("output_path", "")
        if not output_path:
            continue

        mdx_path = docs_dir / f"{output_path}.mdx"
        if not mdx_path.exists():
            print(f"  WARN: skipping {output_path} (no MDX file)", file=sys.stderr)
            continue

        hierarchy = page.get("hierarchy", [])
        # hierarchy[0] is the section name (used as the top-level group name)
        # hierarchy[1:-1] are intermediate group names
        # hierarchy[-1] is the page's own name (not used for grouping)
        intermediate = hierarchy[1:-1] if len(hierarchy) > 2 else []

        node = root
        for level in intermediate:
            if level not in node["_children"]:
                node["_children"][level] = {"_pages": [], "_children": {}}
            node = node["_children"][level]

        # Avoid duplicate page entries
        if output_path not in node["_pages"]:
            node["_pages"].append(output_path)

    return root


def _tree_to_nav(node: dict) -> list:
    """Convert a navigation tree node to Mintlify nav format (recursive).

    Returns a list of page strings and sub-group dicts, preserving the
    order pages and sub-groups were first encountered in the TOC.
    """
    # Interleave pages and children in insertion order.
    # Track which children we've already emitted so we can place them
    # at the position of their first page/child.
    result: list = []
    emitted_children: set = set()

    # Pages at this level come first (they appear before any sub-groups
    # in the TOC).
    result.extend(node["_pages"])

    # Then sub-groups
    for child_name, child_node in node["_children"].items():
        if child_name in emitted_children:
            continue
        emitted_children.add(child_name)

        child_pages = _tree_to_nav(child_node)
        if not child_pages:
            continue
        if len(child_pages) == 1 and isinstance(child_pages[0], str):
            # Single-page group: still wrap in a group so the name is visible
            result.append({"group": child_name, "pages": child_pages})
        else:
            result.append({"group": child_name, "pages": child_pages})

    return result


def build_nav_group(section: dict, docs_dir: Path) -> dict | None:
    """Build a Mintlify navigation group from a TOC section."""
    name = section.get("name", "")
    pages = section.get("pages", [])

    if not pages:
        return None

    tree = _build_tree(pages, docs_dir)
    nav_pages = _tree_to_nav(tree)

    if not nav_pages:
        return None

    return {"group": name, "pages": nav_pages}


def _count_pages(nav: list) -> int:
    """Recursively count page references in a navigation structure."""
    count = 0
    for item in nav:
        if isinstance(item, str):
            count += 1
        elif isinstance(item, dict):
            count += _count_pages(item.get("pages", []))
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs-dir", default="docs",
        help="Directory containing .mdx files (default: docs)",
    )
    parser.add_argument(
        "--manifest", default="manifest.json",
        help="Path to manifest.json (default: manifest.json)",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    docs_json_path = docs_dir / "docs.json"

    manifest = json.load(open(args.manifest))

    # Build navigation groups from manifest hierarchy
    navigation = []
    for section in manifest.get("toc_hierarchy", []):
        group = build_nav_group(section, docs_dir)
        if group:
            navigation.append(group)

    # Merge into existing docs.json template if it exists
    if docs_json_path.exists():
        with open(docs_json_path) as f:
            docs_json = json.load(f)
        # Replace just the navigation groups
        docs_json["navigation"] = {
            "tabs": [{"tab": "Documentation", "groups": navigation}]
        }
    else:
        docs_json = {
            "$schema": "https://mintlify.com/docs.json",
            "name": "Microsoft Foundry Docs",
            "theme": "almond",
            "colors": {
                "primary": "#0078D4",
                "light": "#50A0E0",
                "dark": "#003C6B",
            },
            "favicon": "/images/favicon.png",
            "navigation": {
                "tabs": [{"tab": "Documentation", "groups": navigation}]
            },
            "footerSocials": {
                "github": "https://github.com/MicrosoftDocs/azure-ai-docs-pr"
            },
        }

    with open(docs_json_path, "w") as f:
        json.dump(docs_json, f, indent=2)
        f.write("\n")

    total_pages = sum(_count_pages(g.get("pages", [])) for g in navigation)
    print(
        f"Navigation built: {len(navigation)} groups, {total_pages} pages",
        file=sys.stderr,
    )
    print(f"Written to {docs_json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
