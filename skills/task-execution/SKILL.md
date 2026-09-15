---
name: task-execution
description: Execute one approved plan task or review correction in its assigned worktree, validate it, update task progress, and hand it off for review.
---

# Task Execution

Use this skill inside an `implementer` agent. Follow the
[Orchestration Workflow](../../guides/orchestration-workflow.md),
[Plan and Task Management guide](../../guides/plan-and-task-management.md), and
[Handoff Management guide](../../guides/handoff-management.md).

## Start

1. Read the applicable workspace instruction files and the assigned `TASK.md`,
   `PROGRESS.md`, latest handoff, named review, documentation, and guides.
2. Confirm the task is `in-progress`, its dependencies are completed, and the
   recorded worktree and branch match the current checkout.
3. Confirm the assignment is either the approved task scope or an accepted set
   of review findings or integration-conflict corrections recorded by the
   orchestrator.

Stop and report a mismatch rather than editing a different checkout or task.

## Implement

- Change only what the task or accepted correction requires.
- Preserve unrelated user changes.
- Add or update tests and documentation required by the acceptance criteria.
- Do not decide unresolved product, scope, architecture, or integration
  questions. Return them to the orchestrator.
- Update task `PROGRESS.md` at meaningful checkpoints with work completed,
  decisions, changed files, validation, blockers, and one exact next action.
- Never edit plan-level `PROGRESS.md`.

## Checkpoint Review

At a high-risk checkpoint named in the task, keep status `in-progress`, run the
required checks, create a `checkpoint` handoff, and return its path. Do not
continue past the review boundary until the orchestrator reports a clean review.

## Ready for Final Review

When the implementation satisfies its requirements and focused validation:

1. Refresh `head_commit` and `uncommitted_changes` in task progress.
2. Set the task status to `ready-for-review`.
3. Set the next action to review the exact recorded head state.
4. Create a task-local `completed` handoff to the reviewer with the
   handoff-management skill.
5. Return a concise result and the handoff path to the orchestrator.

Do not mark the task `ready-for-integration` or `completed`. A clean final
review moves it to `ready-for-integration`; only successful integration into
the plan branch completes it.
