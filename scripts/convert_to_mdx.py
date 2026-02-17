#!/usr/bin/env python3
"""Convert Microsoft Learn markdown to Mintlify MDX format.

Handles: moniker filtering, include resolution, front matter, callouts,
tabs, images, zone pivots, link rewriting, code includes, and YML FAQ docs.
"""

import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

import yaml

RAW_DIR = Path("raw_docs")
DOCS_DIR = Path("docs")

# Load manifest and path map
MANIFEST = json.load(open("manifest.json"))
PATH_MAP = json.load(open("path_map.json"))

# Build reverse lookup: source_path → output_path
SOURCE_TO_OUTPUT = {}
for doc in MANIFEST["docs"]:
    if doc["category"] == "in-repo-md" and "output_path" in doc:
        SOURCE_TO_OUTPUT[doc["source_path"]] = doc["output_path"]


def resolve_include_path(inc_ref: str, current_file: str) -> str | None:
    """Resolve an include reference relative to current file."""
    current_dir = str(PurePosixPath(current_file).parent)
    combined = PurePosixPath(current_dir) / inc_ref
    parts = []
    for part in combined.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return "/".join(parts)


def strip_include_front_matter(content: str) -> str:
    """Strip YAML front matter from include file content."""
    fm_match = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)
    if fm_match:
        return content[fm_match.end():]
    return content


def read_include(inc_path: str) -> str:
    """Read an include file from raw_docs, stripping its front matter."""
    full_path = RAW_DIR / inc_path
    if full_path.exists():
        content = full_path.read_text(encoding="utf-8", errors="replace").strip()
        return strip_include_front_matter(content)
    return ""


def resolve_includes(content: str, source_path: str, depth: int = 0) -> str:
    """Recursively resolve [!INCLUDE] references."""
    if depth > 5:
        return content

    def replace_include(match):
        inc_ref = match.group(2)
        resolved = resolve_include_path(inc_ref, source_path)
        if resolved:
            inc_content = read_include(resolved)
            if inc_content:
                # Recursively resolve includes in the included content
                return resolve_includes(inc_content, resolved, depth + 1)
        return ""

    return re.sub(
        r'\[!INCLUDE\s+\[([^\]]*)\]\(([^)]+)\)\]',
        replace_include,
        content
    )


def filter_monikers(content: str) -> str:
    """Keep 'foundry' moniker content, remove 'foundry-classic' blocks."""
    # Handle :::moniker range="foundry-classic" ... :::moniker-end → remove
    content = re.sub(
        r':::moniker\s+range="foundry-classic"\s*\n(.*?):::moniker-end',
        '',
        content,
        flags=re.DOTALL
    )
    # Handle ::: moniker range="foundry-classic" (with space)
    content = re.sub(
        r'::: moniker\s+range="foundry-classic"\s*\n(.*?)::: moniker-end',
        '',
        content,
        flags=re.DOTALL
    )
    # Handle :::moniker range="foundry" ... :::moniker-end → keep content
    content = re.sub(
        r':::moniker\s+range="foundry"\s*\n(.*?):::moniker-end',
        r'\1',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'::: moniker\s+range="foundry"\s*\n(.*?)::: moniker-end',
        r'\1',
        content,
        flags=re.DOTALL
    )
    # Handle combined monikers :::moniker range="foundry-classic || foundry"
    content = re.sub(
        r':::moniker\s+range="foundry-classic \|\| foundry"\s*\n(.*?):::moniker-end',
        r'\1',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'::: moniker\s+range="foundry-classic \|\| foundry"\s*\n(.*?)::: moniker-end',
        r'\1',
        content,
        flags=re.DOTALL
    )
    return content


def simplify_front_matter(content: str) -> tuple[str, dict]:
    """Extract and simplify YAML front matter."""
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match:
        return content, {}

    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError:
        fm = {}

    if not isinstance(fm, dict):
        fm = {}

    # Keep only useful fields
    simplified = {}
    if fm.get("title"):
        simplified["title"] = fm["title"]
    if fm.get("description"):
        simplified["description"] = fm["description"]
    if fm.get("titleSuffix"):
        simplified["sidebarTitle"] = fm.get("title", "")

    body = content[fm_match.end():]
    return body, simplified


