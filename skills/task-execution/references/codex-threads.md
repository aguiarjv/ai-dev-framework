# Dedicated Codex Implementation Threads

Read this reference only for a task selecting `execution_mode: thread`.
The thread is an implementer with the task-execution contract. Exploration
and review remain subagents; the coordinator owns plan state and integration.
Claude Code continues to use subagents in this pilot.

## Select and Check the Mode

Use a dedicated thread when the user wants to steer a long implementation
conversation directly. Record the user's selection in `TASK.md`. An omitted
`execution_mode` means `subagent`. Changing modes is a definition change:
record the user's decision and refresh the definition timestamp.

Before launching, confirm the later implementation request, integrated
dependencies, and the assigned task worktree and branch. Thread creation also
requires an explicit user request for a separate task, such as "Implement the
plan and create dedicated Codex threads for its thread-mode tasks." A single
request may authorize all named tasks; do not ask again within that scope.

Check the client's available thread controls before selecting the launch
path. Supported controls can create a task, read its messages and status,
send a follow-up, and wait for completion or user input. Use their documented
arguments and limits. Do not install a launcher or infer missing controls.
If they are unavailable, explain the limitation and obtain the user's choice
of a manually opened fresh Codex thread or a change to subagent execution.
Manual threads require a verifiable thread identifier and status too.

Inspect workspace, managed-project, and checkout instructions for conflicting
role rules. Older managed projects may still say that every primary agent is
the orchestrator. Resolve that conflict with the user before launching; the
installer's updater intentionally leaves project-authored instructions alone.
The installer README documents the opt-in instruction update.

## Bootstrap, Register, and Start

The existing `create_thread` control starts a turn and inherits the
coordinator's working directory. It does not accept a task worktree or native
custom-agent role. Reading `.codex/agents/implementer.toml` supplies its role
contract, but does not apply its sandbox or model configuration. Verify actual
session permissions and available tools; retain normal restricted settings.
Do not imply that a prompt changes runtime permissions.

1. Verify that no implementation worker already owns the task, across both
   execution modes. Create its worktree through worktree-management. Keep
   status `not-started` for an initial launch until registration succeeds.
2. Create a fresh conversation with a title identifying project, plan, task,
   and attempt. The initial prompt assigns a read-only bootstrap: read this
   reference, the implementer role, task files, applicable instructions, and
   latest artifacts; verify worktree, branch, and head; report readiness and
   await a separate start message. Do not fork the coordinator conversation.
3. Capture the returned identifier and read the bootstrap result. Verify its
   task, checkout, branch, head, and role against Git and task files. Resolve
   blockers before starting. If creation timed out or its result is uncertain,
   use existing thread listings/status to find the attempt; do not launch a
   duplicate. If the client cannot establish its status, stop and report it.
4. Record `execution_thread_id`, set the task `in-progress`, refresh progress,
   and synchronize plan progress. Run the plan validator. The coordinator
   performs these registration writes; the worker has not edited yet.
5. Send a start message naming the registered thread identifier and task.
   Before editing, the worker checks that the ID matches task progress,
   status is `in-progress`, and its checkout still matches the assignment.
   Use explicit tool working directories or `git -C` for the task checkout;
   the inherited coordinator directory is not its implementation checkout.

Keep prompts within the client's limits (the current create and follow-up
controls accept at most 1,000 UTF-8 bytes). Reference durable files instead of
copying the coordinator transcript. Do not override the model unless the user
requested it.

For example, a bounded bootstrap prompt is:

```text
Act as the implementer in read-only bootstrap mode for
projects/sample/workspace-plans/cache-refresh/tasks/001-build.
Read .agents/skills/task-execution/SKILL.md and its references/codex-threads.md,
.codex/agents/implementer.toml, the task files, applicable instructions, and
latest handoff/review. Verify the assigned worktree, branch, and HEAD.
Return the task identity, verified checkout state, and any blocker. Await a
separate start message; do not edit files or spawn another implementer.
```

During bootstrap, the worker may inspect a `not-started`, `needs-fix`, or
interrupted task. This is not permission to implement: only the matching
registered start message and the normal task-execution checks permit edits.

## Monitor and Review

Read or wait for bounded thread updates. User-input or permission requests are
blockers to surface, not permission for the coordinator to bypass them. The
user may steer the task directly; unresolved scope or architectural decisions
return to the coordinator before work proceeds. Persist accepted decisions
in task artifacts so the other sessions can discover them.

At a checkpoint the worker writes task progress and a checkpoint handoff,
then stops its turn. Resume the same registered thread after the coordinator
records the independent review result and explicitly releases that boundary.
After final implementation the worker writes `ready-for-review` and its
exact-head handoff. The coordinator verifies both before starting review.
An idle, completed, or archived conversation alone never marks a task ready
for review, integrated, or completed.

Final actionable findings and integration conflicts use a fresh implementer
session, as in the existing correction policy. Keep the task's worktree and
branch. Confirm the old worker is no longer executing, preserve its identifier
and outcome in task `Work Completed` and the correction handoff, bootstrap the
replacement, then register its new ID and send the matching start message.
Keep the former ID in progress until replacement registration succeeds.

## Resume, Interruption, and Replacement

The coordinator reads durable task state first, then queries the recorded
thread and verifies Git before deciding what to do:

- Running: observe the existing worker; do not start a second one.
- Idle at a checkpoint: verify its handoff and review boundary before sending
  the next permitted message to that same thread.
- Implementation finished: verify `ready-for-review`, the handoff, and Git;
  proceed to independent review rather than restarting implementation.
- Interrupted or archived: verify it is no longer executing and inspect its
  durable progress, handoff, and Git changes. Resume the same conversation
  only when its identity and assignment remain verifiable. A fresh correction
  still requires a new session.
- Missing or inaccessible: absence from a listing is not proof it stopped.
  Record the limitation and resolve it with the user before replacement.

Never remove an ID to hide an uncertain worker. A first thread launch failure
before an ID is obtained may leave a task `blocked` with
`execution_thread_id: null` and a concrete resolution action. A user-approved
switch from subagent execution can retain that subagent's handoffs and reviews;
verify it stopped before launching the first thread. Validation checks the
recorded snapshot; it cannot prove that a previous thread launch never
occurred or that a known ID was preserved. Historical IDs remain after review,
completion, archival, and worktree cleanup; they do not require that the old
chat or checkout still exists. A context reset waits until all implementation
workers, including dedicated threads, have stopped and state is durable.

## Worked Pilot

Use one explicitly selected long implementation task in an approved plan:

1. Set `execution_mode: thread`; leave other tasks in subagent mode.
2. Launch through the bootstrap/register/start procedure above.
3. Exercise direct user steering and a coordinator cold resume while the
   worker is active. Verify that resume observes the existing thread.
4. Obtain the implementation handoff, run a reviewer subagent, and integrate
   only the exact cleanly reviewed head through the normal transaction.
5. Record elapsed wall time, coordination interventions, review/correction
   count, and trustworthy usage when available in task `Resource Usage`.

Current native metrics label root conversations as `orchestrator`, including
dedicated implementer threads, and workspace-root cwd may hide attribution.
Do not treat those role totals as pilot implementer totals or infer absent
usage as zero. Keep unknown counts explicit and avoid double-counting runs.
Compare supervision effort and review outcomes before broadening the pilot.
