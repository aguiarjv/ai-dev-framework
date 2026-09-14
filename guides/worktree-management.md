# Worktree Management

Use a separate Git worktree and branch for every implementation task. The
orchestrator owns task worktree creation and assignment; implementation agents
work only in the checkout recorded for their task.

## Planning and Naming

During planning, record these intended values in each `TASK.md`:

- `planned_worktree`: `worktrees/<plan-id>-<task-id>`
- `planned_branch`: `task/<plan-id>/<task-id>`

Both paths are relative to the managed project or repository conventions shown
above. If either name conflicts with an existing worktree or branch, stop and
ask the user before selecting a different name or reusing the existing object.

## Creation Timing

Do not create task worktrees before the user approves the plan. After approval,
create worktrees for immediately actionable tasks. Create a dependent task's
worktree only after its dependencies are complete and its selected base includes
their required changes.

Before creating a worktree, verify:

- The recorded source checkout, branch, and baseline still exist.
- The task dependencies are complete.
- The base ref contains the dependency results needed by the task.
- The planned worktree path and branch do not already exist.
- The target repository's instructions do not require another branch or
  integration policy.

Use the worktree-management skill for the Git operation. After creation, record
the actual worktree, branch, head commit, and uncommitted-change state in the
task-level `PROGRESS.md`.

## Isolation

Never assign two active tasks to the same worktree or branch. Do not let an
implementation agent edit the source checkout, another task's worktree, plan
metadata outside its task, or another managed project.

Read-only reviewers inspect the exact assigned worktree and head commit. If the
worktree changes during review, discard or qualify the stale result and review
the new state.

## Integration and Cleanup

Follow the target repository's explicit integration policy. Worktree creation
does not authorize merging, rebasing, pushing, deleting branches, or removing
worktrees.

Remove a task worktree or branch only when the user explicitly requests it or
an applicable project rule already authorizes cleanup. Resolve the exact path
and confirm that required work is preserved before any removal.
