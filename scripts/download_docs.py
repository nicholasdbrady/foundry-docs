#!/usr/bin/env python3
"""Download docs from GitHub based on manifest.json.

Fetches all in-repo .md, .yml, include, and media files via GitHub raw URLs.
Organizes into a Mintlify-friendly directory structure and creates path_map.json.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_OWNER = "MicrosoftDocs"
REPO_NAME = "azure-ai-docs"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main"
DOCS_DIR = Path("docs")
RAW_DIR = Path("raw_docs")  # raw downloaded files before conversion
MAX_WORKERS = 10


def download_file(source_path: str, dest_path: Path) -> bool:
    """Download a file from GitHub raw content."""
    if dest_path.exists():
        return True

    url = f"{RAW_BASE}/{source_path}"
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["curl", "-sL", "-o", str(dest_path), "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=30
        )
        http_code = result.stdout.strip()
        if http_code == "200":
            return True
        else:
            dest_path.unlink(missing_ok=True)
            return False
    except Exception as e:
        print(f"  ERROR downloading {source_path}: {e}", file=sys.stderr)
        return False


def download_gh_api(source_path: str, dest_path: Path) -> bool:
    """Download using gh CLI (handles auth better for edge cases)."""
    if dest_path.exists():
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            ["gh", "api", f"/repos/{REPO_OWNER}/{REPO_NAME}/contents/{source_path}",
             "-H", "Accept: application/vnd.github.raw+json"],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            dest_path.write_bytes(result.stdout)
            return True
        return False
    except Exception:
        return False


def main():
    manifest = json.load(open("manifest.json"))

    # Collect all files to download
    files_to_download = []

    # 1. In-repo .md and .yml docs
    for doc in manifest["docs"]:
        if doc["category"] in ("in-repo-md", "in-repo-yml"):
            source = doc["source_path"]
            dest = RAW_DIR / source
            files_to_download.append((source, dest, "doc"))

    # 2. Include files
    for inc_path in manifest.get("includes", []):
        # Skip cross-repo includes (contain ~/reusable-content or similar)
        if "~/reusable-content" in inc_path or inc_path.startswith("/"):
            continue
        dest = RAW_DIR / inc_path
        files_to_download.append((inc_path, dest, "include"))

    # 3. Image files
    for img_path in manifest.get("images", []):
        if img_path.startswith("/") or img_path.startswith("http"):
            continue
        dest = RAW_DIR / img_path
        files_to_download.append((img_path, dest, "image"))

    print(f"Files to download: {len(files_to_download)}", file=sys.stderr)
    print(f"  Docs: {len([f for f in files_to_download if f[2] == 'doc'])}", file=sys.stderr)
    print(f"  Includes: {len([f for f in files_to_download if f[2] == 'include'])}", file=sys.stderr)
    print(f"  Images: {len([f for f in files_to_download if f[2] == 'image'])}", file=sys.stderr)

    # Download in parallel
    success = 0
    failed = 0
    failed_files = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for source, dest, ftype in files_to_download:
            future = executor.submit(download_file, source, dest)
            futures[future] = (source, dest, ftype)

        for i, future in enumerate(as_completed(futures)):
            source, dest, ftype = futures[future]
            try:
                if future.result():
                    success += 1
                else:
                    # Retry with gh API
                    if download_gh_api(source, dest):
                        success += 1
                    else:
                        failed += 1
                        failed_files.append(source)
            except Exception as e:
                failed += 1
                failed_files.append(source)

            if (i + 1) % 50 == 0:
                print(f"  Progress: {i + 1}/{len(files_to_download)} ({success} ok, {failed} failed)", file=sys.stderr)

    print(f"\nDownload complete: {success} succeeded, {failed} failed", file=sys.stderr)
    if failed_files:
        print(f"Failed files:", file=sys.stderr)
        for f in failed_files[:20]:
            print(f"  {f}", file=sys.stderr)
        if len(failed_files) > 20:
            print(f"  ... and {len(failed_files) - 20} more", file=sys.stderr)

    # Build path_map.json (source_path → output_path)
    path_map = {}
    for doc in manifest["docs"]:
        if doc["category"] == "in-repo-md":
            output = doc.get("output_path", "")
            if output:
                path_map[doc["source_path"]] = output

    with open("path_map.json", "w") as f:
        json.dump(path_map, f, indent=2)

    print(f"Path map written with {len(path_map)} entries", file=sys.stderr)


if __name__ == "__main__":
    main()
