from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .classification import ClassificationResult, classify_automation, load_classification_config
from .models import AutomationDocument, DetailItem
from .xml_utils import (
    child_text,
    condition_text,
    named_value_parameters,
    process_metadata,
    strip_namespace,
    target_reference,
    value_text,
)


FLOW_SUFFIX = ".flow-meta.xml"
FLOW_DEFINITION_SUFFIX = ".flowDefinition-meta.xml"
WORKFLOW_SUFFIX = ".workflow-meta.xml"


def collect_automation_documents(project_root: Path) -> list[AutomationDocument]:
    flow_definitions = _collect_flow_definitions(project_root)
    classification_config = load_classification_config(project_root)
    documents: list[AutomationDocument] = []

    for path in sorted(project_root.rglob(f"*{FLOW_SUFFIX}"), key=lambda item: item.as_posix()):
        documents.append(
            _parse_flow(path, project_root, flow_definitions.get(_api_name(path, FLOW_SUFFIX), {}), classification_config)
        )

    for path in sorted(project_root.rglob(f"*{WORKFLOW_SUFFIX}"), key=lambda item: item.as_posix()):
        documents.append(_parse_workflow(path, project_root))

    return sorted(documents, key=lambda item: (item.kind, item.source_path, item.api_name))


def _collect_flow_definitions(project_root: Path) -> dict[str, dict[str, str]]:
    definitions: dict[str, dict[str, str]] = {}
    for path in sorted(project_root.rglob(f"*{FLOW_DEFINITION_SUFFIX}"), key=lambda item: item.as_posix()):
        root = _parse_xml(path)
        api_name = _api_name(path, FLOW_DEFINITION_SUFFIX)
        values = {
            "flowDefinitionPath": _relative_path(path, project_root),
            "activeVersionNumber": child_text(root, "activeVersionNumber"),
            "description": child_text(root, "description"),
        }
        definitions[api_name] = {key: value for key, value in values.items() if value}
    return definitions


def _parse_flow(path: Path, project_root: Path, definition: dict[str, str], classification_config: dict[str, Any]) -> AutomationDocument:
    root = _parse_xml(path)
    api_name = _api_name(path, FLOW_SUFFIX)
    process_type = child_text(root, "processType") or "Flow"
    label = child_text(root, "label") or api_name
    description = child_text(root, "description")
    status = child_text(root, "status")
    api_version = child_text(root, "apiVersion")
    source = _relative_path(path, project_root)
    facts = _flow_classification_facts(root, api_name, label, source, definition)
    classification = classify_automation(facts, classification_config)
    kind = "Process Builder" if process_type == "Workflow" else "Flow"

    identity_pairs = _classification_identity_pairs(classification, facts) + [
        ("API name", api_name),
        ("Label", label),
        ("Process type", process_type),
        ("Flow shape", _flow_shape(root, process_type)),
        ("Status", status or "Not specified"),
        ("API version", api_version or "Not specified"),
        ("Source", source),
    ]
    if description:
        identity_pairs.append(("Description", description))
    for name, value in process_metadata(root):
        identity_pairs.append((f"Process metadata {name}", value))
    for key in ("activeVersionNumber", "flowDefinitionPath", "description"):
        if definition.get(key):
            identity_pairs.append((f"Flow definition {key}", definition[key]))

    entry_criteria = _flow_entry_criteria(root)
    automation_logic = _flow_automation_logic(root)
    scheduled_paths = _flow_scheduled_paths(root)
    data_changes = _flow_data_changes(root)
    side_effects = _flow_side_effects(root)
    resources = _flow_resources(root)
    dependencies = _flow_dependencies(root)
    error_handling = _flow_error_handling(root)
    raw_inventory = _flow_inventory(root)
    connectors = _flow_connectors(root)

    return AutomationDocument(
        title=label,
        kind=kind,
        api_name=api_name,
        source_path=source,
        identity=tuple((key, value) for key, value in identity_pairs if value),
        metadata_type=classification.metadata_type,
        automation_type=classification.automation_type,
        automation_family=classification.automation_family,
        classification_confidence=classification.classification_confidence,
        classification_evidence=classification.evidence,
        entry_criteria=entry_criteria,
        automation_logic=automation_logic,
        scheduled_paths=scheduled_paths,
        data_changes=data_changes,
        side_effects=side_effects,
        resources=resources,
        dependencies=dependencies,
        error_handling=error_handling,
        testing_notes=(
            "Generated from XML only. Validate trigger criteria, branch coverage, DML outcomes, and called automations before treating this as business documentation.",
        ),
        change_notes=("No change notes found in XML metadata.",),
        raw_inventory=raw_inventory,
        connectors=connectors,
    )


