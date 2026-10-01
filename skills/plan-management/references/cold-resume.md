# Cold Resume Checklist

Use this after the user starts a new session for an approved plan. It is also
useful after compaction or a handoff to another orchestrator.

1. Identify the managed project and exact plan path. Read `PLAN.md` and the
   plan-level `PROGRESS.md`. Confirm `approved_at`, delivery branch, integration
   order, combined validation, task statuses, blockers, and `Next Actions`.
2. Read `TASK.md` and `PROGRESS.md` only for tasks in `current_tasks` or `Next
   Actions`. Read their latest handoff/review artifacts when those paths are
   populated. Expand to completed dependencies only if needed for the next
   action.
3. Check the recorded integration worktree, branch, head commit, and clean/dirty
   state against Git. Check the same fields for any task about to be assigned,
   reviewed, or integrated. Do not silently repair a mismatch.
4. Run `scripts/validate_plan.py <path-to-plan>`. Report any discrepancy and
   resolve it before editing state or launching work. Confirm no earlier agent
   is still running before starting a replacement.
   For a thread task, read its `execution_thread_id` and use available Codex
   thread controls to verify identity and status. Observe a running worker;
   an idle conversation requires checking the task's handoff and review gate.
   Missing or inaccessible status does not prove the worker stopped. Use the
   task-execution skill's `references/codex-threads.md` before resuming or
   replacing it, and retain prior IDs as history.
5. Distinguish approval to create plan files from a later user message explicitly
   requesting implementation. Check the plan progress `Implementation Request`
   section when present. If the plan is still awaiting that message,
   summarize its paths and wait; do not create worktrees or launch agents.
   Otherwise summarize the exact next action and any blocker in a few lines,
   then continue through the relevant plan-management step.

The files are authoritative for workflow state, but recorded Git facts must be
verified. A reset does not grant new authority to merge, push, delete, or
change plan scope.
