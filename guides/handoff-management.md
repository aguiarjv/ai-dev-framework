# Handoff Management

Use handoff documents to transfer the minimum durable context required for one
agent to continue work performed by another. A handoff is a point-in-time
transition record; `PROGRESS.md` remains the source of truth for current task
and plan state.

## Structure

Store planning and exploration handoffs at plan level and execution handoffs
with their task:

```text
plans/
  <plan-name>/
    handoffs/
      001-<from-role>-to-<to-role>.md
    tasks/
      <task-id>/
        handoffs/
          001-<from-role>-to-<to-role>.md
```

Use a three-digit sequence local to each `handoffs/` directory. Append a new
file for every transition; never replace an earlier handoff. Keep the handoff
identifier equal to its filename without `.md`.

Plan-level handoffs capture exploration or coordination that applies to the
whole plan. Task-level handoffs capture implementation checkpoints, review
results, correction requests, and task completion.

## Required Contents

Start from `.agents/skills/handoff-management/assets/HANDOFF.md`. Record:

- The plan and optional task receiving the handoff.
- The sender role, recipient role, creation time, and outcome.
- The applicable worktree, branch, and full head commit.
- The purpose and scope of the completed assignment.
- Work completed and files changed or inspected.
- Validation performed and its results.
- Decisions already settled during the assignment.
- Findings, blockers, or unresolved uncertainty.
- One exact next action and the minimal context required to perform it.

Use repository-relative paths for files inside a checkout. Use paths relative
to the managed project for plans, tasks, reviews, reports, and project
documentation.

Do not copy raw logs or broad file dumps into a handoff. Link to durable
artifacts and summarize only the evidence that changes the next agent's work.

## Ownership

An implementation agent writes its own task-local handoff and updates its own
task-level `PROGRESS.md` before returning.

Explorers and reviewers remain sandboxed read-only. They return a complete
handoff payload to the orchestrator. The orchestrator writes that payload to
the appropriate handoff path and may normalize only identifiers, timestamps,
and links required by the template. It must not weaken or reinterpret findings.

The orchestrator writes plan-level handoffs and is the only writer of the
plan-level `PROGRESS.md`.

## Outcomes

Use one of these handoff outcomes:

- `completed`: The assignment finished and its result can be consumed.
- `checkpoint`: Work is valid but intentionally stops at an agreed boundary.
- `changes-requested`: Review findings require another implementation pass.
- `blocked`: Work cannot continue until a recorded blocker is resolved.

## Consumption

Before assigning follow-up work, the orchestrator verifies that the handoff
matches the current task, worktree, branch, and head commit. A receiving agent
reads the task definition, task progress, latest handoff, and any review named
by the handoff. It should not need the sender's chat transcript.

Set `latest_handoff` in the applicable `PROGRESS.md` to the new handoff path.
Do not point it at a missing file or an older handoff when a newer transition
has been accepted.
