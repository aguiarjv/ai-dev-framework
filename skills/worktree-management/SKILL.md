---
name: worktree-management
description: Create and manage plan integration and task worktrees, integrate reviewed task branches, and preserve delivery and cleanup authorization boundaries.
---

# Worktree Management

Follow the [Worktree Management guide](../../guides/worktree-management.md).
Use this skill only for integration and task worktrees recorded in an approved
plan.

## Plan Integration Assignment

Record `planned_integration_worktree`, `planned_integration_branch`, and
`delivery_branch` in `PLAN.md`. The integration worktree path must be
`worktrees/<plan-id>/plan-integration`. Use `plan/<plan-id>` for the branch
unless the target repository has an explicit branch-naming convention. Plan
approval authorizes creating this isolated branch and merging cleanly reviewed
task branches into it; it does not authorize delivery to the target branch.

## Plan Assignments

Record a unique `planned_worktree` and `planned_branch` in every `TASK.md`.
The worktree path must be `worktrees/<plan-id>/<task-id>`. Use
`task/<plan-id>/<task-id>` for the branch unless the target repository has an
explicit branch-naming convention.

Planning a path does not create it. Do not run worktree or branch creation
before the user approves the plan.

## Create the Plan Integration Worktree

1. Read the approved plan and target repository instructions.
2. Confirm the plan's `worktrees/<plan-id>/` grouping folder, planned worktree
   path, and branch do not exist and the recorded baseline commit is still
   available.
3. Create the `worktrees/<plan-id>/` grouping folder, then run this
   non-interactive command from the source checkout:

   ```text
   git worktree add -b <integration-branch> <integration-path> <baseline-commit>
   ```
4. Verify the new worktree's branch and full `HEAD` commit.
5. Record the actual integration worktree, branch, head commit, and
   uncommitted-change state in plan progress.

If the path or branch exists, stop and ask the user. Do not reuse, reset,
delete, or overwrite it.

## Create an Actionable Task Worktree

1. Read the plan, task definition, task progress, and target repository
   instructions.
2. Confirm every dependency is integrated and completed, and resolve the
   current plan integration head as the base ref.
3. Confirm the plan's `worktrees/<plan-id>/` grouping folder contains the
   recorded plan integration worktree, then resolve the planned task path
   relative to the managed project and confirm that task path does not exist.
4. Confirm the planned branch does not exist locally or in another worktree.
5. Run a non-interactive `git worktree add -b <branch> <path> <base-ref>` from
   the repository checkout.
6. Verify the new worktree's branch and full `HEAD` commit.
7. Record the actual `worktree`, `branch`, `head_commit`, and
   `uncommitted_changes` in task `PROGRESS.md`.

If the path or branch exists, or the correct base is uncertain, stop and ask
the user. Do not reuse, reset, delete, or overwrite it.

## Assignment Rules

- One active task owns one worktree and branch.
- The orchestrator alone owns the plan integration worktree and serializes
  merges into it.
- Parallel tasks never share either value.
- Implementers edit only their assigned worktree.
- Reviewers inspect the recorded worktree and exact head state.
- A dependent task worktree is created only after its dependencies complete.

## Integrate a Reviewed Task

1. Confirm the task is `ready-for-integration`, its final review is clean and
   matches its recorded head, and its worktree has no uncommitted changes.
2. Confirm the integration worktree has no uncommitted changes and still
   matches the head recorded in plan progress.
3. From the integration worktree, prepare the merge without committing it. Use
   the target repository's transactional merge policy, or
   `git merge --no-ff --no-commit <task-branch>` when none is specified.
4. If the merge conflicts, abort it. Keep the integration branch unchanged,
   return the task to `in-progress`, and create a correction handoff for a
   fresh implementer. Do not resolve conflicts directly in the integration
   worktree.
5. Run the task's validation against the pending combined tree. If validation
   fails, abort the merge, uncheck any task criterion the failure invalidates,
   and use the same correction flow; do not commit the failed integration.
6. Commit the validated merge without opening an editor. Record the resulting
   plan-branch commit as the task's `integrated_commit`, refresh plan
   integration progress, clear any stale plan-level `latest_review`, and
   complete the task.

Never integrate two task branches concurrently. A correction for an
integration conflict may bring the current plan integration head into the task
branch so the implementer can reconcile it; the corrected result must pass
validation and final review again.

## Delivery and Cleanup

Internal task-to-plan integration is authorized only as described above. This
skill does not authorize merging or rebasing the plan integration branch into
`delivery_branch`, pushing, branch deletion, or worktree removal. Perform those
operations only after explicit user instruction or an applicable project rule
authorizes them, and verify that required work is preserved first.
