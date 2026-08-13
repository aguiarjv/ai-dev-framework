# AI Dev Framework

This repository contains reusable AI guidance, custom agents, skills, and harness scripts for installing a consistent AI development workflow into other projects.

## Working Rules

- Treat `.ai/` as the source of truth. Do not edit generated target-project files as if they were framework sources.
- Treat `.codex/`, `.claude/`, `AGENTS.md`, and `CLAUDE.md` in target projects as adapters generated from `.ai/`.
- Keep guidance broadly reusable. Project-specific rules belong in the target project after installation, not in this framework.
- Prefer small, composable skills over one large workflow skill.
- Keep agent instructions role-focused and standalone.
- Validate framework changes with `framework/harness/validate.sh`.
- When changing installer behavior, also test with `framework/harness/install.sh --target /tmp/<project> --pack core --dry-run` and a real temporary install.

## File Roles

- `.ai/guides/` contains portable guidance.
- `.ai/agents/` contains portable agent prompts.
- `.ai/skills/` contains reusable skill sources.
- `framework/packs/` declares installable bundles.
- `framework/harness/` contains install and validation tools.
- `docs/` contains human-facing framework documentation.
