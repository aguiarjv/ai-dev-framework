# AI Dev Framework

A reusable framework for installing AI development guidance, portable agents, skills, and lightweight harness tooling into multiple projects.

## Quick Start

Validate the framework:

```bash
framework/harness/validate.sh
```

Install the core pack into another project:

```bash
framework/harness/install.sh --target /path/to/project --pack core
```

Preview an install without writing files:

```bash
framework/harness/install.sh --target /path/to/project --pack core --dry-run
```

If an existing target file differs, the installer stops. Re-run with `--force` only when you intentionally want to replace the target project's installed framework files.

## What Core Installs

- `.ai/*` as the portable source of truth.
- `AGENTS.md` generated from `.ai/guides/base.md` for Codex-style project guidance.
- `CLAUDE.md` generated as a Claude Code adapter that imports `.ai/guides/base.md`.
- `.ai/guides/frontend.md` and `.ai/guides/backend.md` supplemental task guides.
- `.codex/agents/*.toml` generated from `.ai/agents/*.md`.
- `.claude/agents/*.md` generated from `.ai/agents/*.md`.
- `.agents/skills/*` generated from `.ai/skills/*` for Codex skill discovery.
- A portable `playwright-visual-review` skill for browser visual QA workflows when projects register their own Playwright harnesses.
- `.ai/templates/*` task, progress, and ADR templates.
- `.ai/harnesses/registry.md` and `.ai/harnesses/scripts/` for reusable validation harnesses.
- `docs/tasks/` and `docs/adr/` working directories.
- `.local/tasks/` for ignored task progress.
- `harness/` as an empty project-owned folder for validation scripts or wrappers.
- `.ai-dev-framework.json` install manifest with pack, timestamp, and copied file list.

The core guide makes the main chat behave as an orchestrator by default. For new implementation work, the orchestrator clarifies intent, uses `explorer` when repository context is unclear or non-trivial, and creates `docs/tasks/<task-slug>.md` with the implementation plan, acceptance criteria, relevant ADR references, and classified tasks or subtasks. It waits for explicit approval before code changes begin. Progress, exploration findings, ADR summaries, and handoffs live in `.local/tasks/<task-slug>/progress.md`, and durable decisions go in `docs/adr/`. Broad ADR discovery belongs to `explorer`; downstream agents use the handed-off ADR summaries or named ADR paths instead of scanning every ADR.

Reviewer, debugger, and implementer agents read `.ai/harnesses/registry.md` before choosing validation commands. Use the `create-harness` skill to add repeatable validation scripts and registry entries. Use `playwright-visual-review` when a project has or needs a registered browser visual QA harness. The top-level `harness/` folder is available for project-owned validation scripts or wrappers.

Tool-specific files are generated adapters. They include source provenance comments and should be regenerated from `.ai/` instead of edited directly. Some adapters expand `.ai` content instead of referencing it because Codex and Claude load agents and skills through different native formats.

See [docs/installing-in-projects.md](docs/installing-in-projects.md) and [docs/authoring.md](docs/authoring.md).
