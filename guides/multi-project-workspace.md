# Multi-Project Workspace Structure

Use this structure for a meta repository that manages multiple projects:

```text
AGENTS.md
CLAUDE.md
.ai-dev-framework.json
.codex/
  agents/
.claude/
  agents/
  skills/
.agents/
  guides/
  skills/
projects/
  README.md
  <project-name>/
    AGENTS.md
    CLAUDE.md
    README.md
    docs/
      adrs/
    plans/
      done/
    scripts/
    worktrees/
      <default-branch-name>/
    reviews/
    reports/
```

## Meta Repository

- `AGENTS.md` contains the shared instructions for agents operating across the
  meta repository. `CLAUDE.md` imports it for Claude Code.
- `.ai-dev-framework.json` records the installed version, source state, managed
  paths, and content hashes.
- `.codex/agents/` contains project-scoped Codex custom agents used in the meta
  repository.
- `.claude/agents/` and `.claude/skills/` contain Claude Code's native agent
  definitions and generated skill copies.
- `.agents/guides/` and `.agents/skills/` contain the installed guides and
  Codex-discoverable skill copies used in the meta repository.
- `projects/` contains the managed project workspaces.
- `projects/README.md` explains the purpose of the projects directory.

## Managed Projects

Each folder under `projects/` represents one managed project:

- `AGENTS.md` contains instructions specific to the managed project;
  `CLAUDE.md` imports those instructions for Claude Code.
- `README.md` provides an overview of the managed project workspace.
- `docs/` contains project documentation. Architecture decision records live
  under `docs/adrs/`; other documentation subfolders are created when needed.
- `plans/` contains plans for features and bug fixes, including related tasks.
  Completed plan folders are stored under `plans/done/`.
- `scripts/` contains helper automation for the managed project workspace.
  Scripts that are part of the project's source code remain in its repository
  checkout.
- `worktrees/` contains Git checkouts and worktrees. The initial repository
  checkout is stored under `worktrees/<default-branch-name>/`.
- `reviews/` contains evidence-backed review results.
- `reports/` contains optional project reports requested by the user or a plan.
