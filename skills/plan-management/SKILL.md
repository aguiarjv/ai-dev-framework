---
name: plan-management
description: Create, resume, update, and complete structured plans and tasks in an AI Dev Framework managed project. Use when work must be planned, tracked across agent handoffs, or archived after completion.
---

# Plan Management

Use this skill for a managed project's `workspace-plans/` directory. The
[Plan and Task Management guide](../../guides/plan-and-task-management.md) is
the canonical lifecycle and schema reference; read its relevant sections for
the operation at hand. Do not load unrelated workspace guides merely because
they appear in the workspace's routing index.

## Route the Work

- New plan: read the guide's Clarify Before Creating, Project Exploration, and
  Creating a Plan sections. Resolve user decisions and one repository baseline,
  then obtain confirmation before writing plan files. Use read-only explorers
  when the delegated workflow requires them; if they are unavailable, ask the
  user how to proceed.
- Resume or update: read Statuses and Managing Progress. Read the plan
  definition and progress, then only the task files relevant to current or next
  actions. Verify recorded worktree, branch, and head against Git before
  changing state.
- Review and integration: read Reviewing a Task and use the review-management
  and worktree-management skills for their respective operations. Reviewers
  stay read-only. The orchestrator alone writes plan-level `PROGRESS.md` and
  serializes task integrations into the dedicated plan integration worktree,
  including for single-task plans.
- Reopen or complete: read Statuses and Completing a Plan. Completed work is
  terminal unless the user explicitly reopens it. Completion does not grant
  authority to deliver, push, or clean up branches or worktrees.

Do not invent requirements, acceptance evidence, dependencies, or missing user
decisions. Keep task progress and plan summaries synchronized; use immutable
handoffs as transition records. Preserve the required metadata and headings
when editing definitions or progress. Run `scripts/validate_plan.py
<path-to-plan>` after structural or state changes and before archiving.

## Templates and Helpers

Use the canonical templates without dropping required fields:

- `assets/plan/PLAN.md` and `assets/plan/PROGRESS.md`.
- `assets/task/TASK.md` and `assets/task/PROGRESS.md`.

The guide defines field semantics, status transitions, path tables, review
gates, and archival rules. The scripts here implement bounded operations; they
do not replace the orchestrator's judgment about acceptance or authorization.

### Cold resume

At plan approval or after a task integration, offer a context reset only when
all agents have finished and approval, task statuses, integration branch/head,
latest artifacts, and exact next actions are durable. The user may run
`/clear` in Claude Code. Never reset during a review, merge, or handoff, and
do not claim to have cleared the context yourself.

In a fresh session, use the [cold-resume checklist](references/cold-resume.md):
read plan `PLAN.md` and `PROGRESS.md`, inspect only the task definitions and
progress needed for current/next actions, verify Git state and latest
artifacts, and run the plan validator before continuing.

### Resource measurement

Native Codex root turns and subagents are observed by the installed hook only
after the user trusts it in `/hooks` and starts a new session. It writes
`.agents/metrics/codex-native.jsonl`. Summarize it with
`python3 .agents/skills/plan-management/scripts/native_metrics.py --summarize`.
Usage from unrecognized local transcript records is unknown; a workspace-root
cwd may not identify a task. Do not sum overlapping root/subagent elapsed time
as end-to-end wall time.

For a separately launched Codex CLI phase, `scripts/measure_task.py run`
records command elapsed time and reported `codex exec --json` usage in the
plan's or task's `METRICS.jsonl`. Run `scripts/measure_task.py summarize
--target-dir <plan-or-task-folder>` for totals. Do not double-count a run seen
by both native and CLI measurement, infer missing tokens as zero, or launch an
agent solely to measure a phase.

For offline Claude Code JSONL analysis, run
`python3 .agents/skills/plan-management/scripts/claude_usage.py
<transcript-directory>`. It reports numeric usage by main/subagent and model,
separates uncached input, cache creation, cache reads, and output, and counts
requests above 200k input context. It does not retain prompt text or reliably
establish role, phase, fork status, cost, or active elapsed time. Session span
includes idle time. Compare a fixed sample before/after changes with review
quality, retries, and outcomes; lower token totals alone do not prove success.
Keep raw metrics files out of ordinary agent context.

### Validated review-to-integration transition

After independently checking a clean final review and each acceptance
criterion, use `scripts/plan_state.py` for `ready-for-review` to
`ready-for-integration`. It updates the task checkboxes (only with
`--accept-all`), task progress, and plan progress, and validates the staged
result before writing:

```text
python3 .agents/skills/plan-management/scripts/plan_state.py \
  projects/<project-name>/workspace-plans/<plan-id> transition <task-id> \
  ready-for-integration \
  --review workspace-reviews/<plan-id>/<review-file>.md \
  --handoff workspace-plans/<plan-id>/tasks/<task-id>/handoffs/<handoff-file>.md \
  --accept-all --dry-run
```

Remove `--dry-run` to apply. The script is idempotent for the same artifacts
and refuses inconsistent starting state, missing artifacts, or a mismatched
review. `--accept-all` is an explicit affirmation, never an inference from the
review result. Other transitions remain manual until separately automated and
tested.
