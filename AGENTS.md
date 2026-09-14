# AI Dev Framework

This repository is a framework for AI-driven development. It stores reusable
agents, guides, and skills that can be installed into other projects.

## Working Rules

- Build this project in small, reviewable steps.
- Ask the user when information is missing or a decision affects project shape.
- Do not make product, structure, or behavior guesses when the user has not
  decided them yet.
- Keep framework content reusable across projects.
- Do not add target-project-specific rules to reusable framework files.

## Repository Roles

- `agents/codex/` contains native Codex custom-agent TOML files installed into
  `.codex/agents/` in target projects.
- `agents/claude/` contains native Claude Code subagent Markdown files installed
  into `.claude/agents/` in target projects.
- `guides/` contains guide files this framework can install into target projects.
- `skills/` contains portable Agent Skills sources installed into both
  `.agents/skills/` and `.claude/skills/` in target projects.
- `.agents/` contains local Codex agents or skills used to work on this framework.

## Installation Model

The installer will be run from this repository and pointed at a target
directory. That target directory becomes a meta repository containing one or
more managed projects.

Guides do not have a separate discovery standard in this project. Install one
shared copy inside `.agents/guides/` and reference it from workspace
instructions, agents, or skills that use it.

The chosen target folder should receive:

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
```

Each managed project under `projects/<project-name>/` uses this structure:

```text
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

The initial repository checkout belongs in
`worktrees/<default-branch-name>/`. Do not create README files inside the
metadata folders `docs/`, `plans/`, `worktrees/`, `reviews/`, or `reports/`.

Implement installer behavior only in small steps approved by the user.
