#!/usr/bin/env python3
"""
Azure OpenAI Model Availability Matrix Generator

Queries the Azure Resource Manager API via `az cognitiveservices model list`
for every relevant region and builds availability tables (HTML + Markdown)
grouped by deployment SKU type — replicating what
https://model-availability.azurewebsites.net/ shows.

Prerequisites:
  - Azure CLI (`az`) installed and logged in
  - A valid Azure subscription
  - `az extension add -n cognitiveservices` (if not already)

Usage:
  python generate.py                  # Generate output/index.html + output/*.md
  python generate.py --format md      # Markdown only
  python generate.py --format html    # HTML only
  python generate.py --regions eastus westus2  # Specific regions only
"""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Regions known to host Azure OpenAI — avoids wasting time on 102 regions.
# Override with --regions if needed.
AOAI_REGIONS = [
    "australiaeast",
    "brazilsouth",
    "canadacentral",
    "canadaeast",
    "centralindia",
    "centralus",
    "eastus",
    "eastus2",
    "francecentral",
    "germanywestcentral",
    "italynorth",
    "japaneast",
    "japanwest",
    "koreacentral",
    "mexicocentral",
    "northcentralus",
    "norwayeast",
    "polandcentral",
    "qatarcentral",
    "southafricanorth",
    "southcentralus",
    "southeastasia",
    "southindia",
    "spaincentral",
    "swedencentral",
    "switzerlandnorth",
    "switzerlandwest",
    "uaenorth",
    "uksouth",
    "westeurope",
    "westus",
    "westus3",
]

SKU_DISPLAY_ORDER = [
    "GlobalStandard",
    "Standard",
    "DataZoneStandard",
    "GlobalBatch",
    "DataZoneBatch",
    "ProvisionedManaged",
    "Provisioned",
    "GlobalProvisionedManaged",
    "DataZoneProvisionedManaged",
    "DeveloperTier",
]

SKU_LABELS = {
    "GlobalStandard": "Global Standard",
    "Standard": "Standard",
    "DataZoneStandard": "Data Zone Standard",
    "GlobalBatch": "Global Batch",
    "DataZoneBatch": "Data Zone Batch",
    "ProvisionedManaged": "Provisioned Managed",
    "Provisioned": "Provisioned",
    "GlobalProvisionedManaged": "Global Provisioned Managed",
    "DataZoneProvisionedManaged": "Data Zone Provisioned",
    "DeveloperTier": "Developer Tier",
}


