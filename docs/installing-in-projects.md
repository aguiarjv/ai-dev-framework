# Installing In Projects

Install a pack from this framework into a target project:

```bash
/path/to/ai-dev-framework/framework/harness/install.sh --target /path/to/project --pack core
```

Use `--dry-run` to preview all copied files. Use `--force` only when replacing existing differing files is intentional.

The core pack writes:

- `.ai/guides/*`
- `.ai/agents/*`
- `.ai/templates/*`
- `.ai/harnesses/registry.md`
- `.ai/harnesses/scripts/`
- `.ai/skills/*`
- `AGENTS.md`
- `CLAUDE.md`
- `.codex/agents/*.toml`
- `.agents/skills/*`
- `.claude/agents/*.md`
- `docs/tasks/`
- `docs/adr/`
- `.local/tasks/`
- `harness/`
- `.gitignore` entry for `.local/`
- `.ai-dev-framework.json`

The manifest records the installed pack, version, timestamp, and written file list. Re-running the installer is idempotent when files are unchanged.

## Updating A Project

Re-run the installer after framework changes. If the target project customized an installed file, the installer will stop unless `--force` is provided. Resolve those differences deliberately.

Edit `.ai` files in the framework, not generated adapter files. The installer renders Codex and Claude Code formats from the same portable source.

Generated adapters include a source marker such as `Generated from .ai/...`. Some adapters are expanded copies rather than reference-only files because Codex and Claude use different discovery formats for agents and skills.

## Task Workflow

For new implementation tasks, the orchestrator creates `docs/tasks/<task-slug>.md` from `.ai/templates/task-spec.md` and waits for explicit approval before implementation. For non-trivial or unclear tasks, it first calls `explorer` to map relevant code, tests, configs, commands, conventions, risks, and relevant ADRs. The task spec must include repository context, relevant ADR references, acceptance criteria, a concise implementation plan, and classified tasks or subtasks before approval. Current progress, exploration findings, ADR summaries, and agent handoffs live under `.local/tasks/<task-slug>/progress.md`, which is ignored by git. Durable decisions and relevant implementation context belong in `docs/adr/`. Broad ADR discovery belongs to `explorer`; downstream agents use handed-off summaries or named ADR paths instead of scanning every ADR.

## Harness Workflow

The installed framework includes `.ai/harnesses/registry.md`. Reviewer, implementer, and test-debugger agents read that registry before choosing validation commands. Use the `create-harness` skill to create `.ai/harnesses/scripts/<harness-slug>.sh`, validate it, and add or update the registry entry. The top-level `harness/` folder is empty by default and can hold project-owned validation scripts or wrappers.
