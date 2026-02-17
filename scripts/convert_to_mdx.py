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

    # Match > [!TYPE]\n> content lines (greedy within blockquote)
    # Support optional leading whitespace for callouts inside list items
    pattern = r'^([ \t]*)>\s*\[!(TIP|NOTE|WARNING|IMPORTANT|CAUTION)\]\s*\n((?:\1>.*\n?)*)'

    def replace_callout(match):
        indent = match.group(1)
        callout_type = match.group(2).upper()
        component = callout_map.get(callout_type, "Note")
        # Get the remaining lines of the blockquote
        block_content = match.group(3)
        # Remove leading indent + > from each line
        lines = []
        for line in block_content.split("\n"):
            # Strip the same indent level, then the > marker
            if line.startswith(indent):
                line = line[len(indent):]
            stripped = re.sub(r"^>\s?", "", line)
            lines.append(stripped)
        inner = "\n".join(lines).strip()
        return f"{indent}<{component}>\n{indent}{inner}\n{indent}</{component}>\n"

    content = re.sub(pattern, replace_callout, content, flags=re.IGNORECASE | re.MULTILINE)
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
        return f'<Columns cols={{{n}}}>\n' + "\n".join(cards) + "\n</Columns>\n"

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


def rewrite_image_paths(content: str) -> str:
    """Rewrite markdown and HTML image paths to /images/filename.

    Converts relative paths (../media/..., media/..., ./media/...) and
    backslash paths to the flat /images/ directory used by the docs site.
    Maps ~/reusable-content/.../ai-services/X.svg to /images/ai-services/X.svg.
    """
    def _rewrite_md_img(m):
        alt = m.group(1)
        path = m.group(2)
        if path.startswith('http'):
            return m.group(0)
        if path.startswith('~/reusable-content/'):
            # Map to /images/ai-services/filename.svg
            name = PurePosixPath(path).name
            return f'![{alt}](/images/ai-services/{name})'
        # Normalize backslashes and extract filename
        path = path.replace('\\', '/')
        name = PurePosixPath(path).name
        return f'![{alt}](/images/{name})'

    # Rewrite markdown images ![alt](path)
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', _rewrite_md_img, content)

    def _rewrite_html_img(m):
        prefix = m.group(1)
        path = m.group(2)
        suffix = m.group(3)
        if path.startswith('http'):
            return m.group(0)
        path = path.replace('\\', '/')
        name = PurePosixPath(path).name
        return f'{prefix}/images/{name}{suffix}'

    # Rewrite <img src="path"> with backslashes or relative paths
    content = re.sub(
        r'(<img\s[^>]*src=")([^"]+)(")',
        _rewrite_html_img,
        content,
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
        tab_match = re.match(r'^#{1,6}\s+\[([^\]]+)\]\(#tab/([^)]+)\)\s*$', line)

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
    """Convert :::zone pivot="..." blocks to Mintlify <Tabs>/<Tab> components."""
    lines = content.split("\n")
    result = []
    i = 0
    zones = []  # stack of (pivot_name, start_index)
    zone_groups = []  # list of (pivot_name, content_lines) for consecutive zones

    def flush_zone_group():
        """Convert accumulated consecutive zones into a <Tabs> block."""
        if not zone_groups:
            return
        if len(zone_groups) == 1:
            # Single zone: just output content without tabs wrapper
            result.extend(zone_groups[0][1])
        else:
            result.append("<Tabs>")
            for pivot_name, zone_lines in zone_groups:
                title = pivot_name.replace("-", " ").title()
                result.append(f'  <Tab title="{title}">')
                for line in zone_lines:
                    result.append(f"  {line}" if line.strip() else "")
                result.append("  </Tab>")
            result.append("</Tabs>")
        zone_groups.clear()

    while i < len(lines):
        line = lines[i]

        # Match zone start: :::zone pivot="python" or ::: zone pivot="python"
        zone_start = re.match(r':::\s*zone\s+pivot="([^"]+)"\s*$', line)
        if zone_start:
            pivot_name = zone_start.group(1)
            zones.append((pivot_name, []))
            i += 1
            continue

        # Match zone end: :::zone-end or ::: zone-end
        if re.match(r':::\s*zone-end\s*$', line):
            if zones:
                pivot_name, zone_content = zones.pop()
                zone_groups.append((pivot_name, zone_content))
            i += 1
            # Peek ahead: if next non-blank line is NOT another zone start, flush
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines) or not re.match(r':::\s*zone\s+pivot="', lines[j]):
                flush_zone_group()
            continue

        if zones:
            zones[-1][1].append(line)
        else:
            # If we have pending zone groups and hit non-zone content, flush first
            if zone_groups:
                flush_zone_group()
            result.append(line)

        i += 1

    # Flush any remaining
    flush_zone_group()

    return "\n".join(result)


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
        indent = match.group(1)
        lang = match.group(2) or ""
        source = match.group(3)
        # source starts with ~/ — map to code_samples directory
        rel_path = source.lstrip("~/")
        code_file = CODE_SAMPLES_DIR / rel_path
        if code_file.exists():
            code = code_file.read_text(encoding="utf-8", errors="replace").strip()
        else:
            filename = PurePosixPath(rel_path).name
            code = f"// Source: {filename} (not available)"
        # Indent code content and closing fence to match the directive's indentation
        # so the code block stays valid inside list items / nested contexts.
        indented_code = '\n'.join(indent + line if line else line for line in code.split('\n'))
        return f"{indent}```{lang}\n{indented_code}\n{indent}```"

    content = re.sub(
        r'^([ \t]*):::code\s+language="(\w+)"\s+source="([^"]+)"(?:\s+[^:]*)?:::',
        replace_code_directive,
        content,
        flags=re.MULTILINE,
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


def replace_html_comments(content: str) -> str:
    """Replace HTML comments <!-- ... --> with MDX-compatible {/* ... */}.

    Skips content inside code fences to avoid mangling code examples.
    For multi-line comments, ensures all inner lines are indented to at
    least the same level as the opening {/* so they don't break list contexts.
    """
    parts = _split_code_and_comments(content)
    for i, part in enumerate(parts):
        if not (part.lstrip().startswith('```') or part.lstrip().startswith('~~~') or part.lstrip().startswith('{/*')):

            def _convert_comment(m, _part=part):
                inner = m.group(1)
                if '\n' not in inner:
                    return '{/*' + inner + '*/}'
                # Detect indent of the <!-- from the part text
                start = m.start()
                line_start = _part.rfind('\n', 0, start) + 1
                indent = ' ' * (start - line_start)
                lines = inner.split('\n')
                result_lines = [lines[0]]  # first line follows {/*
                for line in lines[1:]:
                    if line.strip() == '':
                        result_lines.append('')
                    elif len(line) - len(line.lstrip()) < len(indent):
                        result_lines.append(indent + line.lstrip())
                    else:
                        result_lines.append(line)
                # Ensure closing */} is indented to match opening {/*
                # Remove trailing empty lines, then add indented closing
                while result_lines and result_lines[-1].strip() == '':
                    result_lines.pop()
                return '{/*' + '\n'.join(result_lines) + '\n' + indent + '*/}'

            parts[i] = re.sub(
                r'<!--(.*?)-->',
                _convert_comment,
                part,
                flags=re.DOTALL,
            )
    return ''.join(parts)


def fix_void_elements(content: str) -> str:
    """Replace unclosed HTML void elements with self-closing form for MDX/JSX.

    Handles <br>, </br>, <hr> (case-insensitive) → <br />, <hr />.
    Skips content inside fenced code blocks.
    """
    parts = _split_code_and_comments(content)
    for i, part in enumerate(parts):
        if not (part.lstrip().startswith('```') or part.lstrip().startswith('~~~') or part.lstrip().startswith('{/*')):
            # <br> or <br/> (without space) → <br /> ; also <BR>, <Br>, etc.
            part = re.sub(r'<br\s*/?>', '<br />', part, flags=re.IGNORECASE)
            # </br> → <br />
            part = re.sub(r'</br\s*>', '<br />', part, flags=re.IGNORECASE)
            # <hr> or <hr/> → <hr />
            part = re.sub(r'<hr\s*/?>', '<hr />', part, flags=re.IGNORECASE)
            # </hr> → <hr />
            part = re.sub(r'</hr\s*>', '<hr />', part, flags=re.IGNORECASE)
            # <sup/> → </sup> (malformed closing tag)
            part = re.sub(r'<sup\s*/>', '</sup>', part, flags=re.IGNORECASE)
            parts[i] = part
    return ''.join(parts)


def fix_html_in_tables(content: str) -> str:
    """Fix HTML elements inside markdown table cells that break MDX parsing.

    1. Convert <ul><li>...</li></ul> in table rows to dash-separated items with <br />.
    2. Remove <Frame>...</Frame> wrappers in table rows, keeping inner content.
    """
    parts = _split_code_and_comments(content)
    for i, part in enumerate(parts):
        if part.lstrip().startswith('```') or part.lstrip().startswith('~~~') or part.lstrip().startswith('{/*'):
            continue
        lines = part.split('\n')
        for j, line in enumerate(lines):
            # Only process markdown table rows
            if not re.match(r'\s*\|', line):
                continue
            # Fix <ul><li>...</li></ul> → dash-separated items with <br />
            def replace_ul(m):
                items = re.findall(r'<li>(.*?)</li>', m.group(0), re.DOTALL)
                return ' '.join(f'- {item.strip()}' if idx == 0
                               else f'<br /> - {item.strip()}'
                               for idx, item in enumerate(items))
            line = re.sub(r'<ul>\s*(?:<li>.*?</li>\s*)+</ul>', replace_ul, line, flags=re.IGNORECASE)
            # Also strip orphan list tags that weren't part of a complete <ul>...</ul>
            line = re.sub(r'</?ul>', '', line, flags=re.IGNORECASE)
            line = re.sub(r'<li>', '- ', line, flags=re.IGNORECASE)
            line = re.sub(r'</li>', '', line, flags=re.IGNORECASE)
            # Fix <ol> and list items similarly
            line = re.sub(r'</?ol>', '', line, flags=re.IGNORECASE)
            # Fix <Frame>...</Frame> → keep inner content only (in table rows)
            line = re.sub(r'<Frame[^>]*>\s*', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\s*</Frame>', '', line, flags=re.IGNORECASE)
            lines[j] = line
        # Also strip <Frame>/</Frame> on ANY line between table rows
        # (multi-line table cells have continuation lines without |)
        in_table = False
        for j, line in enumerate(lines):
            if re.match(r'\s*\|', line):
                in_table = True
            elif in_table and line.strip() == '':
                in_table = False
            if in_table:
                lines[j] = re.sub(r'<Frame[^>]*>', '', lines[j], flags=re.IGNORECASE)
                lines[j] = re.sub(r'</Frame>', '', lines[j], flags=re.IGNORECASE)
        parts[i] = '\n'.join(lines)
    return ''.join(parts)


def strip_orphan_tags(content: str) -> str:
    """Remove orphan closing tags (</a>, </span>) that appear outside their opening context."""
    parts = _split_code_and_comments(content)
    for i, part in enumerate(parts):
        if part.lstrip().startswith('```') or part.lstrip().startswith('~~~') or part.lstrip().startswith('{/*'):
            continue
        # Remove </a> not preceded by <a on the same line
        lines = part.split('\n')
        for j, line in enumerate(lines):
            if '</a>' in line and '<a ' not in line and '<a>' not in line:
                lines[j] = line.replace('</a>', '')
            if '</span>' in line and '<span' not in line:
                lines[j] = lines[j].replace('</span>', '')
        parts[i] = '\n'.join(lines)
    return ''.join(parts)


def tabs_to_codegroup(content: str) -> str:
    """Convert code-only <Tabs>/<Tab> blocks to <CodeGroup>.

    Mintlify uses <CodeGroup> for multi-language code examples and <Tabs> for
    mixed content. When every <Tab> contains only a code fence (and maybe
    whitespace), replace the whole block with a <CodeGroup>.
    """
    def replace_tabs_block(match):
        block = match.group(1)
        tabs = re.findall(r'<Tab\s+title="([^"]+)">(.*?)</Tab>', block, re.DOTALL)
        if not tabs:
            return match.group(0)

        code_blocks = []
        for title, body in tabs:
            stripped = body.strip()
            # Extract all code fences
            fences = re.findall(r'(```\w*[^\n]*\n.*?```)', stripped, re.DOTALL)
            # Check if body is ONLY code fences (allow whitespace between)
            no_code = re.sub(r'```[\w]*[^\n]*\n.*?```', '', stripped, flags=re.DOTALL).strip()
            if no_code and len(no_code) > 20:
                return match.group(0)  # mixed content, keep as Tabs
            if not fences:
                return match.group(0)  # no code at all, keep as Tabs

            for fence in fences:
                # Inject title into fence if not already titled
                first_line = fence.split('\n', 1)[0]
                # e.g. ```python  or ```python title.py
                lang_match = re.match(r'^```(\w+)(.*)', first_line)
                if lang_match:
                    lang = lang_match.group(1)
                    rest = lang_match.group(2).strip()
                    if not rest:
                        # Add title from tab
                        new_first = f'```{lang} {title}'
                        fence = new_first + '\n' + fence.split('\n', 1)[1]
                    code_blocks.append(fence)
                else:
                    code_blocks.append(fence)

        return '<CodeGroup>\n' + '\n\n'.join(code_blocks) + '\n</CodeGroup>'

    return re.sub(r'<Tabs>\s*(.*?)\s*</Tabs>', replace_tabs_block, content, flags=re.DOTALL)


def fix_components_in_list_items(content: str) -> str:
    """Break Mintlify components out of markdown list items.

    When component tags like <Frame>, <Note>, etc. appear indented inside
    list items, MDX fails with 'Expected a closing tag before end of
    listItem'. Fix by de-indenting component blocks to top level.
    """
    components = ('Frame', 'Note', 'Info', 'Tip', 'Warning', 'Check', 'Danger')
    comp_names = '|'.join(components)
    open_re = re.compile(rf'^(\s+)<({comp_names})(\s|>|/>)')
    inline_re = re.compile(rf'^(\s+)<({comp_names})\b[^>]*>.*</\2>')
    list_start_re = re.compile(r'^\s*(\d+\.\s|[-*]\s)')

    lines = content.split('\n')
    result = []
    in_list = False

    i = 0
    while i < len(lines):
        line = lines[i]

        if list_start_re.match(line):
            in_list = True
            result.append(line)
            i += 1
            continue

        # Non-blank, non-indented line ends list context
        if line.strip() and not line[0:1] in (' ', '\t'):
            in_list = False

        if in_list:
            # Single-line component (e.g. <Check>text</Check>)
            im = inline_re.match(line)
            if im:
                indent = im.group(1)
                if result and result[-1].strip():
                    result.append('')
                result.append(line[len(indent):])
                i += 1
                if i < len(lines) and lines[i].strip():
                    result.append('')
                continue

            # Multi-line component block
            om = open_re.match(line)
            if om:
                indent = om.group(1)
                tag_name = om.group(2)
                close_tag = f'</{tag_name}>'

                if result and result[-1].strip():
                    result.append('')

                # De-indent all lines until the closing tag
                while i < len(lines):
                    l = lines[i]
                    if l.startswith(indent):
                        result.append(l[len(indent):])
                    elif l.strip():
                        result.append(l.lstrip())
                    else:
                        result.append('')
                    i += 1
                    if close_tag in l:
                        break

                if i < len(lines) and lines[i].strip():
                    result.append('')
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


_KNOWN_HTML_TAGS = frozenset({
    'a', 'abbr', 'address', 'area', 'article', 'aside', 'audio',
    'b', 'base', 'bdi', 'bdo', 'blockquote', 'body', 'br', 'button',
    'canvas', 'caption', 'cite', 'code', 'col', 'colgroup',
    'data', 'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 'div', 'dl', 'dt',
    'em', 'embed', 'fieldset', 'figcaption', 'figure', 'footer', 'form',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header', 'hgroup', 'hr', 'html',
    'i', 'iframe', 'img', 'input', 'ins', 'kbd',
    'label', 'legend', 'li', 'link', 'main', 'map', 'mark', 'math', 'menu', 'meta',
    'meter', 'nav', 'noscript', 'object', 'ol', 'optgroup', 'option', 'output',
    'p', 'param', 'picture', 'pre', 'progress', 'q', 'rp', 'rt', 'ruby',
    's', 'samp', 'script', 'section', 'select', 'slot', 'small', 'source', 'span',
    'strong', 'style', 'sub', 'summary', 'sup', 'svg',
    'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th', 'thead',
    'time', 'title', 'tr', 'track', 'u', 'ul', 'var', 'video', 'wbr',
})


_FENCE_OPEN_RE = re.compile(r'^([ \t]*)(`{3,}|~{3,})([^`~]*)$', re.MULTILINE)


def _split_code_and_comments(content: str) -> list[str]:
    """Split *content* into alternating [prose, protected, prose, …] parts.

    Protected parts are fenced code blocks (``` or ~~~, possibly indented up
    to 9 spaces for list-item nesting) and JSX comments ({/* … */}).
    Code fences are detected line-by-line so that inline triple-backtick
    spans (e.g. ```value```) are never mistaken for fences.
    """
    parts: list[str] = []
    pos = 0

    # Collect all fence and JSX-comment regions as (start, end) spans
    regions: list[tuple[int, int]] = []

    # Find fenced code blocks
    for m in _FENCE_OPEN_RE.finditer(content):
        # Skip if this match starts inside an already-found region
        if regions and m.start() < regions[-1][1]:
            continue
        fence_char = m.group(2)[0]
        fence_len = len(m.group(2))
        # Only treat as an opening fence if the line has a language/info string
        # OR if it's at a position not covered by a prior region's close
        # Build closing-fence pattern: same char, at least as many, on its own line
        close_pat = re.compile(
            r'^[ \t]*' + re.escape(fence_char) + r'{' + str(fence_len) + r',}[ \t]*$',
            re.MULTILINE,
        )
        search_start = m.end()
        # Skip past the newline after the opening fence line
        if search_start < len(content) and content[search_start] == '\n':
            search_start += 1
        close_m = close_pat.search(content, search_start)
        if close_m:
            regions.append((m.start(), close_m.end()))

    # Find JSX comment blocks {/* ... */}
    for m in re.finditer(r'\{/\*[\s\S]*?\*/\}', content):
        regions.append((m.start(), m.end()))

    # Sort by start and remove overlapping regions (keep earliest)
    regions.sort()
    merged: list[tuple[int, int]] = []
    for start, end in regions:
        if merged and start < merged[-1][1]:
            continue  # overlaps with previous region, skip
        merged.append((start, end))

    # Build parts list by slicing around protected regions
    for start, end in merged:
        parts.append(content[pos:start])   # prose before region
        parts.append(content[start:end])   # protected region
        pos = end
    parts.append(content[pos:])            # trailing prose

    return parts


def _is_valid_tag_at(text: str, pos: int) -> bool:
    """Check if '<' at pos in text starts a valid HTML/JSX tag."""
    after = text[pos + 1:]
    if not after:
        return False
    # Closing tag </tagname>
    if after[0] == '/':
        m = re.match(r'/([a-zA-Z][a-zA-Z0-9]*)\s*>', after)
        if m:
            tag = m.group(1)
            return tag[0].isupper() or tag.lower() in _KNOWN_HTML_TAGS
        return False
    # HTML comment <!--
    if after.startswith('!--'):
        return True
    # Opening/self-closing tag
    m = re.match(r'([a-zA-Z][a-zA-Z0-9]*)', after)
    if m:
        tag = m.group(1)
        rest = after[len(tag):]
        if not rest:
            return False
        first = rest[0]
        if first in (' ', '\t', '\n', '>'):
            return tag[0].isupper() or tag.lower() in _KNOWN_HTML_TAGS
        if first == '/':
            # Self-closing: must be /> (possibly with whitespace)
            if re.match(r'/\s*>', rest):
                return tag[0].isupper() or tag.lower() in _KNOWN_HTML_TAGS
            return False
    return False


def escape_angle_brackets(content: str) -> str:
    """Escape '<' in prose that MDX would misinterpret as JSX tags.

    Converts autolinks <URL> to markdown links and escapes remaining
    bare '<' that aren't valid HTML/JSX tag starts.
    Skips content inside code fences and inline code spans.
    """
    parts = _split_code_and_comments(content)
    for i, part in enumerate(parts):
        if part.lstrip().startswith('```') or part.lstrip().startswith('~~~') or part.lstrip().startswith('{/*'):
            continue
        lines = part.split('\n')
        for j, line in enumerate(lines):
            segments = re.split(r'(`[^`]+`)', line)
            for k, seg in enumerate(segments):
                if seg.startswith('`'):
                    continue
                # Convert autolinks <URL> to markdown links
                seg = re.sub(r'(?<!\\)<(https?://[^>]+)>', r'[\1](\1)', seg)
                # Escape bare < that aren't valid HTML/JSX tags
                result = []
                pos = 0
                for m in re.finditer(r'(?<!\\)<', seg):
                    result.append(seg[pos:m.start()])
                    if _is_valid_tag_at(seg, m.start()):
                        result.append('<')
                    else:
                        result.append('&lt;')
                    pos = m.start() + 1
                result.append(seg[pos:])
                segments[k] = ''.join(result)
            lines[j] = ''.join(segments)
        parts[i] = '\n'.join(lines)
    return ''.join(parts)


def escape_jsx_braces(content: str) -> str:
    """Escape { and } in prose text to prevent MDX JSX expression errors.

    Skips content inside code fences, inline code spans, JSX component
    lines (e.g. <Columns cols={3}>), and JSX comments ({/* ... */}).
    """
    parts = _split_code_and_comments(content)
    for i, part in enumerate(parts):
        if part.lstrip().startswith('```') or part.lstrip().startswith('~~~') or part.lstrip().startswith('{/*'):
            continue
        lines = part.split('\n')
        for j, line in enumerate(lines):
            # Skip lines that are JSX/MDX component tags
            if re.match(r'\s*</?[A-Z]', line):
                continue
            # Split by inline code spans and JSX comments — skip those
            segments = re.split(r'(`[^`]+`|\{/\*.*?\*/\})', line)
            for k, seg in enumerate(segments):
                if seg.startswith('`') or seg.startswith('{/*'):
                    continue
                seg = re.sub(r'(?<!\\)\{', r'\\{', seg)
                seg = re.sub(r'(?<!\\)\}', r'\\}', seg)
                segments[k] = seg
            lines[j] = ''.join(segments)
        parts[i] = '\n'.join(lines)
    return ''.join(parts)


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

    # Step 6b: Rewrite markdown/HTML image paths to /images/filename
    body = rewrite_image_paths(body)

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

    # Step 12: Replace HTML comments with MDX-compatible JSX comments
    body = replace_html_comments(body)

    # Step 12b: Ensure JSX comments are separated from preceding list items
    body = re.sub(
        r'(^[ \t]*(?:[-*+]|\d+\.)\s+.+\n)([ \t]*\{/\*)',
        r'\1\n\2',
        body,
        flags=re.MULTILINE,
    )

    # Step 13: Fix void HTML elements (<br>, <hr>) for MDX/JSX
    body = fix_void_elements(body)

    # Step 14: Fix HTML elements inside table cells (<ul><li>, <Frame>)
    body = fix_html_in_tables(body)

    # Step 15: Strip orphan closing tags (</a>, </span>)
    body = strip_orphan_tags(body)

    # Step 16: Escape angle brackets that MDX misinterprets as JSX tags
    body = escape_angle_brackets(body)

    # Step 17: Escape curly braces in prose to prevent JSX expression errors
    body = escape_jsx_braces(body)

    # Step 18: Fix components inside list items (de-indent to break out of list)
    body = fix_components_in_list_items(body)

    # Step 19: Convert code-only <Tabs> to <CodeGroup>
    body = tabs_to_codegroup(body)

    # Step 20: Final cleanup
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
