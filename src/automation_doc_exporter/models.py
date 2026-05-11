from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DetailItem:
    name: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class AutomationDocument:
    title: str
    kind: str
    api_name: str
    source_path: str
    identity: tuple[tuple[str, str], ...]
    metadata_type: str = ""
    automation_type: str = ""
    automation_family: str = ""
    classification_confidence: str = ""
    classification_evidence: tuple[str, ...] = ()
    entry_criteria: tuple[DetailItem, ...] = ()
    automation_logic: tuple[DetailItem, ...] = ()
    scheduled_paths: tuple[DetailItem, ...] = ()
    data_changes: tuple[DetailItem, ...] = ()
    side_effects: tuple[DetailItem, ...] = ()
    resources: tuple[DetailItem, ...] = ()
    dependencies: tuple[str, ...] = ()
    error_handling: tuple[DetailItem, ...] = ()
    testing_notes: tuple[str, ...] = ()
    change_notes: tuple[str, ...] = ()
    raw_inventory: tuple[DetailItem, ...] = field(default_factory=tuple)
    connectors: tuple[str, ...] = ()