def _parse_workflow(path: Path, project_root: Path) -> AutomationDocument:
    root = _parse_xml(path)
    api_name = _api_name(path, WORKFLOW_SUFFIX)
    source = _relative_path(path, project_root)

    rules = tuple(_workflow_rules(root))
    data_changes = tuple(_workflow_field_updates(root))
    side_effects = tuple(_workflow_side_effects(root))
    raw_inventory = _workflow_inventory(root)
    dependencies = sorted(
        {
            detail
            for item in rules + data_changes + side_effects
            for detail in item.details
            if "." in detail or "/" in detail
        }
    )

    return AutomationDocument(
        title=f"Workflow: {api_name}",
        kind="Workflow",
        api_name=api_name,
        source_path=source,
        identity=(
            ("Metadata type", "Workflow metadata"),
            ("Automation type", "Workflow Rule"),
            ("Classification confidence", "High"),
            ("Object", api_name),
            ("API name", api_name),
            ("Source", source),
        ),
        metadata_type="Workflow metadata",
        automation_type="Workflow Rule",
        classification_confidence="high",
        entry_criteria=rules or (DetailItem("No workflow rules found in this workflow XML."),),
        automation_logic=tuple(_workflow_logic(root)),
        scheduled_paths=tuple(_workflow_scheduled_paths(root)),
        data_changes=data_changes,
        side_effects=side_effects,
        resources=raw_inventory,
        dependencies=tuple(dependencies) or ("No explicit dependencies inferred beyond the workflow object.",),
        error_handling=(DetailItem("Workflow XML does not expose explicit fault paths."),),
        testing_notes=(
            "Generated from XML only. Validate workflow rule criteria, time triggers, and each referenced action.",
        ),
        change_notes=("No change notes found in XML metadata.",),
        raw_inventory=raw_inventory,
    )


def _classification_identity_pairs(classification: ClassificationResult, facts: dict[str, Any]) -> list[tuple[str, str]]:
    pairs = [
        ("Automation name", facts.get("label", "")),
        ("Metadata type", classification.metadata_type),
        ("Automation type", classification.automation_type),
        ("Automation family", classification.automation_family),
        ("Execution model", classification.execution_model),
        ("Classification confidence", _sentence_case(classification.classification_confidence)),
        ("Classification evidence", "; ".join(classification.evidence)),
        ("Active version", facts.get("activeVersionNumber", "")),
        ("Related object / process area", _related_area(facts)),
        ("Source metadata", facts.get("source", "")),
    ]
    if classification.documentation_note:
        pairs.append(("Classification note", classification.documentation_note))
    return pairs


def _flow_classification_facts(
    root: ET.Element,
    api_name: str,
    label: str,
    source: str,
    definition: dict[str, str],
) -> dict[str, Any]:
    start = root.find("start")
    facts: dict[str, Any] = {
        "label": label,
        "apiName": api_name,
        "processType": child_text(root, "processType"),
        "status": child_text(root, "status"),
        "apiVersion": child_text(root, "apiVersion"),
        "activeVersionNumber": definition.get("activeVersionNumber", ""),
        "source": source,
        "description": child_text(root, "description") or definition.get("description", ""),
        "start": {
            "object": child_text(start, "object") if start is not None else "",
            "triggerType": child_text(start, "triggerType") if start is not None else "",
            "recordTriggerType": child_text(start, "recordTriggerType") if start is not None else "",
        },
        "processMetadataValues": dict(process_metadata(root)),
        "variables": _flow_variable_facts(root),
        "elementCounts": _flow_element_counts(root),
    }
    return facts


def _flow_variable_facts(root: ET.Element) -> dict[str, str]:
    variables: dict[str, str] = {}
    for variable in root.findall("variables"):
        name = child_text(variable, "name")
        data_type = child_text(variable, "dataType")
        object_type = child_text(variable, "objectType")
        value = " / ".join(part for part in (data_type, object_type) if part)
        if name and value:
            variables[name] = value
    return variables


