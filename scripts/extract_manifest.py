#!/usr/bin/env python3
"""Extract manifest from Microsoft Foundry TOC files.

Parses the root toc.yml and all sub-TOC YAML files from MicrosoftDocs/azure-ai-docs,
resolves paths, deduplicates, and outputs manifest.json.
"""

import json
import re
import subprocess
import sys
from pathlib import PurePosixPath
from urllib.parse import urlparse

import yaml

REPO_OWNER = "MicrosoftDocs"
REPO_NAME = "azure-ai-docs"
ROOT_TOC_PATH = "articles/ai-foundry/default/toc.yml"

# Section name → output directory mapping
SECTION_SLUG_MAP = {
    "What is Microsoft Foundry (new)?": "overview",
    "Get started": "get-started",
    "Agent development": "agents/development",
    "Agent tools & integration": "agents/tools",
    "Model catalog": "models/catalog",
    "Model capabilities": "models/capabilities",
    "Fine-tuning": "models/fine-tuning",
    "Manage agents, models, & tools": "manage",
    "Observability, evaluation, & tracing": "observability",
    "Developer experience": "developer-experience",
    "API & SDK": "api-sdk",
    "Guardrails and controls": "guardrails",
    "Responsible AI": "responsible-ai",
    "Best practices": "best-practices",
    "Setup & configure": "setup",
    "Security & governance": "security",
    "Operate & support": "operate",
}


def gh_get_file(path: str, ref: str = "main") -> str:
    """Fetch a file from GitHub using the gh CLI."""
    result = subprocess.run(
        ["gh", "api", f"/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
         "-H", "Accept: application/vnd.github.raw+json",
         "--method", "GET"],
        capture_output=True, text=True, check=True
    )
    return result.stdout


def resolve_path(href: str, toc_dir: str) -> str:
    """Resolve a relative href against a TOC file's directory."""
    href = re.sub(r'\?.*$', '', href)  # strip query params
    href = href.replace('\\', '/')  # normalize Windows backslashes
    combined = PurePosixPath(toc_dir) / href
    parts = []
    for part in combined.parts:
        if part == '..':
            if parts:
                parts.pop()
        elif part != '.':
            parts.append(part)
    return '/'.join(parts)


def categorize_href(href: str) -> str:
    """Categorize an href as in-repo-md, in-repo-yml, external, or cross-repo."""
    if href.startswith('http://') or href.startswith('https://'):
        return 'external'
    clean = re.sub(r'\?.*$', '', href)
    if clean.startswith('/azure/') or clean.startswith('/rest/'):
        return 'cross-repo'
    if clean.endswith('.md'):
        return 'in-repo-md'
    if clean.endswith('.yml') or clean.endswith('.yaml'):
        return 'in-repo-yml'
    return 'external'


def parse_toc_items(items: list, toc_dir: str, section: str, hierarchy: list) -> list:
    """Recursively parse TOC items, resolving paths."""
    entries = []
    for item in items:
        name = item.get('name', '')
        href = item.get('href', '')
        sub_items = item.get('items', [])
        current_hierarchy = hierarchy + [name]

        if href:
            cat = categorize_href(href)
            if cat == 'in-repo-md' or cat == 'in-repo-yml':
                resolved = resolve_path(href, toc_dir)
                entries.append({
                    'name': name,
                    'source_path': resolved,
                    'category': cat,
                    'section': section,
                    'hierarchy': current_hierarchy,
                })
            elif cat == 'cross-repo':
                clean_href = re.sub(r'\?.*$', '', href)
                entries.append({
                    'name': name,
                    'source_path': clean_href,
                    'category': cat,
                    'section': section,
                    'hierarchy': current_hierarchy,
                    'url': f"https://learn.microsoft.com{clean_href}",
                })
            elif cat == 'external':
                entries.append({
                    'name': name,
                    'source_path': href,
                    'category': cat,
                    'section': section,
                    'hierarchy': current_hierarchy,
                })

        if sub_items:
            entries.extend(parse_toc_items(sub_items, toc_dir, section, current_hierarchy))

    return entries


def parse_sub_toc(toc_path: str, section: str) -> list:
    """Parse a sub-TOC YAML file."""
    try:
        content = gh_get_file(toc_path)
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: Could not fetch {toc_path}: {e.stderr}", file=sys.stderr)
        return []

    data = yaml.safe_load(content)
    if not data or 'items' not in data:
        return []

    toc_dir = str(PurePosixPath(toc_path).parent)
    return parse_toc_items(data['items'], toc_dir, section, [section])


def scan_doc_for_includes(source_path: str) -> list[str]:
    """Scan a markdown file for [!INCLUDE] references."""
    try:
        content = gh_get_file(source_path)
    except subprocess.CalledProcessError:
        return []

    includes = []
    for match in re.finditer(r'\[!INCLUDE\s+\[.*?\]\((.*?)\)\]', content):
        inc_path = match.group(1)
        resolved = resolve_path(inc_path, str(PurePosixPath(source_path).parent))
        includes.append(resolved)
    return includes


