# Authoring Framework Assets

## Portable Source

Put authored reusable assets under `.ai/`. Treat tool-specific files as generated adapters.

## Guidance

Put reusable project-wide behavior in `.ai/guides`. Keep guidance stable and broadly applicable. Avoid project-specific commands, service names, and credentials.

Use supplemental guides such as `frontend.md` and `backend.md` for task-domain rules that agents should load only when relevant.

## Agents

Put portable agents in `.ai/agents/<name>.md`. Each agent uses simple YAML frontmatter:

```yaml
---
name: reviewer
description: Review code for bugs, regressions, security issues, data risks, and missing tests.
model: inherit
tools: read
permission_mode: read-only
---
```

The Markdown body is the portable system prompt. The installer renders Codex TOML into `.codex/agents/` and Claude Code Markdown into `.claude/agents/`.

Supported portable `tools` values are `read`, `write`, `web`, and `orchestrate`. Use `orchestrate` only for the default orchestrator agent because it renders Claude Code's `Agent` tool.

Supported `permission_mode` values are `read-only` and `project-write`.

Generated tool-specific agents are adapters with source markers. Do not edit generated `.codex/agents` or `.claude/agents` files as framework sources.

## Skills

Put skills in `.ai/skills/<skill-name>`. Each skill needs a `SKILL.md` with YAML frontmatter containing only `name` and `description`.

Use `references/` for optional details that are not always needed. Use `scripts/` only for deterministic reusable automation that is worth testing directly.

Codex skill installs under `.agents/skills` are generated copies with provenance markers on `SKILL.md`. Keep authored skill content in `.ai/skills`.

## Templates

Put reusable workflow templates in `.ai/templates`. The core pack installs:

- `task-spec.md` for approved task documents in `docs/tasks/`.
- `local-progress.md` for ignored progress state in `.local/tasks/`.
- `adr.md` for durable decisions and implementation records in `docs/adr/`.
- `harness-registry.md`, `harness-entry.md`, and `harness-script.sh` for validation harness creation.

## Harnesses

Put reusable validation harness scripts under `.ai/harnesses/scripts`. Register every harness in `.ai/harnesses/registry.md` so reviewer, implementer, and test-debugger agents can discover the correct command before falling back to ad hoc validation.

## Packs

Packs in `framework/packs` declare installable groups of guide, adapters, templates, agents, and skills. Keep pack files simple so the dependency-free harness can parse them.

After any change, run:

```bash
framework/harness/validate.sh
```
