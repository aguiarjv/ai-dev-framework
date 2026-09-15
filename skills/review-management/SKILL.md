---
name: review-management
description: Prepare, persist, and apply read-only reviews for task checkpoints, task final gates, and final plan integration heads.
---

# Review Management

Use this skill from the orchestrator. Follow the
[Review Management guide](../../guides/review-management.md) and use
`assets/REVIEW.md` for every review artifact.

## Prepare a Review

1. For a task review, read the plan, task definition, task progress, and latest
   implementation handoff. For a plan integration review, read the plan,
   plan progress, plan-level handoff, and every completed task's definition,
   progress, and final review.
2. Confirm a task is `in-progress` at a planned checkpoint or
   `ready-for-review` at its final gate. Confirm a plan integration review runs
   only after all tasks are integrated and complete and combined validation is
   recorded.
3. Capture the exact worktree, branch, head commit, uncommitted-change state,
   comparison base, and review attempt number.
4. Spawn a read-only reviewer with only that bounded context, applicable
   documentation and guides, and the required review and handoff output shapes.

If the target changes while review runs, discard or qualify the stale result
and review the new head state.

## Persist Reviewer Output

The reviewer returns a review payload and a handoff payload. The orchestrator:

1. Writes a task review to `reviews/<plan-id>-<task-id>-review-<NNN>.md`, or a
   plan integration review to
   `reviews/<plan-id>-integration-review-<NNN>.md`, using the next unused
   sequence for that target.
2. Writes the reviewer handoff to the task's `handoffs/` directory for a task
   review or the plan-level `handoffs/` directory for an integration review.
3. Sets `latest_review` and `latest_handoff` in the applicable progress file.
4. Preserves finding IDs and evidence exactly; only normalize template metadata
   and links.

Never overwrite a prior review or handoff.

## Apply the Result

- `clean` at an intermediate checkpoint: keep the task `in-progress` and allow
  the next approved implementation step.
- `clean` at the final task gate: mark satisfied acceptance criteria, set the
  task `ready-for-integration`, clear blockers, and make integration of the
  exact reviewed head the next action.
- `clean` at the plan integration gate: permits plan completion when every
  other completion condition is satisfied and the reviewed head still matches
  plan progress.
- `actionable-findings` at a task gate: set the task to `needs-fix`, record the
  review path and accepted findings, and set the next action to spawn a fresh
  implementer for those findings.
- `actionable-findings` at the plan integration gate: keep the plan
  `in-progress` and add a correction task after resolving any required user
  decision.
- `blocked` at a task gate: set the task to `blocked`, record the review
  limitation, and set one exact resolution action.
- `blocked` at the plan integration gate: keep the plan with completed tasks
  `in-progress`, record the limitation as a blocker, and set one exact
  resolution action.

After every state change, synchronize plan progress and run the plan validator.
Review does not authorize the orchestrator or reviewer to implement a fix.
