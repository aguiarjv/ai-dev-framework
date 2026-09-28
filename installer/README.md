# Installer

This directory contains the scripts used to install this framework into a
target directory for Codex and Claude Code.

The target directory becomes a meta repository containing one or more managed
projects.

## Target Layout

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
    workspace-docs/
      adrs/
    workspace-plans/
      done/
    workspace-scripts/
    worktrees/
      <default-branch-name>/
    workspace-reviews/
    workspace-reports/
```

## Usage

Python 3.11 or newer is required; the installer has no third-party Python
dependencies.

```bash
./installer/install.sh --target /path/to/ai-workspace
```

Use `--dry-run` to preview the result. The target may be missing or may already
contain unrelated files. All destinations are checked before writing; a
differing file, symlink, invalid manifest, or non-directory path component
aborts the install without overwriting anything.

For an existing installation, preview the workspace naming migration with
`python3 installer/migrate.py --target /path/to/ai-workspace`. Add `--apply`
after reviewing its moves, file updates, and references marked `REVIEW`.
The migration verifies installed files against the existing manifest, stops
on folder collisions, and keeps the `worktrees/` checkouts untouched. `REVIEW`
lines identify references the tool cannot safely classify; they may refer to
files inside a checkout. Rerunning `--apply` after an interruption restores
the previous state before retrying.

The installer copies native agent definitions to `.codex/agents/` and
`.claude/agents/`, guides to `.agents/guides/`, and generated copies of each
portable skill to `.agents/skills/` and `.claude/skills/`. `CLAUDE.md` imports
the generated `AGENTS.md`, and `.ai-dev-framework.json` records the version,
source revision, dirty state, installation time, managed paths, and hashes.

The initial Git checkout for each managed project lives at
`projects/<project-name>/worktrees/<default-branch-name>/`. The installer does
not create README files inside `workspace-docs/`, `workspace-plans/`,
`workspace-scripts/`, `worktrees/`, `workspace-reviews/`, or
`workspace-reports/`.

Run Codex or Claude Code from the meta-repository root. The base installer does
not initialize Git or create a managed project; use the installed
`project-setup` skill for that next step.

## Manual Compatibility Check

- In Codex, start a session at the target root, use `/skills`, and ask it to
  identify the installed custom agents.
- In Claude Code, start at the target root and check `/context`, `/skills`, and
  `/agents` for the generated instructions, skills, and agents.
