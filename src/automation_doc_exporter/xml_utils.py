from __future__ import annotations

from xml.etree import ElementTree as ET


def strip_namespace(root: ET.Element) -> None:
    for element in root.iter():
        if "}" in element.tag:
            element.tag = element.tag.rsplit("}", 1)[1]


def child_text(element: ET.Element, tag: str, default: str = "") -> str:
    child = element.find(tag)
    if child is None or child.text is None:
        return default
    return normalize_text(child.text)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def value_text(value_node: ET.Element | None) -> str:
    if value_node is None:
        return ""
    for child in list(value_node):
        if child.text is not None:
            text = normalize_text(child.text)
            if text:
                return text
    if value_node.text:
        return normalize_text(value_node.text)
    return ""


def process_metadata(element: ET.Element) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for node in element.findall("processMetadataValues"):
        name = child_text(node, "name")
        value = value_text(node.find("value"))
        if name or value:
            values.append((name, value))
    return tuple(sorted(values))


def named_value_parameters(element: ET.Element, tag: str = "inputParameters") -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for node in element.findall(tag):
        name = child_text(node, "name")
        value = value_text(node.find("value"))
        if name or value:
            values.append((name, value))
    return tuple(values)


def condition_text(condition: ET.Element) -> str:
    left = child_text(condition, "leftValueReference") or child_text(condition, "field")
    operator = child_text(condition, "operator")
    right = value_text(condition.find("rightValue")) or value_text(condition.find("value"))
    return " ".join(part for part in (left, operator, right) if part)


def target_reference(element: ET.Element, connector_tag: str = "connector") -> str:
    connector = element.find(connector_tag)
    if connector is None:
        return ""
    return child_text(connector, "targetReference")

