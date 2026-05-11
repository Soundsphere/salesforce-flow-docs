from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .markdown import render_markdown
from .parser import collect_automation_documents


@dataclass(frozen=True)
class ExportSummary:
    flow_count: int
    workflow_count: int


def export_automation_markdown(project_root: Path, output_path: Path) -> ExportSummary:
    documents = collect_automation_documents(project_root)
    markdown = render_markdown(documents)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    flow_count = sum(1 for document in documents if document.metadata_type == "Flow metadata")
    workflow_count = sum(1 for document in documents if document.kind == "Workflow")
    return ExportSummary(flow_count=flow_count, workflow_count=workflow_count)
