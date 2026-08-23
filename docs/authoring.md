# Authoring Framework Assets

## Portable Source

Put authored reusable assets under `.ai/`. Treat tool-specific files as generated adapters.

Keep `.ai/agent-capabilities.md` current when adding agents or skills. It defines routing conditions and the minimum context/output contract for each role.

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

Portable skills should not embed project-specific validation commands. For browser visual QA, keep reusable workflow guidance in skills such as `playwright-visual-review`, then create project-specific Playwright harness scripts with `create-harness` and register them in `.ai/harnesses/registry.md`.

## Templates

Put reusable workflow templates in `.ai/templates`. The core pack installs:

- `task-spec.md` for approved task documents in `docs/tasks/`, including the implementation plan, relevant ADR references, and classified task breakdown.
- `task-contract.json` for the machine-readable task graph, acceptance criteria, dependencies, worktree state, risk, and review policy.
- `workflow-state.json` for phase, status, active subtask, review-cycle, blocker, and transition evidence.
- `handoff.md`, `agent-result.md`, and `review-finding.md` for durable delegation, result, and review contracts.
- `local-progress.md` for ignored progress state and agent handoffs in `.local/tasks/`.
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
