from scripts import convert_to_mdx


def test_zone_pivots_emit_one_page_level_selector_for_repeated_group(monkeypatch):
    monkeypatch.setattr(
        convert_to_mdx,
        "_PIVOT_TITLES",
        {
            "azd": "Azure Developer CLI",
            "vscode": "VS Code",
        },
    )
    content = """Before

:::zone pivot="azd"

* [Azure Developer CLI](/azure/developer/azure-developer-cli/install-azd) version 1.24.0 or later

:::zone-end
:::zone pivot="vscode"

* [Visual Studio Code](https://code.visualstudio.com/)
* [Microsoft Foundry Toolkit](https://aka.ms/foundrytk)

:::zone-end

<Note>
Hosted agents are currently in preview.
</Note>

:::zone pivot="azd"

## Step 1
CLI content

:::zone-end
:::zone pivot="vscode"

## Step 1
VS Code content

:::zone-end
"""

    converted = convert_to_mdx.convert_zone_pivots(content)

    assert converted.count("<ZonePivot") == 1
    assert converted.count('<ZoneContent group="azd__vscode" value="azd"') == 2
    assert converted.count('<ZoneContent group="azd__vscode" value="vscode"') == 2
    assert 'options={[{"id": "azd", "title": "Azure Developer CLI"}, {"id": "vscode", "title": "VS Code"}]}' in converted
    assert "* [Azure Developer CLI](/azure/developer/azure-developer-cli/install-azd)" in converted
    assert "* [Visual Studio Code](https://code.visualstudio.com/)" in converted
    assert converted.index("Hosted agents are currently in preview.") < converted.index("## Step 1\nCLI content")
    assert "Hosted agents are currently in preview." in converted
    assert "* For Azure Developer CLI" not in converted


def test_zone_pivots_emit_zone_content(monkeypatch):
    monkeypatch.setattr(
        convert_to_mdx,
        "_PIVOT_TITLES",
        {
            "azd": "Azure Developer CLI",
            "vscode": "VS Code",
        },
    )
    content = """:::zone pivot="azd"

## Step 1
CLI content

:::zone-end
:::zone pivot="vscode"

## Step 1
VS Code content

:::zone-end
"""

    converted = convert_to_mdx.convert_zone_pivots(content)

    assert converted.count("<ZonePivot") == 1
    assert '<ZoneContent group="azd__vscode" value="azd"' in converted
    assert '<ZoneContent group="azd__vscode" value="vscode"' in converted
    assert "## Step 1\nCLI content" in converted
    assert "## Step 1\nVS Code content" in converted
    assert "* For Azure Developer CLI" not in converted


def test_zone_pivot_import_added_only_when_needed():
    body = '<ZonePivot group="azd__vscode" options={[]} defaultValue="azd" />\n'

    converted = convert_to_mdx.add_zone_pivot_import(body)

    assert converted.startswith('import { ZoneContent, ZonePivot } from "/snippets/zone-pivot.jsx"\n\n')
    assert convert_to_mdx.add_zone_pivot_import("No pivots here") == "No pivots here"


def test_reordered_matching_pivots_share_one_selector(monkeypatch):
    monkeypatch.setattr(
        convert_to_mdx,
        "_PIVOT_TITLES",
        {
            "azd": "Azure Developer CLI",
            "vscode": "VS Code",
        },
    )
    content = """:::zone pivot="azd"
CLI first
:::zone-end
:::zone pivot="vscode"
VS Code first
:::zone-end

Shared content

:::zone pivot="vscode"
VS Code second
:::zone-end
:::zone pivot="azd"
CLI second
:::zone-end
"""

    converted = convert_to_mdx.convert_zone_pivots(content)

    assert converted.count("<ZonePivot") == 1
    assert converted.count('<ZoneContent group="azd__vscode" value="azd"') == 2
    assert converted.count('<ZoneContent group="azd__vscode" value="vscode"') == 2


def test_repeated_pivot_id_starts_new_group(monkeypatch):
    monkeypatch.setattr(
        convert_to_mdx,
        "_PIVOT_TITLES",
        {
            "python": "Python",
            "csharp": "C#",
        },
    )
    content = """:::zone pivot="python"
Python first
:::zone-end
:::zone pivot="csharp"
C# first
:::zone-end
:::zone pivot="python"
Python second
:::zone-end
:::zone pivot="csharp"
C# second
:::zone-end
"""

    converted = convert_to_mdx.convert_zone_pivots(content)

    assert converted.count("<ZonePivot") == 1
    assert converted.count('<ZoneContent group="csharp__python" value="python"') == 2
    assert converted.count('<ZoneContent group="csharp__python" value="csharp"') == 2


def test_normalize_markdown_tables_adds_missing_delimiter_cell():
    content = """| Model ID | Standard regions | Global | Developer | Methods | Status | Modality |
| --- | --- | :---: | :---: | :---: | --- |
| `gpt-4o-mini` | North Central US | ✅ | ✅ | SFT | GA | Text to text |
"""

    converted = convert_to_mdx.normalize_markdown_tables(content)

    assert "| --- | --- | :---: | :---: | :---: | --- | --- |" in converted


def test_normalize_markdown_tables_preserves_valid_tables():
    content = """| Name | Value |
| --- | :---: |
| A | B |
"""

    assert convert_to_mdx.normalize_markdown_tables(content) == content
