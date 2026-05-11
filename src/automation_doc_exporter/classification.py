from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONFIG_PATH = Path("config/automation_classification_rules.json")


@dataclass(frozen=True)
class ClassificationResult:
    metadata_type: str
    automation_type: str
    classification_confidence: str
    automation_family: str = ""
    execution_model: str = ""
    documentation_note: str = ""
    matched_rule_id: str = ""
    evidence: tuple[str, ...] = ()


def load_classification_config(project_root: Path) -> dict[str, Any]:
    path = _resolve_config_path(project_root)
    return json.loads(path.read_text(encoding="utf-8"))


def classify_automation(facts: dict[str, Any], config: dict[str, Any]) -> ClassificationResult:
    for rule in sorted(config.get("rules", ()), key=lambda item: item.get("priority", 0), reverse=True):
        if _rule_matches(rule, facts):
            return _classification_result(
                rule.get("classify_as", {}),
                rule.get("evidence_paths", ()),
                facts,
                documentation_note=rule.get("documentation_note", ""),
                matched_rule_id=rule.get("id", ""),
            )

    return _classification_result(
        config.get("fallback", {}),
        config.get("fallback", {}).get("evidence_paths", ()),
        facts,
        documentation_note=config.get("fallback", {}).get("documentation_note", ""),
    )


def evidence_for_paths(facts: dict[str, Any], paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    evidence: list[str] = []
    for path in paths:
        value = lookup_path(facts, path)
        if _has_value(value):
            evidence.append(f"{path} = {_format_value(value)}")
    return tuple(evidence)


def lookup_path(values: dict[str, Any], path: str) -> Any:
    current: Any = values
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _resolve_config_path(project_root: Path) -> Path:
    candidates = [
        project_root / CONFIG_PATH,
        Path.cwd() / CONFIG_PATH,
        Path(__file__).resolve().parents[3] / CONFIG_PATH,
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"Automation classification config not found at {CONFIG_PATH}")


def _rule_matches(rule: dict[str, Any], facts: dict[str, Any]) -> bool:
    when_all = rule.get("when_all")
    when_any = rule.get("when_any")
    if when_all and not all(_condition_matches(condition, facts) for condition in when_all):
        return False
    if when_any and not any(_condition_matches(condition, facts) for condition in when_any):
        return False
    return bool(when_all or when_any)


def _condition_matches(condition: dict[str, Any], facts: dict[str, Any]) -> bool:
    value = lookup_path(facts, condition["path"])
    if "equals" in condition:
        return value == condition["equals"]
    if "exists" in condition:
        return _has_value(value) is bool(condition["exists"])
    if "gt" in condition:
        try:
            return float(value) > float(condition["gt"])
        except (TypeError, ValueError):
            return False
    return False


def _classification_result(
    values: dict[str, Any],
    evidence_paths: list[str] | tuple[str, ...],
    facts: dict[str, Any],
    *,
    documentation_note: str = "",
    matched_rule_id: str = "",
) -> ClassificationResult:
    return ClassificationResult(
        metadata_type=values.get("metadata_type", ""),
        automation_type=values.get("automation_type", ""),
        automation_family=values.get("automation_family", ""),
        execution_model=values.get("execution_model", ""),
        classification_confidence=values.get("classification_confidence", ""),
        documentation_note=documentation_note or values.get("documentation_note", ""),
        matched_rule_id=matched_rule_id,
        evidence=evidence_for_paths(facts, evidence_paths),
    )


def _has_value(value: Any) -> bool:
    return value is not None and value != "" and value != () and value != [] and value != {}


def _format_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)