def fetch_models_for_region(region: str) -> dict:
    """Call `az cognitiveservices model list` for a single region."""
    try:
        result = subprocess.run(
            ["az", "cognitiveservices", "model", "list",
             "--location", region, "-o", "json"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  ⚠ {region}: {result.stderr.strip()[:120]}", file=sys.stderr)
            return {"region": region, "models": []}
        models = json.loads(result.stdout)
        print(f"  ✓ {region}: {len(models)} models")
        return {"region": region, "models": models}
    except subprocess.TimeoutExpired:
        print(f"  ⚠ {region}: timeout", file=sys.stderr)
        return {"region": region, "models": []}
    except Exception as e:
        print(f"  ⚠ {region}: {e}", file=sys.stderr)
        return {"region": region, "models": []}


def build_availability_matrix(all_region_data: list[dict]) -> dict:
    """
    Build a nested dict:
      sku_name -> {
        "models": { (model_name, version): set_of_regions },
        "regions": set_of_all_regions_with_this_sku
      }
    """
    matrix = defaultdict(lambda: {
        "models": defaultdict(set),
        "regions": set()
    })

    for rd in all_region_data:
        region = rd["region"]
        for entry in rd["models"]:
            m = entry.get("model", {})
            name = m.get("name", "")
            version = m.get("version", "")
            lifecycle = m.get("lifecycleStatus", "")
            if lifecycle in ("Deprecated",):
                continue
            for sku in m.get("skus", []):
                sku_name = sku.get("name", "")
                if not sku_name:
                    continue
                matrix[sku_name]["models"][(name, version)].add(region)
                matrix[sku_name]["regions"].add(region)

    return matrix


def sort_model_key(model_tuple):
    """Sort models: by name, then by version descending."""
    name, version = model_tuple
    return (name.lower(), version)


def generate_markdown(matrix: dict) -> dict[str, str]:
    """Generate a markdown table per SKU type. Returns {sku_name: md_string}."""
    outputs = {}

    for sku_name in SKU_DISPLAY_ORDER:
        if sku_name not in matrix:
            continue

        data = matrix[sku_name]
        models = sorted(data["models"].keys(), key=sort_model_key)
        regions = sorted(data["regions"])

        if not models or not regions:
            continue

        label = SKU_LABELS.get(sku_name, sku_name)
        lines = [f"# {label}\n"]

        # Header
        header = "| **Region** |"
        sep = "|:---|"
        for name, ver in models:
            header += f" **{name}** ({ver}) |"
            sep += ":---:|"
        lines.append(header)
        lines.append(sep)

        # Data rows
        for region in regions:
            row = f"| {region} |"
            for model_key in models:
                row += " ✅ |" if region in data["models"][model_key] else " - |"
            lines.append(row)

        lines.append("")
        outputs[sku_name] = "\n".join(lines)

    return outputs


def generate_html(matrix: dict) -> str:
    """Generate a single-page HTML with tabs for each SKU type."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sku_tables = []

    for sku_name in SKU_DISPLAY_ORDER:
        if sku_name not in matrix:
            continue

        data = matrix[sku_name]
        models = sorted(data["models"].keys(), key=sort_model_key)
        regions = sorted(data["regions"])

        if not models or not regions:
            continue

        sku_id = sku_name.lower()

        # Build table HTML
        header_row1 = "<th>Region</th>"
        header_row2 = "<th>Version</th>"
        for name, ver in models:
            header_row1 += f"<th>{name}</th>"
            header_row2 += f"<th>{ver}</th>"

        body_rows = ""
        for region in regions:
            cells = f"<td>{region}</td>"
            for model_key in models:
                if region in data["models"][model_key]:
                    cells += '<td>✅</td>'
                else:
                    cells += '<td>-</td>'
            body_rows += f"<tr>{cells}</tr>\n"

        table = f"""
<div class="sku-table" id="table-{sku_id}" style="display:none;">
  <table>
    <thead>
      <tr>{header_row1}</tr>
      <tr>{header_row2}</tr>
    </thead>
    <tbody>
      {body_rows}
    </tbody>
  </table>
</div>"""
        sku_tables.append(table)

    first_sku = next(
        (s.lower() for s in SKU_DISPLAY_ORDER if s in matrix), ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Azure OpenAI Model Regional Availability (Self-Generated)</title>
<style>
  body {{
    background: #212121; color: #ECECEC; font-family: 'Segoe UI', sans-serif;
    padding: 20px 30px; margin: 0;
  }}
  h1 {{
    color: white; font-size: medium; padding: 10px;
    border: 2px solid white; display: inline-block;
  }}
  .subtitle {{ color: #999; font-size: 12px; margin-top: 8px; }}
  .controls {{ margin: 20px 0 10px; }}
  select {{
    padding: 6px 12px; background: #2b2b2b; color: #ECECEC;
    border: 1px solid #515151; border-radius: 4px; font-size: 13px;
    cursor: pointer;
  }}
  input[type=text] {{
    padding: 6px 12px; background: #2b2b2b; color: #ECECEC;
    border: 1px solid #515151; border-radius: 4px; font-size: 13px;
    margin-left: 10px; width: 250px;
  }}
  table {{
    background: #2b2b2b; border-collapse: separate; border-spacing: 0;
    border-radius: 10px; font-size: 12px; text-align: left;
    margin-top: 10px; width: auto;
  }}
  thead th {{
    text-align: center; padding: 12px 16px; position: sticky; top: 0;
    background: rgba(107, 64, 216, 0.3); z-index: 2;
  }}
  thead tr:nth-child(2) th {{ background: #2b2b2b; }}
  td {{ text-align: center; padding: 6px 12px; }}
  tr td:first-child {{ text-align: left; font-weight: 500; }}
  tbody tr:nth-child(even) {{ background: #333; }}
  tbody tr:nth-child(odd) {{ background: #2b2b2b; }}
  tbody tr:hover {{ background: rgba(104, 222, 122, 0.4) !important; }}
  th, td {{ border: 1px solid #515151; }}
  .hidden {{ display: none !important; }}
</style>
</head>
<body>
  <h1>Azure OpenAI Model Regional Availability</h1>
  <div class="subtitle">
    Auto-generated on {timestamp} via
    <code>az cognitiveservices model list</code>
  </div>

  <div class="controls">
    <select id="skuSelect" onchange="switchSku(this.value)">
      {"".join(f'<option value="{s.lower()}">{SKU_LABELS.get(s, s)}</option>'
               for s in SKU_DISPLAY_ORDER if s in matrix)}
    </select>
    <input type="text" id="search" placeholder="Filter models..."
           oninput="filterModels(this.value)">
  </div>

  <div id="tables">
    {"".join(sku_tables)}
  </div>

  <script>
    function switchSku(sku) {{
      document.querySelectorAll('.sku-table').forEach(
        t => t.style.display = 'none'
      );
      var el = document.getElementById('table-' + sku);
      if (el) el.style.display = '';
      document.getElementById('search').value = '';
      filterModels('');
    }}

    function filterModels(query) {{
      query = query.toLowerCase();
      document.querySelectorAll(
        '.sku-table:not([style*="display: none"]) table'
      ).forEach(function(table) {{
        var headers = table.querySelectorAll('thead tr:first-child th');
        var versionHeaders = table.querySelectorAll(
          'thead tr:nth-child(2) th'
        );
        var visibleCols = [0];
        for (var i = 1; i < headers.length; i++) {{
          var name = headers[i].textContent.toLowerCase();
          var ver = (versionHeaders[i] || {{}}).textContent || '';
          if (!query || name.indexOf(query) !== -1
              || ver.toLowerCase().indexOf(query) !== -1) {{
            visibleCols.push(i);
          }}
        }}
        table.querySelectorAll('tr').forEach(function(row) {{
          var cells = row.querySelectorAll('th, td');
          for (var c = 0; c < cells.length; c++) {{
            cells[c].style.display =
              visibleCols.indexOf(c) !== -1 ? '' : 'none';
          }}
        }});
      }});
    }}

    switchSku('{first_sku}');
  </script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generate Azure OpenAI model availability matrix"
    )
    parser.add_argument(
        "--regions", nargs="*", default=None,
        help="Specific regions to query (default: all known AOAI regions)"
    )
    parser.add_argument(
        "--format", choices=["html", "md", "both"], default="both",
        help="Output format (default: both)"
    )
    parser.add_argument(
        "--output", default="output",
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--workers", type=int, default=8,
        help="Parallel workers for querying regions (default: 8)"
    )
    args = parser.parse_args()

    regions = args.regions or AOAI_REGIONS
    os.makedirs(args.output, exist_ok=True)

    print(f"🔍 Querying {len(regions)} regions with {args.workers} workers...")
    all_data = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_models_for_region, r): r for r in regions}
        for future in as_completed(futures):
            all_data.append(future.result())

    print(f"\n📊 Building availability matrix...")
    matrix = build_availability_matrix(all_data)

    skus_found = [s for s in SKU_DISPLAY_ORDER if s in matrix]
    total_models = sum(len(matrix[s]["models"]) for s in skus_found)
    total_regions = len(set().union(*(matrix[s]["regions"] for s in skus_found)))
    print(f"   Found {total_models} unique model+version combos "
          f"across {total_regions} regions and {len(skus_found)} SKU types")

    if args.format in ("md", "both"):
        md_outputs = generate_markdown(matrix)
        for sku_name, md in md_outputs.items():
            path = os.path.join(args.output, f"{sku_name}.md")
            with open(path, "w") as f:
                f.write(md)
        combined = os.path.join(args.output, "all_models.md")
        with open(combined, "w") as f:
            for sku_name in SKU_DISPLAY_ORDER:
                if sku_name in md_outputs:
                    f.write(md_outputs[sku_name])
                    f.write("\n---\n\n")
        print(f"   ✅ Markdown: {args.output}/*.md")

    if args.format in ("html", "both"):
        html = generate_html(matrix)
        path = os.path.join(args.output, "index.html")
        with open(path, "w") as f:
            f.write(html)
        print(f"   ✅ HTML:     {args.output}/index.html")

    # Dump raw JSON for downstream use
    raw_path = os.path.join(args.output, "raw_data.json")
    with open(raw_path, "w") as f:
        json.dump(all_data, f, indent=2, default=str)
    print(f"   ✅ Raw JSON: {args.output}/raw_data.json")

    print(f"\n✨ Done! Open {args.output}/index.html in a browser.")


if __name__ == "__main__":
    main()