def _flow_element_counts(root: ET.Element) -> dict[str, int]:
    return {
        "screens": len(root.findall("screens")),
        "decisions": len(root.findall("decisions")),
        "recordCreates": len(root.findall("recordCreates")),
        "recordUpdates": len(root.findall("recordUpdates")),
        "recordDeletes": len(root.findall("recordDeletes")),
        "actionCalls": len(root.findall("actionCalls")),
        "subflows": len(root.findall("subflows")),
    }


def _related_area(facts: dict[str, Any]) -> str:
    return (
        facts.get("start", {}).get("object")
        or facts.get("processMetadataValues", {}).get("ObjectType")
        or facts.get("apiName", "")
    )


def _sentence_case(value: str) -> str:
    return value[:1].upper() + value[1:] if value else value


def _flow_shape(root: ET.Element, process_type: str) -> str:
    if process_type == "Workflow":
        return "Process Builder"
    if root.findall("screens"):
        return "Screen Flow"
    if root.find("start") is not None:
        trigger_type = child_text(root.find("start"), "triggerType")
        if trigger_type:
            return f"Triggered Flow ({trigger_type})"
    return process_type or "Flow"


def _flow_entry_criteria(root: ET.Element) -> tuple[DetailItem, ...]:
    items: list[DetailItem] = []
    formulas = _formula_map(root)
    process_type = child_text(root, "processType")
    start_reference = child_text(root, "startElementReference")
    metadata = process_metadata(root)
    if metadata:
        items.append(DetailItem("Top-level process metadata", tuple(f"{name}: {value}" for name, value in metadata)))

    for start in root.findall("start"):
        details = []
        for tag in ("object", "triggerType", "recordTriggerType", "filterLogic"):
            value = child_text(start, tag)
            if value:
                details.append(f"{tag}: {value}")
        details.extend(_condition_details(start.findall("filters"), formulas))
        for scheduled_path in start.findall("scheduledPaths"):
            name = child_text(scheduled_path, "name")
            details.append(f"scheduledPath: {name or 'unnamed'}")
        items.append(DetailItem("Start element", tuple(details) or ("No start criteria details found.",)))

    if process_type == "Workflow":
        items.extend(_flow_decisions(root, title="Process Builder criteria node"))

    if start_reference and not items:
        items.append(DetailItem("Start reference", (start_reference,)))

    for lookup in root.findall("recordLookups"):
        name = child_text(lookup, "name")
        object_name = child_text(lookup, "object")
        if object_name and _looks_like_context_lookup(name):
            details = [f"object: {object_name}"]
            filter_logic = child_text(lookup, "filterLogic")
            if filter_logic:
                details.append(f"filterLogic: {filter_logic}")
            details.extend(_condition_details(lookup.findall("filters"), formulas))
            items.append(DetailItem(f"Context lookup: {name or object_name}", tuple(details)))

    return tuple(items) or (DetailItem("No explicit entry criteria found in XML."),)


def _flow_automation_logic(root: ET.Element) -> tuple[DetailItem, ...]:
    items: list[DetailItem] = []
    formulas = _formula_map(root)
    for tag, title in (
        ("decisions", "Decision element"),
        ("assignments", "Assignment"),
        ("recordLookups", "Record lookup"),
        ("recordCreates", "Record create"),
        ("recordUpdates", "Record update"),
        ("recordDeletes", "Record delete"),
        ("loops", "Loop"),
        ("actionCalls", "Action call"),
        ("subflows", "Subflow"),
        ("screens", "Screen"),
        ("collectionProcessors", "Collection processor"),
    ):
        for element in root.findall(tag):
            if tag == "decisions":
                items.append(_flow_decision_item(element, title, formulas))
            else:
                items.append(_flow_element_item(element, title))
    return tuple(items) or (DetailItem("No automation logic elements found."),)


def _flow_decisions(root: ET.Element, title: str = "Decision element") -> tuple[DetailItem, ...]:
    formulas = _formula_map(root)
    return tuple(_flow_decision_item(decision, title, formulas) for decision in root.findall("decisions"))


