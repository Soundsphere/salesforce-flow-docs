---
name: salesforce-automation-documentation
description: Use this skill when asked to create or update a Living Technical Blueprint, Automation Impact Map, Flow documentation, or review notes from Salesforce automation evidence files. Do not use it for extractor implementation unless explicitly asked.
---

# Salesforce Automation Documentation Skill

## Purpose

Use this skill to transform deterministic Salesforce automation evidence files into reviewable documentation.

The evidence file is a technical evidence layer. It may come from Flow XML metadata transformed into structured Markdown. It is not final business documentation.

The output should help people understand automation behaviour, dependencies, side effects, and change impact.

The central question is:

> What happens if this changes?

## When to use this skill

Use this skill when the user asks for any of the following:

- Generate a Living Technical Blueprint from an evidence file.
- Generate an Automation Impact Map from an evidence file.
- Update an existing blueprint or map from new evidence.
- Compare current documentation against evidence.
- Create review notes showing what requires human validation.
- Draft documentation for Salesforce Flow or automation from extracted metadata.

Do not use this skill for normal code implementation unless the user explicitly asks to change the extractor or tooling.

## Operating principle

Use this rule throughout:

> Metadata provides evidence. AI may interpret the evidence. Business meaning must be marked as proposed unless explicitly present in the evidence.

Do not invent facts.

Do not claim generated documentation is validated.

Do not assume one Flow tells the whole story.

## Inputs to inspect

Before writing output, inspect the files the user points to.

Typical input files:

- evidence file
- existing Living Technical Blueprint
- existing Automation Impact Map
- previous generated documentation
- Jira / Azure DevOps context
- release notes
- naming convention or documentation template

If no existing output file is provided, create a new Markdown output and make the filename clear.

Suggested filenames:

- `docs/automation/living-technical-blueprint.md`
- `docs/automation/automation-impact-map.md`
- `docs/automation/review-notes.md`

If the repository already has conventions, follow them.

## Required certainty labels

Use these labels consistently:

- Confirmed from evidence
- Inferred from technical structure
- Proposed interpretation
- Missing / requires validation

Never present inferred business meaning as confirmed fact.

## Blueprint output structure

For each automation, create or update this structure:

```markdown
# [Automation / Flow Name]

## 1. Flow identity

| Field | Value |
|---|---|
| Flow label | |
| API name | |
| Type | |
| Status | |
| Active version | |
| Object / process area | |
| Trigger / timing | |
| Owner | Missing / validate |
| Documentation status | Draft from evidence |

## 2. Business purpose

- Confirmed from evidence:
- Proposed interpretation:
- Requires validation:

## 3. Trigger and scope

Explain when the automation runs, for which records, with which trigger criteria and timing.

## 4. Main logic

Summarise high-level behaviour. Do not mechanically list every element.

## 5. Key decisions

| Decision | Evidence | Interpreted meaning | Notes |
|---|---|---|---|

## 6. Data changes and side effects

### Direct effects

| Operation | Object | Field / target | Value / source | Notes |
|---|---|---|---|---|

### Side effects

List visible side effects: tasks, emails, notifications, subflows, Apex actions, platform events, integrations, external actions.

### Potential downstream effects

List only what is confirmed or reasonably inferred. Mark uncertainty clearly.

## 7. Dependencies

Group dependencies into:

- Data dependencies
- Automation dependencies
- Integration / action dependencies
- Configuration dependencies
- Unknown / requires validation

Avoid noisy raw dependency dumps.

## 8. Error handling and observability

Explain fault paths, custom errors, logging, alerts, user-visible errors, and missing/unclear error handling.

## 9. Testing and validation

Suggest proposed validation scenarios unless actual tests are provided.

## 10. Change notes

Summarise change context if provided. Otherwise state that change context was not included.

## 11. Open questions for human validation

List only specific, meaningful validation questions.
```

## Automation Impact Map output structure

Use this compact table:

```markdown
| Name | Type | Object / Process Area | Trigger / Timing | Purpose | Data Changed | Side Effects / Dependencies | Risk / Criticality | Owner | Documentation Status | Last Reviewed | Detail Link |
|---|---|---|---|---|---|---|---|---|---|---|---|
```

Rules:

- Keep the row useful as an inventory, not as full documentation.
- Prefix inferred purpose with `Proposed:`.
- Use `Missing / validate`, `TBD`, or `Not visible in evidence` rather than guessing.
- Data Changed should list key objects/fields, not internal variables.
- Side Effects / Dependencies should focus on impact analysis.
- Risk may be proposed but must be marked as proposed unless explicitly provided.

## Conflict handling

If existing documentation conflicts with evidence:

1. Do not silently overwrite.
2. Preserve human-authored business context unless clearly obsolete.
3. Add a review note explaining the mismatch.
4. Suggest what to validate.

## Required review notes

Every generated or updated documentation output must include:

```markdown
## Review notes

### Confirmed from evidence

- ...

### Inferred / proposed

- ...

### Missing or requires validation

- ...

### Possible documentation risks

- ...
```

## Quality checklist

Before finishing, verify:

1. Evidence was inspected.
2. Existing documentation structure was preserved where reasonable.
3. Facts were separated from interpretation.
4. Trigger and scope are clear.
5. Direct data changes are clear.
6. Side effects and dependencies are clear.
7. Missing owner, purpose, risk, tests, and change context are visible.
8. Human validation notes are included.
9. The output helps answer: “What happens if this changes?”

## Final response format

In the final response, include:

- files read;
- files created or updated;
- whether blueprint, map, or both were generated;
- key assumptions or missing information;
- whether human validation is required;
- checks run, if any.

Do not call the documentation final unless human validation was explicitly provided.
