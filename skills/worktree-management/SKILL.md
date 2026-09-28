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
unless the target repository has an explicit branch-naming convention. Only a
later explicit user request to implement the created plan authorizes creating
this isolated branch and merging cleanly reviewed task branches into it; it
does not authorize delivery to the target branch.

## Plan Assignments

Record a unique `planned_worktree` and `planned_branch` in every `TASK.md`.
The worktree path must be `worktrees/<plan-id>/<task-id>`. Use
`task/<plan-id>/<task-id>` for the branch unless the target repository has an
explicit branch-naming convention.

Planning a path does not create it. Approval to write plan files does not
authorize worktree or branch creation. Wait for a later user message explicitly
requesting implementation of the created plan or approved follow-up task.

## Create the Initial Plan Integration Worktree

1. Confirm that the plan files exist and the user has since explicitly requested
   implementation. Read the plan and target repository instructions.
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

## Restore a Plan Integration Worktree for a Follow-up Task

After the user approves the correction task files and later explicitly
requests implementation, inspect the existing plan's recorded integration
path, branch, and full head against Git. If the registered checkout still
exists, verify that it is clean and matches progress. If it was removed and
the branch still points to the recorded head, is not checked out elsewhere,
and the path is free, run `git worktree add <path> <existing-branch>` without
`-b`. Verify the restored checkout and refresh plan progress. Stop on any
path, branch, head, or worktree registration discrepancy; do not reset or
recreate the branch from the original plan baseline.

## Create an Actionable Task Worktree

1. Read the plan, task definition, task progress, and target repository
   instructions.
2. Confirm every dependency is integrated and completed, and resolve the
   current plan integration head as the base ref.
3. Confirm the plan's `worktrees/<plan-id>/` grouping folder contains the
   verified plan integration worktree, restoring it first when authorized and
   necessary. Resolve the planned task path relative to the managed project
   and confirm that task path does not exist.
4. Confirm the planned branch does not exist locally or in another worktree.
5. Run a non-interactive `git worktree add -b <branch> <path> <base-ref>` from
   the repository checkout.
6. Verify the new worktree's branch and full `HEAD` commit.
7. Record the actual `worktree`, `branch`, `head_commit`, and
   `uncommitted_changes` in task `PROGRESS.md`.

If the path or branch exists, or the correct base is uncertain, stop and ask
the user. Do not reuse, reset, delete, or overwrite it.
For a new correction task, create its own branch and worktree from the current
integration head; do not assign a completed task's checkout or branch to it.

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
authorizes them. Do not move merged worktrees into another folder or clean them
up automatically when a task or plan completes.

For an authorized task worktree removal:

1. Confirm the task is `completed`, its reviewed head and `integrated_commit`
   are recorded, and the task result is preserved on the plan integration
   branch or a verified delivery branch.
2. Confirm the exact registered worktree path, branch, and head with Git.
   Inspect tracked, untracked, and ignored files and preserve anything needed.
3. Run `git worktree remove <path>` only for a clean checkout, without
   `--force`. Stop if Git refuses; do not delete the directory manually.
4. Record the cleanup time, path, branch, and final head in task progress.
   Keep the recorded worktree assignment and commits as history.

Branch deletion must be covered by the cleanup authorization. Verify that its
tip still matches the recorded reviewed head and is preserved in the intended
destination. A task branch may remain after its worktree is removed. Use Git's
safe branch deletion only when its merged history is confirmed; do not
force-delete a branch after a failed check. Record branch cleanup in progress.

Keep the plan integration worktree until the final review and authorized
delivery to `delivery_branch` are complete and verified. Apply the same
clean-checkout and authorization checks to its removal and the branch checks
to any branch deletion. Record any cleanup in plan progress. Never remove the
initial repository checkout.