def convert_callouts(content: str) -> str:
    """Convert > [!TIP], > [!NOTE], > [!WARNING], > [!IMPORTANT], > [!CAUTION] to MDX callouts."""
    callout_map = {
        "TIP": "Tip",
        "NOTE": "Note",
        "WARNING": "Warning",
        "IMPORTANT": "Info",
        "CAUTION": "Danger",
    }

    def replace_callout(match):
        callout_type = match.group(1).upper()
        component = callout_map.get(callout_type, "Note")
        # Get the remaining lines of the blockquote
        block_content = match.group(2)
        # Remove leading > from each line
        lines = []
        for line in block_content.split("\n"):
            stripped = re.sub(r"^>\s?", "", line)
            lines.append(stripped)
        inner = "\n".join(lines).strip()
        return f"<{component}>\n{inner}\n</{component}>"

    # Match > [!TYPE]\n> content lines (greedy within blockquote)
    pattern = r'>\s*\[!(TIP|NOTE|WARNING|IMPORTANT|CAUTION)\]\s*\n((?:>.*\n?)*)'
    content = re.sub(pattern, replace_callout, content, flags=re.IGNORECASE)
    return content


def convert_nextstep(content: str) -> str:
    """Convert > [!div class="nextstepaction"] blocks to Mintlify Card links."""
    def replace_nextstep(match):
        block = re.sub(r'^>\s?', '', match.group(1), flags=re.MULTILINE).strip()
        # Extract markdown links from the block
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', block)
        if links:
            cards = []
            for text, href in links:
                cards.append(f'<Card title="{text}" icon="arrow-right" href="{href}" />')
            return "\n".join(cards)
        return block

    content = re.sub(
        r'>\s*\[!div\s+class="nextstepaction"\]\s*\n((?:>.*\n?)*)',
        replace_nextstep,
        content
    )
    return content


def convert_checklists(content: str) -> str:
    """Convert > [!div class="checklist"] blocks to Mintlify Check components."""
    def replace_checklist(match):
        block = match.group(1)
        lines = []
        for line in block.split("\n"):
            stripped = re.sub(r'^>\s?', '', line).strip()
            if stripped.startswith("* ") or stripped.startswith("- "):
                item = stripped[2:].strip()
                lines.append(f"<Check>{item}</Check>")
            elif stripped:
                lines.append(stripped)
        return "\n".join(lines)

    content = re.sub(
        r'>\s*\[!div\s+class="checklist"\]\s*\n((?:>.*\n?)*)',
        replace_checklist,
        content
    )
    return content


def convert_selectors(content: str) -> str:
    """Convert > [!div class="op_single_selector"] blocks to Mintlify Tabs."""
    def replace_selector(match):
        block = match.group(1)
        tabs = []
        for line in block.split("\n"):
            stripped = re.sub(r'^>\s?', '', line).strip()
            link_match = re.match(r'^-\s*\[([^\]]+)\]\(([^)]+)\)', stripped)
            if link_match:
                title = link_match.group(1)
                href = link_match.group(2)
                tabs.append(f'  <Tab title="{title}">\n    [{title}]({href})\n  </Tab>')
        if tabs:
            return "<Tabs>\n" + "\n".join(tabs) + "\n</Tabs>"
        return ""

    content = re.sub(
        r'>\s*\[!div\s+class="op_single_selector"\]\s*\n((?:>.*\n?)*)',
        replace_selector,
        content
    )
    # Multi-selector — convert to plain links (no clean Mintlify mapping)
    content = re.sub(
        r'>\s*\[!div\s+class="op_multi_selector"[^\]]*\]\s*\n((?:>.*\n?)*)',
        lambda m: re.sub(r'^>\s?', '', m.group(1), flags=re.MULTILINE),
        content
    )
    return content


def convert_columns(content: str) -> str:
    """Convert :::row:::/:::column::: blocks to Mintlify Columns/Card layout."""
    # Count columns in each row to set cols attribute
    def replace_row(match):
        row_content = match.group(1)
        # Split by column markers
        columns = re.split(r':::column[^:]*:::\s*\n?', row_content)
        columns = [re.sub(r':::column-end:::\s*\n?', '', c).strip() for c in columns if c.strip()]
        if not columns:
            return ""
        n = len(columns)
        cards = []
        for col in columns:
            cards.append(f"  <Card>\n    {col}\n  </Card>")
        return f'<Columns cols={{{n}}}>\n' + "\n".join(cards) + "\n</Columns>"

    content = re.sub(
        r':::row:::\s*\n(.*?):::row-end:::\s*\n?',
        replace_row,
        content,
        flags=re.DOTALL,
    )
    return content


