#!/usr/bin/env python3
"""Build Mintlify navigation from manifest TOC hierarchy.

Generates docs.json with full navigation structure.
"""

import json
import os
import sys
from pathlib import Path

DOCS_DIR = Path("docs")


def build_nav_group(section: dict) -> dict | None:
    """Build a Mintlify navigation group from a TOC section."""
    name = section.get("name", "")
    slug = section.get("slug", "")
    pages = section.get("pages", [])

    if not pages:
        return None

    # Build page entries, respecting hierarchy
    nav_pages = []
    sub_groups = {}

    for page in pages:
        if page.get("category") in ("cross-repo", "external"):
            continue

        output_path = page.get("output_path", "")
        if not output_path:
            continue

        # Check the MDX file exists
        mdx_path = DOCS_DIR / f"{output_path}.mdx"
        if not mdx_path.exists():
            continue

        hierarchy = page.get("hierarchy", [])
        if len(hierarchy) > 2:
            # Nested under a sub-group
            sub_group_name = hierarchy[1]
            if sub_group_name not in sub_groups:
                sub_groups[sub_group_name] = []
            sub_groups[sub_group_name].append(output_path)
        else:
            nav_pages.append(output_path)

    # Build the group
    group_pages = []

    # Add direct pages
    group_pages.extend(nav_pages)

    # Add sub-groups
    for sg_name, sg_pages in sub_groups.items():
        if len(sg_pages) == 1:
            group_pages.append(sg_pages[0])
        else:
            group_pages.append({
                "group": sg_name,
                "pages": sg_pages
            })

    if not group_pages:
        return None

    return {
        "group": name,
        "pages": group_pages
    }


def main():
    manifest = json.load(open("manifest.json"))

    navigation = []
    for section in manifest.get("toc_hierarchy", []):
        group = build_nav_group(section)
        if group:
            navigation.append(group)

    docs_json = {
        "$schema": "https://mintlify.com/docs.json",
        "name": "Microsoft Foundry Docs",
        "theme": "quill",
        "colors": {
            "primary": "#0078D4",
            "light": "#50A0E0",
            "dark": "#003C6B"
        },
        "favicon": "/images/favicon.png",
        "navigation": {
            "tabs": [
                {
                    "tab": "Documentation",
                    "groups": navigation
                }
            ]
        },
        "footerSocials": {
            "github": "https://github.com/MicrosoftDocs/azure-ai-docs"
        }
    }

    with open("docs.json", "w") as f:
        json.dump(docs_json, f, indent=2)

    total_pages = sum(
        len(g.get("pages", [])) for g in navigation
    )
    print(f"Navigation built: {len(navigation)} groups, ~{total_pages} top-level entries", file=sys.stderr)
    print("Written to docs.json", file=sys.stderr)


if __name__ == "__main__":
    main()
