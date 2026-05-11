from __future__ import annotations

import argparse
from pathlib import Path

from .exporter import export_automation_markdown

DEFAULT_OUTPUT_DIR = "descriptions"
DEFAULT_OUTPUT_FILENAME = ""


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
        default=None,
        help="Markdown output file, relative to project root unless absolute. Overrides --output-dir.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the generated evidence file, relative to project root unless absolute.",
    )
    return parser


def resolve_output_path(project_root: Path, output: str | None, output_dir: str) -> Path:
    if output:
        output_path = Path(output)
    else:
        output_path = Path(output_dir) / DEFAULT_OUTPUT_FILENAME

    if not output_path.is_absolute():
        return project_root / output_path
    return output_path


def display_output_path(project_root: Path, output_path: Path) -> Path:
    try:
        return output_path.relative_to(project_root)
    except ValueError:
        return output_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_path = resolve_output_path(
        project_root=project_root,
        output=args.output,
        output_dir=args.output_dir,
    )

    summary = export_automation_markdown(project_root=project_root, output_path=output_path)
    print(
        "Wrote {output} with {flows} flows/process builders and {workflows} workflow files.".format(
            output=display_output_path(project_root, output_path),
            flows=summary.flow_count,
            workflows=summary.workflow_count,
        )
    )
    return 0