def _flow_decision_item(decision: ET.Element, title: str, formulas: dict[str, str] | None = None) -> DetailItem:
    details = []
    formula_values = formulas or {}
    metadata = process_metadata(decision)
    if metadata:
        details.extend(f"{name}: {value}" for name, value in metadata)
    for rule in decision.findall("rules"):
        rule_label = child_text(rule, "label") or child_text(rule, "name")
        logic = child_text(rule, "conditionLogic")
        rule_details = [f"rule: {rule_label}"]
        if logic:
            rule_details.append(f"conditionLogic: {logic}")
        rule_details.extend(_condition_details(rule.findall("conditions"), formula_values))
        target = target_reference(rule)
        if target:
            rule_details.append(f"connector: {target}")
        details.append("; ".join(rule_details))
    default_target = target_reference(decision, "defaultConnector")
    default_label = child_text(decision, "defaultConnectorLabel")
    if default_target or default_label:
        details.append(f"default: {'; '.join(part for part in (default_label, default_target) if part)}")
    return DetailItem(
        name=_element_name(decision, title),
        details=tuple(details) or ("No rule criteria found.",),
    )


def _flow_scheduled_paths(root: ET.Element) -> tuple[DetailItem, ...]:
    items: list[DetailItem] = []
    formulas = _formula_map(root)
    for start in root.findall("start"):
        for scheduled_path in start.findall("scheduledPaths"):
            details = _direct_child_details(
                scheduled_path,
                exclude={"name", "label", "connector", "conditions", "inputParameters", "processMetadataValues"},
            )
            details.extend(_condition_details(scheduled_path.findall("conditions"), formulas))
            target = target_reference(scheduled_path)
            if target:
                details.append(f"connector: {target}")
            items.append(DetailItem(_element_name(scheduled_path, "Scheduled path"), tuple(details)))
    for wait in root.findall("waits"):
        details = []
        default_target = target_reference(wait, "defaultConnector")
        if default_target:
            details.append(f"defaultConnector: {default_target}")
        for event in wait.findall("waitEvents"):
            event_details = [f"event: {child_text(event, 'label') or child_text(event, 'name')}"]
            event_type = child_text(event, "eventType")
            if event_type:
                event_details.append(f"eventType: {event_type}")
            logic = child_text(event, "conditionLogic")
            if logic:
                event_details.append(f"conditionLogic: {logic}")
            event_details.extend(_condition_details(event.findall("conditions"), formulas))
            for name, value in named_value_parameters(event):
                event_details.append(f"{name}: {value}")
            target = target_reference(event)
            if target:
                event_details.append(f"connector: {target}")
            details.append("; ".join(event_details))
        items.append(DetailItem(_element_name(wait, "Wait path"), tuple(details) or ("No wait event details found.",)))
    return tuple(items) or (DetailItem("No scheduled paths or wait elements found."),)


def _flow_data_changes(root: ET.Element) -> tuple[DetailItem, ...]:
    items: list[DetailItem] = []
    formulas = _formula_map(root)
    for tag, title in (
        ("recordCreates", "Record create"),
        ("recordUpdates", "Record update"),
        ("recordDeletes", "Record delete"),
        ("recordRollbacks", "Record rollback"),
    ):
        for element in root.findall(tag):
            details: list[str] = []
            object_name = child_text(element, "object")
            if object_name:
                details.append(f"Object: {object_name}")
            filter_logic = child_text(element, "filterLogic")
            if filter_logic:
                details.append(f"filterLogic: {filter_logic}")
            details.extend(_condition_details(element.findall("filters"), formulas))
            for assignment in element.findall("inputAssignments"):
                field = child_text(assignment, "field")
                value = value_text(assignment.find("value"))
                if field or value:
                    details.append(f"{field}: {value}".strip(": "))
            items.append(DetailItem(name=_element_name(element, title), details=tuple(details)))
    return tuple(items) or (DetailItem("No explicit record create/update/delete elements found."),)


def _flow_side_effects(root: ET.Element) -> tuple[DetailItem, ...]:
    items: list[DetailItem] = []
    for element in root.findall("actionCalls"):
        details = [
            f"Action type: {child_text(element, 'actionType') or 'Not specified'}",
            f"Action name: {child_text(element, 'actionName') or 'Not specified'}",
        ]
        for name, value in named_value_parameters(element):
            details.append(f"{name}: {value}")
        items.append(DetailItem(name=_element_name(element, "Action"), details=tuple(details)))
    return tuple(items) or (DetailItem("No action call side effects found."),)


