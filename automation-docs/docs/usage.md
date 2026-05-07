# Automation Docs Exporter

This tool exports Salesforce Flow, Process Builder, and Workflow XML metadata into one deterministic Markdown file.

## Structure

- `automation-docs/src/automation_doc_exporter` - Python source code.
- `automation-docs/tests` - unit tests, using only Python standard library.
- `automation-docs/output` - generated Markdown files.
- `automation-docs/docs` - documentation for the exporter.
- `automation-docs/Dockerfile` - container image for running the exporter.
- `automation-docs/compose.yml` - compose services for export and tests.

## Run From Project Root

```bash
docker compose -f automation-docs/compose.yml run --rm automation-docs
```

The default output file is:

```text
automation-docs/output/salesforce-automation.md
```

## Run Tests

```bash
docker compose -f automation-docs/compose.yml run --rm tests
```

## Output Contract

The exporter writes one Markdown document. Each automation starts with a level-one heading based on the Flow label, or `Workflow: <Object>` for workflow metadata:

```markdown
# Flow Label
## Identity
## Entry Criteria
## Automation Logic
## Data and Side Effects
## Operational Trust
## XML Extraction Detail
```

The output is deterministic: files are discovered from the project root, paths are stored as relative paths, and items are sorted before rendering where XML ordering is not semantically important. XML `decisions` are rendered as technical branching logic, not business decisions.
