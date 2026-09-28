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
differs. The base installer has no force or update mode.

To preview migration of a previously installed workspace, run:

```bash
python3 installer/migrate.py --target /path/to/ai-workspace
```

After resolving any reported conflicts, add `--apply`. The migration updates
installed framework files, renames managed-project metadata folders, and
reports project-authored references that may need review.

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
  hooks.json
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

The initial checkout for a managed project lives under
`projects/<project-name>/worktrees/<default-branch-name>/`. The other folders
store workspace metadata outside the Git checkout. They do not receive
per-folder README files.

## Workflow

Launch Codex or Claude Code from the installed meta-repository root so it
discovers the workspace-level agents, skills, and instructions. Use the
`project-setup` skill to clone or initialize managed projects after the base
workspace has been installed.

For native Codex work, the installed `.codex/hooks.json` records root turns and
subagent starts/stops in `.agents/metrics/codex-native.jsonl`. Codex requires
the user to review and trust this project-local hook in `/hooks` before it runs;
start a new session after trusting it. The hook records timestamps, role, and
available numeric usage, never prompts or transcripts. Local transcript usage
is best-effort because its format is not stable; missing counts remain unknown.
Use `python3 .agents/skills/plan-management/scripts/native_metrics.py
--summarize` from the installed workspace to inspect the log. Native events
cannot always be attributed to one task when the session cwd is the workspace
root.

For separately launched Codex CLI work, `scripts/measure_task.py run` still
wraps `codex exec --json` and writes `METRICS.jsonl` beside the relevant plan
or task progress file. Claude Code runs are not covered by the Codex hook.

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