def _flow_resources(root: ET.Element) -> tuple[DetailItem, ...]:
    items: list[DetailItem] = []
    for tag, title in (
        ("formulas", "Formula"),
        ("variables", "Variable"),
        ("constants", "Constant"),
        ("choices", "Choice"),
        ("dynamicChoiceSets", "Dynamic choice set"),
        ("textTemplates", "Text template"),
    ):
        for element in root.findall(tag):
            details = _direct_child_details(element, exclude={"name", "label"})
            value = value_text(element.find("value"))
            if value:
                details.append(f"value: {value}")
            items.append(DetailItem(_element_name(element, title), tuple(details)))
    return tuple(items) or (DetailItem("No formulas, variables, constants, choices, or text templates found."),)


def _flow_dependencies(root: ET.Element) -> tuple[str, ...]:
    values: set[str] = set()
    for tag in ("actionName", "object", "objectType", "elementReference", "assignToReference", "leftValueReference", "field"):
        for element in root.iter(tag):
            if element.text:
                values.add(" ".join(element.text.split()))
    for parameter in root.findall(".//inputParameters"):
        name = child_text(parameter, "name")
        value = value_text(parameter.find("value"))
        if value and name in {"template", "emailAddresses", "subjectNameOrId", "SObject", "recordId"}:
            values.add(f"{name}: {value}")
    return tuple(sorted(values)) or ("No dependencies inferred from XML references.",)


def _flow_error_handling(root: ET.Element) -> tuple[DetailItem, ...]:
    items: list[DetailItem] = []
    for element in root.iter():
        fault = element.find("faultConnector")
        if fault is not None:
            target = child_text(fault, "targetReference")
            items.append(DetailItem(name=_element_name(element, element.tag), details=(f"Fault target: {target}",)))
    error_actions = [
        _flow_element_item(element, "Error action")
        for element in root.findall("actionCalls")
        if "error" in (_element_name(element, "") + " " + child_text(element, "actionName")).lower()
    ]
    return tuple(items + error_actions) or (DetailItem("No explicit fault connectors found."),)


def _flow_inventory(root: ET.Element) -> tuple[DetailItem, ...]:
    flow_sections = (
        "actionCalls",
        "assignments",
        "choices",
        "collectionProcessors",
        "constants",
        "decisions",
        "dynamicChoiceSets",
        "formulas",
        "loops",
        "recordCreates",
        "recordDeletes",
        "recordLookups",
        "recordUpdates",
        "screens",
        "stages",
        "subflows",
        "textTemplates",
        "variables",
        "waits",
    )
    items: list[DetailItem] = []
    for tag in flow_sections:
        nodes = root.findall(tag)
        if nodes:
            names = tuple(_inventory_detail(node, tag) for node in nodes)
            items.append(DetailItem(f"{tag}: {len(nodes)}", names))
    return tuple(items)


def _flow_connectors(root: ET.Element) -> tuple[str, ...]:
    edges: set[str] = set()
    for element in root.iter():
        source = child_text(element, "name")
        if not source:
            continue
        for connector_tag in ("connector", "defaultConnector", "nextValueConnector", "noMoreValuesConnector"):
            target = target_reference(element, connector_tag)
            if target:
                edges.add(f"{source} -> {target}")
    return tuple(sorted(edges))


def _workflow_rules(root: ET.Element) -> list[DetailItem]:
    items: list[DetailItem] = []
    for rule in root.findall("rules"):
        details = []
        for tag in ("active", "description", "formula", "triggerType", "booleanFilter"):
            value = child_text(rule, tag)
            if value:
                details.append(f"{tag}: {value}")
        for criteria in rule.findall("criteriaItems"):
            field = child_text(criteria, "field")
            operation = child_text(criteria, "operation")
            value = child_text(criteria, "value")
            details.append(f"criteria: {' '.join(part for part in (field, operation, value) if part)}")
        for time_trigger in rule.findall("workflowTimeTriggers"):
            trigger_details = []
            for tag in ("timeLength", "workflowTimeTriggerUnit", "actions"):
                value = child_text(time_trigger, tag)
                if value:
                    trigger_details.append(f"{tag}: {value}")
            if trigger_details:
                details.append(f"time trigger: {'; '.join(trigger_details)}")
        for action_tag in ("actions", "alerts", "fieldUpdates", "tasks", "outboundMessages"):
            for action in rule.findall(action_tag):
                name = child_text(action, "name") or child_text(action, "fullName")
                if name:
                    details.append(f"{action_tag}: {name}")
        items.append(DetailItem(child_text(rule, "fullName") or "Workflow rule", tuple(details)))
    return items


