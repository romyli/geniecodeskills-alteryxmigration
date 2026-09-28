#!/usr/bin/env python3
"""Inventory Alteryx workflow XML without echoing embedded secret values."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


WORKFLOW_SUFFIXES = {".yxmd", ".yxmc", ".yxwz"}
SECRET_TAG_FRAGMENTS = ("password", "secret", "token", "apikey", "api_key")
SIDE_EFFECT_MARKERS = ("email", "download", "runcommand", "render", "sharepointoutput")
SOURCE_MARKERS = ("dbfileinput", "sharepointinput", "lockininput")
OUTPUT_MARKERS = ("dbfileoutput", "macrooutput", "lockinstreamout")
EXPRESSION_TAGS = {
    "Expression",
    "UpdateExpression",
    "ConditionExpression",
    "InitExpression",
    "LoopExpression",
}
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(password|passwd|pwd|token|api[_-]?key|secret)\s*([=:])\s*([^;,\s&<]+)"
)
URL_CREDENTIAL_PATTERN = re.compile(r"(?i)(https?://)[^/@\s:]+:[^/@\s]+@")


def clean(value: str | None) -> str:
    return " ".join((value or "").split())


def clip(value: str, limit: int = 300) -> str:
    value = sanitize(value)
    return value if len(value) <= limit else value[: limit - 1] + "…"


def sanitize(value: str | None) -> str:
    value = clean(value)
    value = SECRET_VALUE_PATTERN.sub(r"\1\2<redacted>", value)
    return URL_CREDENTIAL_PATTERN.sub(r"\1<redacted>@", value)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_texts(element: ET.Element | None, tag: str) -> list[str]:
    if element is None:
        return []
    values: list[str] = []
    for child in element.iter():
        if local_name(child.tag) == tag and clean(child.text):
            values.append(clean(child.text))
    return values


def first_text(element: ET.Element | None, *tags: str) -> str:
    for tag in tags:
        values = element_texts(element, tag)
        if values:
            return values[0]
    return ""


def iter_workflows(paths: Iterable[str]) -> list[Path]:
    found: set[Path] = set()
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in WORKFLOW_SUFFIXES:
                    found.add(candidate.resolve())
        elif path.is_file() and path.suffix.lower() in WORKFLOW_SUFFIXES:
            found.add(path.resolve())
        else:
            raise FileNotFoundError(f"No Alteryx workflow found at: {path}")
    return sorted(found)


def plugin_name(node: ET.Element) -> tuple[str, str | None]:
    gui = node.find("GuiSettings")
    plugin = gui.get("Plugin", "") if gui is not None else ""
    engine = node.find("EngineSettings")
    macro = engine.get("Macro") if engine is not None else None
    return plugin, macro


def contains_secret_material(configuration: ET.Element | None) -> bool:
    if configuration is None:
        return False
    for element in configuration.iter():
        name = local_name(element.tag).lower()
        if any(fragment in name for fragment in SECRET_TAG_FRAGMENTS):
            if clean(element.text) or any(clean(value) for value in element.attrib.values()):
                return True
    serialized = ET.tostring(configuration, encoding="unicode")
    return bool(SECRET_VALUE_PATTERN.search(serialized) or URL_CREDENTIAL_PATTERN.search(serialized))


def node_record(node: ET.Element) -> dict[str, Any]:
    plugin, macro = plugin_name(node)
    configuration = node.find("./Properties/Configuration")
    lower = plugin.lower()
    tool = plugin.rsplit(".", 1)[-1] if plugin else (f"Macro:{macro}" if macro else "Unknown")

    files = element_texts(configuration, "File")
    query = first_text(configuration, "Query")
    table = first_text(configuration, "Table")
    connection = (
        next(
            (element for element in configuration.iter() if local_name(element.tag) == "Connection"),
            None,
        )
        if configuration is not None
        else None
    )
    connection_title = connection.get("DcmTitle", "") if connection is not None else ""

    source_location = files[0] if files else (query or table)
    if "sharepointinput" in lower:
        source_location = first_text(configuration, "List") or "SharePoint input"

    output_location = files[0] if files else ""
    if "email" in lower:
        output_location = "Email action"
    elif "download" in lower:
        output_location = "HTTP action"

    expressions: list[str] = []
    for element in node.iter():
        expression = element.get("expression")
        if expression:
            expressions.append(expression)
        if local_name(element.tag) in EXPRESSION_TAGS and clean(element.text):
            expressions.append(element.text or "")

    return {
        "tool_id": node.get("ToolID", ""),
        "plugin": plugin,
        "tool": tool,
        "macro": macro,
        "is_source": any(marker in lower for marker in SOURCE_MARKERS),
        "is_output": any(marker in lower for marker in OUTPUT_MARKERS)
        or any(marker in lower for marker in SIDE_EFFECT_MARKERS),
        "is_side_effect": any(marker in lower for marker in SIDE_EFFECT_MARKERS),
        "source_location": clip(source_location),
        "output_location": clip(output_location),
        "connection_title": clip(connection_title, 120),
        "expression_count": len(expressions),
        "max_expression_length": max((len(value) for value in expressions), default=0),
        "contains_secret_material": contains_secret_material(configuration),
        "configuration_text": ET.tostring(configuration, encoding="unicode")
        if configuration is not None
        else "",
    }


def analyze(path: Path) -> dict[str, Any]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML in {path}: {exc}") from exc

    nodes = [node_record(node) for node in root.findall(".//Node")]
    connections = root.findall(".//Connections/Connection")
    tool_counts = Counter(record["tool"] for record in nodes)
    all_configuration = "\n".join(record.pop("configuration_text") for record in nodes)
    all_lower = all_configuration.lower()

    sources = [
        {
            "tool_id": record["tool_id"],
            "tool": record["tool"],
            "location": record["source_location"],
            "connection": record["connection_title"],
        }
        for record in nodes
        if record["is_source"]
    ]
    outputs = [
        {
            "tool_id": record["tool_id"],
            "tool": record["tool"],
            "location": record["output_location"],
            "side_effect": record["is_side_effect"],
        }
        for record in nodes
        if record["is_output"]
    ]
    macros = sorted({record["macro"] for record in nodes if record["macro"]})

    locations = "\n".join(
        [source["location"] for source in sources] + [output["location"] for output in outputs]
    ).lower()
    risks: list[str] = []
    if any(record["contains_secret_material"] for record in nodes):
        risks.append("Embedded credential or secret material is present; values were not emitted.")
    if "\\\\" in all_configuration or re.search(r"^[a-z]:\\", all_configuration, re.M | re.I):
        risks.append("SMB/UNC or local Windows paths require a landing step before Designer.")
    if ".yxdb" in locations:
        risks.append("YXDB is proprietary and requires an export/conversion step.")
    if ".hyper" in locations:
        risks.append("Hyper input/output should normally be replaced by a Unity Catalog table.")
    if "sharepointversion" in all_lower and re.search(
        r"<SharePointVersion>\s*2007\s*</SharePointVersion>", all_configuration, re.I
    ):
        risks.append(
            "Legacy SharePoint 2007 configuration is present; managed OAuth ingestion is not a drop-in replacement."
        )
    if re.search(r"https?://", all_configuration, re.I):
        risks.append(
            "HTTP endpoint configuration is present; review connectivity, secrets, preview safety, and idempotency."
        )
    if any(record["is_side_effect"] for record in nodes):
        risks.append(
            "Operational side effects are present and should be isolated from visual transformations."
        )
    if any(
        "interface" in record["plugin"].lower() or "questions" in record["plugin"].lower()
        for record in nodes
    ):
        risks.append("Interface tools are present; map them to Job parameters or a Databricks App.")

    return {
        "path": str(path),
        "document_type": path.suffix.lower().lstrip("."),
        "alteryx_version": root.get("yxmdVer", ""),
        "node_count": len(nodes),
        "connection_count": len(connections),
        "expression_count": sum(record["expression_count"] for record in nodes),
        "max_expression_length": max(
            (record["max_expression_length"] for record in nodes), default=0
        ),
        "tool_counts": dict(tool_counts.most_common()),
        "sources": sources,
        "outputs": outputs,
        "macros": macros,
        "risk_flags": risks,
    }


def escape_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def markdown_report(results: list[dict[str, Any]]) -> str:
    lines = ["# Alteryx workflow inventory", ""]
    for result in results:
        lines.extend(
            [
                f"## {Path(result['path']).name}",
                "",
                f"- Path: `{result['path']}`",
                f"- Type/version: `{result['document_type']}` / `{result['alteryx_version'] or 'unknown'}`",
                f"- Nodes/connections: {result['node_count']} / {result['connection_count']}",
                f"- Expressions: {result['expression_count']} (maximum length {result['max_expression_length']})",
                "",
                "### Tool counts",
                "",
                "| Tool | Count |",
                "|---|---:|",
            ]
        )
        lines.extend(
            f"| {escape_cell(tool)} | {count} |"
            for tool, count in result["tool_counts"].items()
        )

        lines.extend(
            [
                "",
                "### Sources",
                "",
                "| ID | Tool | Location/query | Connection |",
                "|---|---|---|---|",
            ]
        )
        if result["sources"]:
            lines.extend(
                f"| {escape_cell(item['tool_id'])} | {escape_cell(item['tool'])} | {escape_cell(item['location'])} | {escape_cell(item['connection'])} |"
                for item in result["sources"]
            )
        else:
            lines.append("|  |  | None detected |  |")

        lines.extend(
            [
                "",
                "### Outputs and side effects",
                "",
                "| ID | Tool | Destination/action | Side effect |",
                "|---|---|---|---|",
            ]
        )
        if result["outputs"]:
            lines.extend(
                f"| {escape_cell(item['tool_id'])} | {escape_cell(item['tool'])} | {escape_cell(item['location'])} | {'yes' if item['side_effect'] else 'no'} |"
                for item in result["outputs"]
            )
        else:
            lines.append("|  |  | None detected |  |")

        lines.extend(["", "### Referenced macros", ""])
        if result["macros"]:
            lines.extend(f"- `{macro}`" for macro in result["macros"])
        else:
            lines.append("- None detected")
        lines.extend(["", "### Risk flags", ""])
        if result["risk_flags"]:
            lines.extend(f"- {risk}" for risk in result["risk_flags"])
        else:
            lines.append("- None detected")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Alteryx workflow files or directories")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write the report to this path instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        workflows = iter_workflows(args.paths)
        results = [analyze(path) for path in workflows]
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = (
        json.dumps(results, indent=2) + "\n"
        if args.format == "json"
        else markdown_report(results)
    )
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
