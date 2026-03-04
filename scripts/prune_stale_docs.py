#!/usr/bin/env python3
"""Remove stale MDX files that are no longer in the upstream manifest.

Compares files on disk in the docs directory against the current
manifest.json and deletes any .mdx files whose output_path no longer
appears.  Preserves manually-created files listed in a keep list.

Usage:
    python scripts/prune_stale_docs.py [--docs-dir docs] [--manifest manifest.json] [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

# Files that are manually maintained and should never be pruned,
# even if they don't appear in the manifest.
KEEP = {
    "api-sdk/sdk-api-reference",
}


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
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print files that would be removed without deleting them.",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    manifest = json.load(open(args.manifest))

    # Collect all output_paths the manifest knows about
    manifest_paths: set[str] = set()
    for doc in manifest.get("docs", []):
        op = doc.get("output_path", "")
        if op:
            manifest_paths.add(op)

    # Walk the docs directory and find .mdx files not in the manifest
    stale: list[Path] = []
    for mdx_file in sorted(docs_dir.rglob("*.mdx")):
        rel = str(mdx_file.relative_to(docs_dir)).replace(".mdx", "")
        if rel not in manifest_paths and rel not in KEEP:
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