def strip_table_wrappers(content: str) -> str:
    """Strip [!div class="mx-tdBreakAll"] and similar table CSS wrappers."""
    content = re.sub(
        r'>\s*\[!div\s+class="mx-td[^"]*"\]\s*\n((?:>.*\n?)*)',
        lambda m: re.sub(r'^>\s?', '', m.group(1), flags=re.MULTILINE),
        content
    )
    return content


def convert_images(content: str) -> str:
    """Convert :::image to Mintlify components.

    - type="content" / default → <Frame><img ... /></Frame>
    - type="complex" with :::image-end::: → <Frame caption="long desc"><img ... /></Frame>
    - type="icon" → <img ... /> (no alt, no frame)
    - lightbox → wraps in <Frame> (Mintlify supports zoom by default)
    """
    # First: handle complex images with long descriptions (multi-line :::image ... :::image-end:::)
    def replace_complex_image(match):
        tag = match.group(1)
        long_desc = match.group(2).strip()
        source = re.search(r'source="([^"]+)"', tag)
        alt = re.search(r'alt-text="([^"]+)"', tag)
        src = source.group(1) if source else ""
        alt_text = alt.group(1) if alt else ""
        src = re.sub(r'\?.*$', '', src)
        if src and not src.startswith("http"):
            src = f"/images/{PurePosixPath(src).name}"
        caption = long_desc.replace('"', '\\"') if long_desc else ""
        if caption:
            return f'<Frame caption="{caption}">\n  <img src="{src}" alt="{alt_text}" />\n</Frame>'
        return f'<Frame>\n  <img src="{src}" alt="{alt_text}" />\n</Frame>'

    content = re.sub(
        r':::image\s+(.*?):::\s*\n(.*?):::image-end:::',
        replace_complex_image,
        content,
        flags=re.DOTALL,
    )

    # Then: handle single-line :::image ... :::
    def replace_image(match):
        full = match.group(0)
        img_type = re.search(r'type="([^"]+)"', full)
        source = re.search(r'source="([^"]+)"', full)
        alt = re.search(r'alt-text="([^"]+)"', full)
        src = source.group(1) if source else ""
        alt_text = alt.group(1) if alt else ""
        src = re.sub(r'\?.*$', '', src)
        if src and not src.startswith("http"):
            src = f"/images/{PurePosixPath(src).name}"

        # Icons: no frame, no alt required
        if img_type and img_type.group(1) == "icon":
            return f'<img src="{src}" />'

        # Content and default: wrap in Frame
        return f'<Frame>\n  <img src="{src}" alt="{alt_text}" />\n</Frame>'

    content = re.sub(
        r':::image[^:]*?:::', replace_image, content, flags=re.DOTALL
    )
    return content


def convert_tabs(content: str) -> str:
    """Convert # [Tab Title](#tab/id) ... --- patterns to <Tabs>/<Tab> components."""
    lines = content.split("\n")
    result = []
    i = 0
    in_tabs = False
    current_tab_content = []
    current_tab_title = ""

    while i < len(lines):
        line = lines[i]

        # Check for tab header: # [Title](#tab/id)
        tab_match = re.match(r'^#\s+\[([^\]]+)\]\(#tab/([^)]+)\)\s*$', line)

        if tab_match:
            tab_title = tab_match.group(1)

            if not in_tabs:
                # Start new tabs group
                in_tabs = True
                result.append("<Tabs>")
                current_tab_title = tab_title
                current_tab_content = []
            else:
                # Close previous tab, start new one
                result.append(f'  <Tab title="{current_tab_title}">')
                result.extend(f"    {l}" if l.strip() else "" for l in current_tab_content)
                result.append("  </Tab>")
                current_tab_title = tab_title
                current_tab_content = []
            i += 1
            continue

        # Tab separator ---
        if in_tabs and line.strip() == "---":
            # Close the last tab and the tabs group
            result.append(f'  <Tab title="{current_tab_title}">')
            result.extend(f"    {l}" if l.strip() else "" for l in current_tab_content)
            result.append("  </Tab>")
            result.append("</Tabs>")
            in_tabs = False
            current_tab_content = []
            current_tab_title = ""
            i += 1
            continue

        if in_tabs:
            current_tab_content.append(line)
        else:
            result.append(line)

        i += 1

    # Handle unclosed tabs
    if in_tabs:
        result.append(f'  <Tab title="{current_tab_title}">')
        result.extend(f"    {l}" if l.strip() else "" for l in current_tab_content)
        result.append("  </Tab>")
        result.append("</Tabs>")

    return "\n".join(result)