def _workflow_logic(root: ET.Element) -> list[DetailItem]:
    items = _workflow_rules(root)
    items.extend(_workflow_side_effects(root))
    items.extend(_workflow_field_updates(root))
    return items or [DetailItem("No workflow logic found.")]


def _workflow_scheduled_paths(root: ET.Element) -> list[DetailItem]:
    items: list[DetailItem] = []
    for rule in root.findall("rules"):
        rule_name = child_text(rule, "fullName") or "Workflow rule"
        for time_trigger in rule.findall("workflowTimeTriggers"):
            details = _direct_child_details(time_trigger, exclude={"actions"})
            for action in time_trigger.findall("actions"):
                action_name = child_text(action, "name")
                action_type = child_text(action, "type")
                details.append(f"action: {' '.join(part for part in (action_type, action_name) if part)}")
            items.append(DetailItem(f"Workflow time trigger: {rule_name}", tuple(details)))
    return items or [DetailItem("No workflow time triggers found.")]


def _workflow_field_updates(root: ET.Element) -> list[DetailItem]:
    items: list[DetailItem] = []
    for update in root.findall("fieldUpdates"):
        details = []
        for tag in ("field", "literalValue", "formula", "operation", "notifyAssignee"):
            value = child_text(update, tag)
            if value:
                details.append(f"{tag}: {value}")
        items.append(DetailItem(child_text(update, "fullName") or "Field update", tuple(details)))
    return items or [DetailItem("No workflow field updates found.")]


def _workflow_side_effects(root: ET.Element) -> list[DetailItem]:
    items: list[DetailItem] = []
    for tag, title in (
        ("alerts", "Email alert"),
        ("tasks", "Task"),
        ("outboundMessages", "Outbound message"),
        ("knowledgePublishes", "Knowledge publish"),
        ("flowActions", "Flow action"),
    ):
        for action in root.findall(tag):
            details = []
            for child in list(action):
                if child.tag == "recipients":
                    recipient_type = child_text(child, "type")
                    recipient = child_text(child, "recipient")
                    details.append(f"recipient: {recipient_type} {recipient}".strip())
                elif child.text and child.tag != "fullName":
                    details.append(f"{child.tag}: {' '.join(child.text.split())}")
            items.append(DetailItem(f"{title}: {child_text(action, 'fullName')}", tuple(details)))
    return items or [DetailItem("No workflow action side effects found.")]


def _workflow_inventory(root: ET.Element) -> tuple[DetailItem, ...]:
    tags = ("rules", "alerts", "fieldUpdates", "tasks", "outboundMessages", "flowActions")
    return tuple(
        DetailItem(f"{tag}: {len(root.findall(tag))}", tuple(child_text(node, "fullName") for node in root.findall(tag)))
        for tag in tags
        if root.findall(tag)
    )


def _flow_element_item(element: ET.Element, title: str) -> DetailItem:
    details: list[str] = []
    label = child_text(element, "label")
    if label:
        details.append(f"Label: {label}")
    details.extend(_direct_child_details(element, exclude={"name", "label", "connector", "faultConnector", "processMetadataValues"}))
    target = target_reference(element)
    if target:
        details.append(f"Next: {target}")
    fault_target = target_reference(element, "faultConnector")
    if fault_target:
        details.append(f"Fault: {fault_target}")
    if element.findall("filters"):
        details.extend(_condition_details(element.findall("filters"), _formula_map(element)))
    for assignment in element.findall("assignmentItems"):
        assign_to = child_text(assignment, "assignToReference")
        operator = child_text(assignment, "operator")
        value = value_text(assignment.find("value"))
        details.append(f"assignment: {' '.join(part for part in (assign_to, operator, value) if part)}")
    for assignment in element.findall("inputAssignments"):
        field = child_text(assignment, "field")
        value = value_text(assignment.find("value"))
        details.append(f"inputAssignment: {' = '.join(part for part in (field, value) if part)}")
    for field in element.findall(".//fields"):
        field_name = child_text(field, "name") or child_text(field, "fieldText")
        field_type = child_text(field, "fieldType") or child_text(field, "dataType")
        if field_name or field_type:
            details.append(f"screenField: {' | '.join(part for part in (field_name, field_type) if part)}")
    metadata = process_metadata(element)
    if metadata:
        details.extend(f"{name}: {value}" for name, value in metadata)
    for name, value in named_value_parameters(element):
        details.append(f"{name}: {value}")
    return DetailItem(name=_element_name(element, title), details=tuple(details))


