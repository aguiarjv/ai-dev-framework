# AI Dev Framework

This repository contains reusable AI guidance, agents, skills, harnesses, and installer tooling for applying a consistent development workflow across projects.

## Source Of Truth

- Treat `.ai/` as the authored source of truth.
- Treat generated target-project files such as `.codex/`, `.claude/`, `AGENTS.md`, and `CLAUDE.md` as adapters generated from `.ai/`.
- Do not edit generated adapters as framework sources.
- Keep reusable framework behavior broad and project-agnostic.

## Working Rules

- Prefer small, composable agents and skills over large catch-all workflows.
- Keep agent prompts role-focused and standalone.
- Keep skill instructions concise and validate skills after edits.
- Preserve user changes and unrelated work.
- Use `framework/harness/validate.sh` after framework changes.
- When changing installer behavior, test both dry-run and real installs into `/tmp`.

## Portable Guides

Read these guides when relevant:

@.ai/guides/base.md
@.ai/guides/frontend.md
@.ai/guides/backend.md

## File Roles

- `.ai/guides/` contains portable guidance.
- `.ai/agents/` contains portable agent prompts.
- `.ai/skills/` contains reusable skill sources.
- `.ai/harnesses/` contains validation harness registry and scripts.
- `.ai/templates/` contains reusable workflow templates.
- `framework/packs/` declares installable bundles.
- `framework/harness/` contains install and validation tools.
- `docs/` contains human-facing framework documentation.
