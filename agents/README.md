# Agents

This directory contains reusable native agent definitions that the framework
installs into target projects.

- `codex/` contains TOML definitions copied to `.codex/agents/`.
- `claude/` contains Markdown definitions with YAML frontmatter copied to
  `.claude/agents/`.

The two native definitions for a role may use platform-specific configuration,
but they must keep matching names, descriptions, responsibilities, handoff
contracts, and outcomes. The installer validates that behavioral contract
before writing a target. Do not add rules that apply to only one target project.

## Available Agents

- `orchestrator` coordinates plan-driven work and agent handoffs.
- `explorer` performs read-only repository exploration and returns
  repository, project-documentation, and workspace-guide evidence for plans and
  tasks.
- `database-explorer` performs bounded read-only exploration of a live
  database and returns a structured handoff.
- `implementer` implements one approved task or correction pass in an
  assigned worktree and writes a task-local handoff.
- `reviewer` performs read-only task and final plan integration reviews and
  returns review and handoff payloads for the orchestrator to persist.
