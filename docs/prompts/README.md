# WSO26 Agent Instructions Bundle

This bundle contains reusable Markdown instructions for agents that generate Salesforce automation documentation from evidence files.

## Correct repository paths

### GitHub Copilot custom agent

```text
.github/agents/salesforce-automation-documentation.agent.md
```

Use this when you want a selectable GitHub Copilot custom agent for documentation work in the repository.

### Codex repo-scoped skill

```text
.agents/skills/salesforce-automation-documentation/SKILL.md
```

Use this when you want Codex to discover a reusable documentation-generation skill from the repository.

### Optional Codex / agent repo guidance

```text
AGENTS.md
```

Use this only for short durable repo guidance. Do not put the full prompt there unless you want every Codex task in the repo to carry that extra instruction weight.

### Canonical standalone prompt

```text
docs/prompts/evidence-to-blueprint-and-map.prompt.md
```

Use this when you want a full copy-paste prompt for any AI tool, outside the custom-agent / skill mechanism.

## Files included

```text
.github/agents/salesforce-automation-documentation.agent.md
.agents/skills/salesforce-automation-documentation/SKILL.md
AGENTS.md
docs/prompts/evidence-to-blueprint-and-map.prompt.md
```

## Recommended use

For GitHub Copilot, commit the `.agent.md` file under `.github/agents/` in the repository where you want the custom agent to be available.

For Codex, commit the skill under `.agents/skills/` in the repository. Codex can also use user-level skills from `$HOME/.agents/skills`, but for this project the repo-scoped path is the cleaner choice.

Use `AGENTS.md` only as a short router / rule reminder, for example to tell Codex that documentation generation from evidence files should use the Salesforce automation documentation skill.

## Core principle

> Metadata provides evidence. AI may interpret the evidence. Business meaning must be marked as proposed unless explicitly present in the evidence.

## Core output model

1. Automation Impact Map — navigation layer.
2. Living Technical Blueprint — explanation layer.
3. Review notes — validation and uncertainty layer.
