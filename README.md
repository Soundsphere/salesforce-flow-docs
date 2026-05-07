# Salesforce Flow Docs Starter Kit

A small example repository showing one practical way to document Salesforce automation from metadata.

This repository was created as a companion example for the session:

**From “I Have a Flow” to “I Know What Happens”**

The main idea is simple:

> Do not start by asking AI to document a Salesforce org from a blank prompt.  
> First extract repeatable facts from metadata. Then use those facts to create useful documentation.

## What this repository demonstrates

Salesforce Flow is visual, but the canvas alone does not explain the full behaviour of an org.

This starter kit shows a lightweight documentation workflow:

```text
Salesforce Flow metadata
        ↓
Deterministic extraction
        ↓
Structured technical Markdown
        ↓
AI-assisted documentation draft
        ↓
Human review
        ↓
Automation Impact Map + Living Technical Blueprint
```

The goal is not perfect documentation.

The goal is to make automation understandable enough to support impact analysis and safe change.

## What is included

This repository contains:

- a small Salesforce DX project with example Salesforce metadata,
- an example record-triggered Flow,
- a Python-based metadata extractor,
- generated technical Markdown output,
- example documentation artifacts,
- reusable AI prompts and agent instructions.

## Repository structure

```text
force-app/
  main/default/
    flows/
    objects/
    layouts/
    permissionsets/

automation-docs/
  src/automation_doc_exporter/
  tests/
  docs/
  output/

docs/
  automation/
  prompts/

.github/agents/
.agents/skills/
AGENTS.md
```

### `force-app/`

Contains the Salesforce metadata used as the example input.

The main example is a record-triggered Flow for Contract renewal follow-up.

### `automation-docs/`

Contains the deterministic exporter.

The exporter reads Salesforce automation metadata and produces a structured Markdown evidence file.

The generated example output is here:

```text
automation-docs/output/salesforce-automation.md
```

This output is intentionally committed so the documentation workflow can be reviewed without running the tool first.

### `docs/automation/`

Contains the human-readable documentation layer.

This is where the example Living Technical Blueprint lives.

### `docs/prompts/`

Contains reusable prompts for converting technical evidence into:

- an Automation Impact Map row,
- a Living Technical Blueprint section,
- review notes and assumptions.

### `.github/agents/` and `.agents/skills/`

Contain reusable instructions for AI-assisted documentation workflows.

These are optional. They are included to show how the same documentation rules can be reused by tools such as GitHub Copilot or Codex.

## How to run the exporter

From the repository root:

```bash
docker compose -f automation-docs/compose.yml run --rm automation-docs
```

The default output file is:

```text
automation-docs/output/salesforce-automation.md
```

## How to run tests

```bash
docker compose -f automation-docs/compose.yml run --rm tests
```

## Documentation model

This repository uses two connected documentation layers.

### 1. Automation Impact Map

The map is the navigation layer.

It should help answer questions such as:

- what automation exists,
- where it runs,
- what object or process area it belongs to,
- what data it changes,
- what side effects it may cause,
- where the detailed explanation lives.

### 2. Living Technical Blueprint

The blueprint is the explanation layer.

It should explain:

- why the automation exists,
- when it runs,
- what it does,
- what decisions it makes,
- what data it changes,
- what side effects and dependencies matter,
- how it fails,
- how it should be validated before change.

## AI-assisted documentation principle

AI can help transform evidence into readable documentation, but it should not invent business meaning.

Use this rule:

> Metadata provides evidence. AI may interpret the evidence. Business meaning must be marked as proposed unless explicitly present in the evidence.

A generated draft should be reviewed by someone who understands the business process and the Salesforce org.

## Example workflow

1. Review the example Flow metadata in `force-app/main/default/flows/`.
2. Run the exporter or inspect the committed output in `automation-docs/output/`.
3. Use the prompt in `docs/prompts/` to create a documentation draft.
4. Review the generated draft.
5. Update the Automation Impact Map and Living Technical Blueprint.

## What this is not

This is not a complete Salesforce documentation product.

It is not an official Salesforce tool.

It is not a replacement for architecture review, testing, or human validation.

It is a small, practical starter kit showing how metadata, deterministic extraction, Markdown, and AI-assisted drafting can work together.

## Why this matters

In mature Salesforce orgs, one Flow rarely tells the whole story.

A record change may trigger Flows, Apex, validation rules, related-object automation, scheduled paths, notifications, integrations, or managed package logic.

Good documentation should help answer the real maintenance question:

> What happens if this changes?

