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
  Codex can run this same role in an explicitly selected dedicated thread;
  Claude Code retains subagent execution in the pilot.
- `reviewer` performs read-only task and final plan integration reviews and
  returns review and handoff payloads for the orchestrator to persist.

## Model Defaults

Codex native subagents use these defaults:

| Role | Model | Reasoning effort |
| --- | --- | --- |
| `orchestrator` | Inherit the user's session selection | Inherit |
| `explorer` | `gpt-6-luna` | `max` |
| `database-explorer` | `gpt-6.1-sol` | `high` |
| `implementer` | `gpt-6.1-sol` | `high` |
| `reviewer` | `gpt-6.1-sol` | `xhigh` |

For complex implementation tasks, select `xhigh` in the implementer's native
configuration or the dedicated thread's actual client settings.

Luna is the default for bounded evidence gathering. Its effort setting does
not establish that it is sufficient for every repository investigation. For
ambiguous architecture, complex root causes, or conflicting evidence, use a
user-selected stronger explorer configuration, such as Sol at `xhigh`, and
verify the findings before using them in a plan.

Choose models available to the target workspace. To override a native role,
edit its installed `.codex/agents/<role>.toml`; explicit model and effort
values there take precedence over inherited settings. Local edits are subject
to the updater's normal conflict handling. Claude's explorer uses Sonnet at
medium effort; its other roles inherit the user's session model.

A dedicated implementation thread does not load these native configuration
values automatically. Select its model through the thread creation control
when the user authorizes that selection, and verify its actual client
reasoning setting. The current creation control has no reasoning-effort
argument; reading an agent file or mentioning an effort in a prompt does not
apply it.