def _condition_details(conditions: list[ET.Element], formulas: dict[str, str] | None = None) -> list[str]:
    details: list[str] = []
    formula_lookup = formulas or {}
    for index, condition in enumerate(conditions, start=1):
        text = condition_text(condition)
        if text:
            details.append(f"condition {index}: {text}")
        left = child_text(condition, "leftValueReference")
        if left in formula_lookup:
            details.append(f"condition {index} formula {left}: {formula_lookup[left]}")
        metadata = process_metadata(condition)
        if metadata:
            details.extend(f"condition {index} metadata {name}: {value}" for name, value in metadata)
    return details


def _formula_map(root: ET.Element) -> dict[str, str]:
    document = root
    while document.tag != "Flow" and document.tag != "Workflow":
        break
    return {
        child_text(formula, "name"): child_text(formula, "expression")
        for formula in document.findall("formulas")
        if child_text(formula, "name") and child_text(formula, "expression")
    }


def _direct_child_details(element: ET.Element, exclude: set[str] | None = None) -> list[str]:
    excluded = exclude or set()
    details: list[str] = []
    repeated_children = {
        "assignmentItems",
        "conditions",
        "filters",
        "inputAssignments",
        "inputParameters",
        "outputAssignments",
        "processMetadataValues",
        "rules",
        "fields",
        "waitEvents",
    }
    for child in list(element):
        if child.tag in excluded or child.tag in repeated_children:
            continue
        if list(child):
            value = value_text(child)
        else:
            value = child_text(element, child.tag)
        if value:
            details.append(f"{child.tag}: {value}")
    return details


def _looks_like_context_lookup(name: str) -> bool:
    lowered = name.lower()
    return "context" in lowered or "recordlookup" in lowered or "contextrecord" in lowered


def _element_name(element: ET.Element, fallback: str) -> str:
    name = child_text(element, "name")
    label = child_text(element, "label")
    if label and name and label != name:
        return f"{fallback}: {label} ({name})" if fallback else f"{label} ({name})"
    return f"{fallback}: {label or name}" if fallback else label or name or element.tag


def _inventory_detail(element: ET.Element, tag: str) -> str:
    name = _element_name(element, tag)
    parts: list[str] = []

    if tag == "formulas":
        for child_tag in ("dataType", "expression", "scale"):
            value = child_text(element, child_tag)
            if value:
                parts.append(f"{child_tag}: {value}")
    elif tag == "variables":
        for child_tag in ("dataType", "objectType", "isCollection", "isInput", "isOutput"):
            value = child_text(element, child_tag)
            if value:
                parts.append(f"{child_tag}: {value}")
        initial = value_text(element.find("value"))
        if initial:
            parts.append(f"value: {initial}")
    elif tag in {"constants", "choices", "dynamicChoiceSets"}:
        for child_tag in ("dataType", "choiceText", "object", "displayField", "valueField"):
            value = child_text(element, child_tag)
            if value:
                parts.append(f"{child_tag}: {value}")
        initial = value_text(element.find("value"))
        if initial:
            parts.append(f"value: {initial}")
    elif tag == "textTemplates":
        description = child_text(element, "description")
        text = child_text(element, "text")
        if description:
            parts.append(f"description: {description}")
        if text:
            parts.append(f"text: {text}")
    elif tag in {"recordLookups", "recordCreates", "recordUpdates", "recordDeletes"}:
        object_name = child_text(element, "object")
        if object_name:
            parts.append(f"object: {object_name}")
        filters = [condition_text(node) for node in element.findall("filters")]
        filters = [item for item in filters if item]
        if filters:
            parts.append(f"filters: {'; '.join(filters)}")
    elif tag == "actionCalls":
        for child_tag in ("actionType", "actionName"):
            value = child_text(element, child_tag)
            if value:
                parts.append(f"{child_tag}: {value}")

    if parts:
        return f"{name} | {'; '.join(parts)}"
    return name


def _parse_xml(path: Path) -> ET.Element:
    root = ET.parse(path).getroot()
    strip_namespace(root)
    return root


def _api_name(path: Path, suffix: str) -> str:
    name = path.name
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return path.stem


def _relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()
