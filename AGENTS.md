# AGENTS.md — Salesforce Automation Documentation

This repository contains Salesforce automation evidence files and documentation generated from them.

## Durable project rule

When working on documentation generated from Salesforce automation evidence files, follow this principle:

> Metadata provides evidence. AI may interpret the evidence. Business meaning must be marked as proposed unless explicitly present in the evidence.

The goal is to help maintainers answer:

> What happens if this changes?

## Preferred reusable instruction

For Codex, use the `salesforce-automation-documentation` skill when the task involves:

- Living Technical Blueprint generation or update;
- Automation Impact Map generation or update;
- Flow documentation from evidence files;
- review notes for human validation;
- checking whether existing documentation still matches evidence.

Do not paste the full prompt every time. Prefer invoking the reusable skill or relying on this repository guidance.

## Documentation outputs

The standard documentation model has two connected layers:

1. **Automation Impact Map** — navigation layer.
2. **Living Technical Blueprint** — explanation layer.

The map tells people where to look.  
The blueprint helps people understand what they found.

## Certainty labels

Use these labels consistently:

- Confirmed from evidence
- Inferred from technical structure
- Proposed interpretation
- Missing / requires validation

Do not invent business intent, owner, risk level, or downstream behaviour.

## Non-goals

Do not modify Salesforce metadata or extractor code unless explicitly asked.

Do not turn the output into a raw metadata dump.

Do not claim generated documentation is final or validated without human validation.
