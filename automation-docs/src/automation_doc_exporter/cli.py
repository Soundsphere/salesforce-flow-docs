from __future__ import annotations

import argparse
from pathlib import Path

from .exporter import export_automation_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Salesforce Flow, Process Builder, and Workflow metadata to deterministic Markdown."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Salesforce project root. Defaults to current directory.",
    )
    parser.add_argument(
        "--output",
        default="automation-docs/output/salesforce-automation.md",
        help="Markdown output file, relative to project root unless absolute.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    summary = export_automation_markdown(project_root=project_root, output_path=output_path)
    print(
        "Wrote {output} with {flows} flows/process builders and {workflows} workflow files.".format(
            output=output_path.relative_to(project_root),
            flows=summary.flow_count,
            workflows=summary.workflow_count,
        )
    )
    return 0

