---
name: handoff-management
description: Create and consume durable, minimal-context handoffs between agents working on an AI Dev Framework plan or task.
---

# Handoff Management

Follow the [Handoff Management guide](../../guides/handoff-management.md) and
start new handoffs from `assets/HANDOFF.md`.

## Create a Handoff

1. Identify the plan, optional task, sender role, recipient role, and transition
   being recorded.
2. Choose the applicable directory:
   - Plan-level exploration, coordination, or integration review:
     `plans/<plan-id>/handoffs/`.
   - Task-level: `plans/<plan-id>/tasks/<task-id>/handoffs/`.
3. Assign the next unused three-digit sequence in that directory and use
   `<sequence>-<from-role>-to-<to-role>.md` as the filename.
4. Fill every template field with the exact baseline and concise durable state.
5. Verify that the next agent can continue using the task definition, progress,
   named review if any, and this handoff without the sender's transcript.
6. Set `latest_handoff` in the applicable `PROGRESS.md` to the handoff path.

Never overwrite or renumber an existing handoff. Do not include raw logs,
secrets, credentials, personal data, or broad file dumps.

## Read-Only Agent Payloads

Explorers and reviewers cannot write files. Require them to return all fields
and sections from the handoff template. The orchestrator persists the payload,
normalizing only the assigned identifier, timestamp, and artifact links. Do not
silently alter findings, uncertainty, or the requested next action.

## Implementation Handoffs

An implementer writes its own task-local handoff before returning. Use outcome
`checkpoint` for an approved intermediate review boundary, `completed` when
implementation is ready for final review, `changes-requested` when handing
review corrections to another implementer, and `blocked` when work cannot
continue.

## Consume a Handoff

Confirm that its plan, task, worktree, branch, and head commit still match the
current assignment. Read only the referenced context needed for the next
action. If the target state has changed, report the stale handoff to the
orchestrator instead of proceeding from it.
