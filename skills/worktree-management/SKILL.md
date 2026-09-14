---
name: worktree-management
description: Plan, create, assign, inspect, and safely retire isolated Git worktrees for approved AI Dev Framework tasks.
---

# Worktree Management

Follow the [Worktree Management guide](../../guides/worktree-management.md).
Use this skill only for task worktrees recorded in an approved plan.

## Plan Assignments

Record a unique `planned_worktree` and `planned_branch` in every `TASK.md`.
Use `worktrees/<plan-id>-<task-id>` and `task/<plan-id>/<task-id>` unless the
target repository has an explicit naming convention.

Planning a path does not create it. Do not run worktree or branch creation
before the user approves the plan.

## Create an Actionable Task Worktree

1. Read the plan, task definition, task progress, and target repository
   instructions.
2. Confirm every dependency is completed and resolve a base ref containing the
   required dependency results.
3. Resolve the planned path relative to the managed project and confirm the
   path does not exist.
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
- Parallel tasks never share either value.
- Implementers edit only their assigned worktree.
- Reviewers inspect the recorded worktree and exact head state.
- A dependent task worktree is created only after its dependencies complete.

## Integration and Cleanup

Follow the target repository's explicit policy. This skill does not authorize
merge, rebase, push, branch deletion, or worktree removal. Perform cleanup only
after explicit user instruction or an applicable project rule authorizes it,
and verify that required work is preserved first.