def scan_doc_for_images(source_path: str) -> list[str]:
    """Scan a markdown file for :::image references."""
    try:
        content = gh_get_file(source_path)
    except subprocess.CalledProcessError:
        return []

    doc_dir = str(PurePosixPath(source_path).parent)
    images = []
    for match in re.finditer(r':::image[^:]*source="([^"]+)"', content):
        img_path = match.group(1)
        if img_path.startswith('/azure/'):
            # Absolute MS Learn path — convert to repo-relative articles/ path
            images.append('articles' + img_path)
        else:
            resolved = resolve_path(img_path, doc_dir)
            images.append(resolved)
    # Also catch standard markdown images
    for match in re.finditer(r'!\[.*?\]\(([^)]+)\)', content):
        img_path = match.group(1)
        if img_path.startswith('http') or img_path.startswith('~/'):
            continue
        if img_path.startswith('/azure/'):
            images.append('articles' + img_path)
        else:
            resolved = resolve_path(img_path, doc_dir)
            images.append(resolved)
    return images


def build_output_path(entry: dict) -> str:
    """Build Mintlify output path from entry metadata."""
    section_slug = SECTION_SLUG_MAP.get(entry['section'], entry['section'].lower().replace(' ', '-'))
    source = PurePosixPath(entry['source_path'])
    stem = source.stem
    # Use section slug + filename
    return f"{section_slug}/{stem}"


def main():
    print("Fetching root TOC...", file=sys.stderr)
    root_content = gh_get_file(ROOT_TOC_PATH)
    root_toc = yaml.safe_load(root_content)

    root_dir = str(PurePosixPath(ROOT_TOC_PATH).parent)
    all_entries = []
    toc_hierarchy = []

    for item in root_toc.get('items', []):
        section_name = item.get('name', '')
        href = item.get('href', '')

        if not href:
            continue

        cat = categorize_href(href)
        toc_section = {
            'name': section_name,
            'slug': SECTION_SLUG_MAP.get(section_name, section_name.lower().replace(' ', '-')),
            'pages': [],
        }

        if href.endswith('toc.yml'):
            # Sub-TOC reference
            toc_path = resolve_path(href, root_dir)
            print(f"Parsing sub-TOC: {section_name} ({toc_path})", file=sys.stderr)
            entries = parse_sub_toc(toc_path, section_name)
            for e in entries:
                e['output_path'] = build_output_path(e)
            all_entries.extend(entries)
            toc_section['pages'] = entries
        elif cat in ('in-repo-md', 'in-repo-yml'):
            # Direct doc reference
            resolved = resolve_path(href, root_dir)
            entry = {
                'name': section_name,
                'source_path': resolved,
                'category': cat,
                'section': section_name,
                'hierarchy': [section_name],
            }
            entry['output_path'] = build_output_path(entry)
            all_entries.append(entry)
            toc_section['pages'] = [entry]

        toc_hierarchy.append(toc_section)

    # Deduplicate by source_path
    seen = {}
    deduped = []
    for entry in all_entries:
        sp = entry['source_path']
        if sp not in seen:
            seen[sp] = entry
            deduped.append(entry)
        else:
            # Keep the first occurrence but note the duplicate
            seen[sp].setdefault('also_in_sections', []).append(entry['section'])

    # Scan in-repo docs for includes and images
    print(f"\nFound {len(deduped)} unique docs. Scanning for includes and images...", file=sys.stderr)
    all_includes = set()
    all_images = set()

    for entry in deduped:
        if entry['category'] == 'in-repo-md':
            includes = scan_doc_for_includes(entry['source_path'])
            if includes:
                entry['includes'] = includes
                all_includes.update(includes)
            images = scan_doc_for_images(entry['source_path'])
            if images:
                entry['images'] = images
                all_images.update(images)

    # Recursively scan include files for nested includes AND images
    scanned_includes = set()
    to_scan = list(all_includes)
    while to_scan:
        inc_path = to_scan.pop()
        if inc_path in scanned_includes:
            continue
        scanned_includes.add(inc_path)
        nested = scan_doc_for_includes(inc_path)
        for n in nested:
            if n not in all_includes:
                all_includes.add(n)
                to_scan.append(n)
        # Also scan includes for image references
        inc_images = scan_doc_for_images(inc_path)
        all_images.update(inc_images)

    if scanned_includes:
        print(f"  Scanned {len(scanned_includes)} include files, found {len(all_includes)} total (including nested)", file=sys.stderr)

    manifest = {
        'repo': f"{REPO_OWNER}/{REPO_NAME}",
        'root_toc': ROOT_TOC_PATH,
        'stats': {
            'total_docs': len(deduped),
            'in_repo_md': len([e for e in deduped if e['category'] == 'in-repo-md']),
            'in_repo_yml': len([e for e in deduped if e['category'] == 'in-repo-yml']),
            'cross_repo': len([e for e in deduped if e['category'] == 'cross-repo']),
            'external': len([e for e in deduped if e['category'] == 'external']),
            'include_files': len(all_includes),
            'image_files': len(all_images),
        },
        'toc_hierarchy': toc_hierarchy,
        'docs': deduped,
        'includes': sorted(all_includes),
        'images': sorted(all_images),
    }

    output_path = 'manifest.json'
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to {output_path}", file=sys.stderr)
    print(f"  Total docs: {manifest['stats']['total_docs']}", file=sys.stderr)
    print(f"  In-repo .md: {manifest['stats']['in_repo_md']}", file=sys.stderr)
    print(f"  In-repo .yml: {manifest['stats']['in_repo_yml']}", file=sys.stderr)
    print(f"  Cross-repo: {manifest['stats']['cross_repo']}", file=sys.stderr)
    print(f"  External: {manifest['stats']['external']}", file=sys.stderr)
    print(f"  Include files: {manifest['stats']['include_files']}", file=sys.stderr)
    print(f"  Image files: {manifest['stats']['image_files']}", file=sys.stderr)


if __name__ == '__main__':
    main()