def convert_zone_pivots(content: str) -> str:
    """Convert :::zone pivot="..." blocks. Keep content, strip markers."""
    content = re.sub(r':::zone\s+pivot="[^"]*"\s*\n?', '', content)
    content = re.sub(r'::: zone\s+pivot="[^"]*"\s*\n?', '', content)
    content = re.sub(r':::zone-end\s*\n?', '', content)
    content = re.sub(r'::: zone-end\s*\n?', '', content)
    return content


def rewrite_links(content: str, source_path: str) -> str:
    """Rewrite internal links and externalize cross-repo refs."""
    def rewrite_link(match):
        text = match.group(1)
        href = match.group(2)

        # Strip query params
        clean_href = re.sub(r'\?.*$', '', href)

        # External links - keep as-is
        if clean_href.startswith("http://") or clean_href.startswith("https://"):
            return f"[{text}]({href})"

        # Absolute /azure/... paths → learn.microsoft.com URLs
        if clean_href.startswith("/azure/") or clean_href.startswith("/rest/") or clean_href.startswith("/dotnet/") or clean_href.startswith("/python/") or clean_href.startswith("/javascript/") or clean_href.startswith("/cli/") or clean_href.startswith("/java/"):
            return f"[{text}](https://learn.microsoft.com{clean_href})"

        # Relative .md links → try to map to output path
        if clean_href.endswith(".md") or ".md#" in href:
            anchor = ""
            path_part = clean_href
            if "#" in clean_href:
                path_part, anchor = clean_href.split("#", 1)
                anchor = f"#{anchor}"

            resolved = resolve_include_path(path_part, source_path)
            if resolved and resolved in SOURCE_TO_OUTPUT:
                output = SOURCE_TO_OUTPUT[resolved]
                return f"[{text}](/{output}{anchor})"

        return f"[{text}]({clean_href})"

    # Match markdown links [text](url) but not images ![text](url)
    content = re.sub(r'(?<!!)\[([^\]]*)\]\(([^)]+)\)', rewrite_link, content)
    return content


CODE_SAMPLES_DIR = RAW_DIR / "code_samples"


def resolve_code_includes(content: str) -> str:
    """Resolve :::code directives by inlining the actual source file content."""
    def replace_code_directive(match):
        lang = match.group(1) or ""
        source = match.group(2)
        # source starts with ~/ — map to code_samples directory
        rel_path = source.lstrip("~/")
        code_file = CODE_SAMPLES_DIR / rel_path
        if code_file.exists():
            code = code_file.read_text(encoding="utf-8", errors="replace").strip()
            return f"```{lang}\n{code}\n```"
        else:
            filename = PurePosixPath(rel_path).name
            return f"```{lang}\n// Source: {filename} (not available)\n```"

    content = re.sub(
        r':::code\s+language="(\w+)"\s+source="([^"]+)"(?:\s+[^:]*)?:::',
        replace_code_directive,
        content
    )
    return content


def strip_code_includes(content: str) -> str:
    """Replace [!code-*] references with placeholder code blocks."""
    def replace_code_include(match):
        lang = match.group(1) or ""
        path = match.group(2)
        filename = PurePosixPath(path).name
        return f"```{lang}\n// See: {filename}\n```"

    content = re.sub(
        r'\[!code-(\w+)\[.*?\]\(([^)]+)\)\]',
        replace_code_include,
        content
    )
    return content


def clean_up(content: str) -> str:
    """Final cleanup pass."""
    # Remove leftover moniker range from front matter comments
    content = re.sub(r'monikerRange:.*\n', '', content)
    # Remove :::no-loc directives
    content = re.sub(r':::no-loc\s+text="([^"]+)":::', r'\1', content)
    # Remove any leftover :::row/:::column directives not caught by convert_columns
    content = re.sub(r':::row:::\s*\n?', '', content)
    content = re.sub(r':::row-end:::\s*\n?', '', content)
    content = re.sub(r':::column[^:]*:::\s*\n?', '', content)
    content = re.sub(r':::column-end:::\s*\n?', '', content)
    # Remove customer intent comments
    content = re.sub(r'#\s*customer intent:.*\n', '', content, flags=re.IGNORECASE)
    # Collapse 3+ blank lines to 2
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip() + "\n"


