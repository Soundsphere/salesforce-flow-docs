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

    # Determine output directory
    if output_path.suffix == '.md':
        output_dir = output_path.parent
    else:
        output_dir = output_path
    output_dir.mkdir(parents=True, exist_ok=True)

    flow_count = 0
    workflow_count = 0

    for document in documents:
        # Create markdown filename from XML filename
        xml_path = Path(document.source_path)
        md_name = xml_path.stem + ".md"
        output_file = output_dir / md_name

        markdown = render_markdown([document])
        output_file.write_text(markdown, encoding="utf-8")

        if document.metadata_type == "Flow metadata":
            flow_count += 1
        if document.kind == "Workflow":
            workflow_count += 1

    return ExportSummary(flow_count=flow_count, workflow_count=workflow_count)
