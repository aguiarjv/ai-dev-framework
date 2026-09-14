---
name: review-management
description: Prepare, persist, and apply read-only implementation reviews for plan task checkpoints and final review gates.
---

# Review Management

Use this skill from the orchestrator. Follow the
[Review Management guide](../../guides/review-management.md) and use
`assets/REVIEW.md` for every review artifact.

## Prepare a Review

1. Read the plan, task definition, task progress, and latest implementation
   handoff.
2. Confirm the task is `in-progress` at a planned checkpoint or
   `ready-for-review` at the final gate.
3. Capture the exact worktree, branch, head commit, uncommitted-change state,
   comparison base, and review attempt number.
4. Spawn a read-only reviewer with only that bounded context, applicable
   documentation and guides, and the required review and handoff output shapes.

If the target changes while review runs, discard or qualify the stale result
and review the new head state.

## Persist Reviewer Output

The reviewer returns a review payload and a handoff payload. The orchestrator:

1. Writes the review to
   `reviews/<plan-id>-<task-id>-review-<NNN>.md` using the next unused sequence
   for that plan and task.
2. Writes the reviewer handoff to the task's `handoffs/` directory.
3. Sets `latest_review` and `latest_handoff` in task progress.
4. Preserves finding IDs and evidence exactly; only normalize template metadata
   and links.

Never overwrite a prior review or handoff.

## Apply the Result

- `clean` at an intermediate checkpoint: keep the task `in-progress` and allow
  the next approved implementation step.
- `clean` at the final gate: mark satisfied acceptance criteria, set the task
  `completed`, clear blockers, and set the next action to `None.`.
- `actionable-findings`: set the task to `needs-fix`, record the review path and
  accepted findings, and set the next action to spawn a fresh implementer for
  those findings.
- `blocked`: set the task to `blocked`, record the review limitation as a
  blocker, and set one exact resolution action.

After every state change, synchronize plan progress and run the plan validator.
Review does not authorize the orchestrator or reviewer to implement a fix.
