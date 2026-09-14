# AI Dev Framework

AI Dev Framework installs reusable AI development guidance into multi-project
workspaces for Codex and Claude Code.

It provides native custom agents for each platform, shared guides, and portable
Agent Skills generated into both platforms' discovery locations.

## Install

The installer requires Python 3.11 or newer and otherwise uses only the Python
standard library.

Run the installer from any directory and point it at the meta-repository to
create or extend:

```bash
./installer/install.sh --target /path/to/ai-workspace
```

Preview the full operation without writing files:

```bash
./installer/install.sh --target /path/to/ai-workspace --dry-run
```

The installer is idempotent when generated files are unchanged. It preflights
the whole target and refuses to write anything when an existing destination
differs. Version 1 intentionally has no force or update mode.

## Goals

- Keep reusable AI development files in one source repository.
- Install those files into target projects consistently.
- Support meta repositories that coordinate one or more managed projects.
- Keep each step of the framework easy to review and change.

## Meta-Repository Layout

The installer writes the generated AI development files into a chosen folder
that acts as a meta repository for one or more managed projects.

Target layout:

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
    worktrees/
      <default-branch-name>/
    reviews/
    reports/
```

The initial checkout for a managed project lives under
`projects/<project-name>/worktrees/<default-branch-name>/`. The other folders
store workspace metadata outside the Git checkout. They do not receive
per-folder README files.

## Workflow

Launch Codex or Claude Code from the installed meta-repository root so it
discovers the workspace-level agents, skills, and instructions. Use the
`project-setup` skill to clone or initialize managed projects after the base
workspace has been installed.

## Repository Layout

```text
agents/     Native Codex and Claude Code agent definitions.
guides/     Guide files installed into target `.agents/guides/`.
skills/     Portable skill sources rendered for both platforms.
installer/  Installer code and generated-file templates.
.agents/    Local Codex helpers for working on this framework.
```

## Compatibility Notes

`CLAUDE.md` imports `AGENTS.md`, keeping workspace behavior in one shared
instruction source. Claude's read-only agents use plan mode and deny its
built-in editing and delegation tools. Claude Code can still inherit a more
permissive parent session mode, so start sensitive work with an appropriately
restricted parent permission mode and independently read-only database access.
