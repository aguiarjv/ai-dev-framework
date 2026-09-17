# Worktree Management

Use one plan integration worktree and a separate Git worktree and branch for
every implementation task. The orchestrator owns the integration checkout and
task worktree creation and assignment; implementation agents work only in the
checkout recorded for their task.

## Planning and Naming

During planning, record these intended values in each `TASK.md`:

- `planned_worktree`: `worktrees/<plan-id>/<task-id>`
- `planned_branch`: `task/<plan-id>/<task-id>`

Both paths are relative to the managed project or repository conventions shown
above. If either name conflicts with an existing worktree or branch, stop and
ask the user before selecting a different name or reusing the existing object.

Record these values in `PLAN.md`:

- `planned_integration_worktree`: `worktrees/<plan-id>/plan-integration`
- `planned_integration_branch`: `plan/<plan-id>`
- `delivery_branch`: The eventual destination for the combined result.

The folder `worktrees/<plan-id>/` groups the plan integration worktree and all
of that plan's task worktrees. The initial repository checkout stays at its
existing path. The plan integration branch represents the complete plan. The
delivery branch is metadata only; recording it does not authorize a merge or
push.

## Creation Timing

Do not create integration or task worktrees before the user approves the plan.
After approval, create `worktrees/<plan-id>/`, then create the plan integration
worktree inside it from the recorded baseline commit. Record its actual
worktree, branch, head commit, and uncommitted-change state in plan progress.

Create worktrees for immediately actionable tasks from the current plan
integration head. Create a dependent task's worktree only after its
dependencies are integrated and complete, which guarantees that the current
plan head includes their results.

Before creating a worktree, verify:

- The recorded source checkout, branch, and baseline still exist.
- The task dependencies are complete.
- The base ref is the recorded current plan integration head and contains the
  dependency results needed by the task.
- The planned worktree path and branch do not already exist.
- The target repository's instructions do not require another branch or
  integration policy.

Use the worktree-management skill for the Git operation. After creation, record
the actual worktree, branch, head commit, and uncommitted-change state in the
task-level `PROGRESS.md`.

## Isolation

Never assign two active tasks to the same worktree or branch. Do not let an
implementation agent edit the source checkout, another task's worktree, plan
metadata outside its task, the plan integration worktree, or another managed
project.

The orchestrator serializes all changes to the plan integration worktree. Do
not run two task integrations concurrently.

Read-only reviewers inspect the exact assigned worktree and head commit. If the
worktree changes during review, discard or qualify the stale result and review
the new state.

## Task Integration

A clean final task review moves the task to `ready-for-integration`; it does
not complete the task. Before integrating it, confirm:

- The task branch and head still match the clean review and task progress.
- The task worktree has no uncommitted changes.
- The integration worktree and head still match plan progress and have no
  uncommitted changes.

From the integration worktree, prepare the merge without committing it using
the target repository's explicit transactional merge policy. When none is
specified, use `git merge --no-ff --no-commit <task-branch>` so validation can
run before the plan branch advances.

If the merge conflicts, abort it and verify that the integration branch is
unchanged and clean. Record a task-local correction handoff with the conflict
evidence and current integration head, return the task to `in-progress`, and
assign a fresh implementer. That implementer may bring the current integration
head into the task branch to reconcile the conflict. Use the same correction
flow if validation of the pending combined tree fails, and abort the merge so
the plan branch remains unchanged. Uncheck any task criterion invalidated by
the failure. The corrected task must pass validation and final review again
before another integration attempt.

After the pending combined tree passes the task's required validation, commit
the merge without opening an editor. Record the resulting plan-branch commit as
`integrated_commit` in task progress, refresh the plan integration state, clear
any stale plan-level `latest_review`, and only then complete the task.
Downstream task worktrees are based on this refreshed head.

## Delivery and Cleanup

Approval of the plan authorizes creation of its recorded worktrees and merges
from cleanly reviewed task branches into its integration branch. It does not
authorize merging or rebasing the plan branch into `delivery_branch`, pushing,
deleting branches, or removing worktrees.

Remove a task worktree or branch only when the user explicitly requests it or
an applicable project rule already authorizes cleanup. Resolve the exact path
and confirm that required work is preserved before any removal.