def build_mdx_front_matter(meta: dict) -> str:
    """Build simplified MDX front matter."""
    if not meta:
        return ""
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, str):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---\n")
    return "\n".join(lines)


def convert_yml_faq(source_path: str) -> str:
    """Convert a YML FAQ doc to MDX."""
    full_path = RAW_DIR / source_path
    if not full_path.exists():
        return ""

    data = yaml.safe_load(full_path.read_text(encoding="utf-8", errors="replace"))
    if not data:
        return ""

    meta = data.get("metadata", {})
    title = data.get("title", meta.get("title", "FAQ"))
    summary = data.get("summary", meta.get("description", ""))

    lines = [
        f"---",
        f'title: "{title}"',
        f'description: "{summary.strip()}"' if summary else "",
        f"---\n",
        f"# {title}\n",
    ]
    if summary:
        lines.append(summary.strip() + "\n")

    for section in data.get("sections", []):
        section_name = section.get("name", "")
        if section_name:
            lines.append(f"## {section_name}\n")
        for qa in section.get("questions", []):
            q = qa.get("question", "").strip()
            a = qa.get("answer", "").strip()
            if q:
                lines.append(f"### {q}\n")
            if a:
                lines.append(f"{a}\n")

    return "\n".join(lines)


def convert_doc(doc: dict) -> str | None:
    """Convert a single document to MDX format."""
    source_path = doc["source_path"]
    category = doc["category"]

    if category == "in-repo-yml":
        return convert_yml_faq(source_path)

    if category != "in-repo-md":
        return None

    full_path = RAW_DIR / source_path
    if not full_path.exists():
        print(f"  SKIP (not downloaded): {source_path}", file=sys.stderr)
        return None

    content = full_path.read_text(encoding="utf-8", errors="replace")

    # Step 1: Resolve includes first (before moniker filtering)
    content = resolve_includes(content, source_path)

    # Step 2: Filter monikers
    content = filter_monikers(content)

    # Step 3: Simplify front matter
    body, meta = simplify_front_matter(content)

    # Step 4: Convert callouts
    body = convert_callouts(body)
    body = convert_nextstep(body)
    body = convert_checklists(body)
    body = convert_selectors(body)

    # Step 5: Convert tabs
    body = convert_tabs(body)

    # Step 6: Convert images
    body = convert_images(body)

    # Step 7: Convert zone pivots
    body = convert_zone_pivots(body)

    # Step 8: Convert columns (after zone pivots strip markers)
    body = convert_columns(body)

    # Step 9: Rewrite links
    body = rewrite_links(body, source_path)

    # Step 10: Resolve :::code includes (inline actual source files)
    body = resolve_code_includes(body)

    # Step 11: Strip remaining [!code-*] includes
    body = strip_code_includes(body)

    # Step 11: Strip table CSS wrappers
    body = strip_table_wrappers(body)

    # Step 12: Final cleanup
    body = clean_up(body)

    # Build final MDX
    front_matter = build_mdx_front_matter(meta)
    return front_matter + body


def main():
    print("Converting docs to Mintlify MDX...", file=sys.stderr)

    # Also collect images for copying
    images_copied = 0

    success = 0
    failed = 0

    for doc in MANIFEST["docs"]:
        if doc["category"] not in ("in-repo-md", "in-repo-yml"):
            continue

        output_path = doc.get("output_path", "")
        if not output_path:
            continue

        result = convert_doc(doc)
        if result is None:
            failed += 1
            continue

        # Write MDX file
        out_file = DOCS_DIR / f"{output_path}.mdx"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(result, encoding="utf-8")
        success += 1

    # Copy images to docs/images/
    images_dir = DOCS_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    for img_path in MANIFEST.get("images", []):
        if img_path.startswith("/") or img_path.startswith("http"):
            continue
        src = RAW_DIR / img_path
        if src.exists():
            dest = images_dir / src.name
            if not dest.exists():
                import shutil
                shutil.copy2(src, dest)
                images_copied += 1

    print(f"\nConversion complete: {success} docs converted, {failed} failed", file=sys.stderr)
    print(f"Images copied: {images_copied}", file=sys.stderr)


if __name__ == "__main__":
    main()
