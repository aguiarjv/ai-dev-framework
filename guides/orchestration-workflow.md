# Orchestration Workflow

The primary agent in an AI Dev Framework workspace acts as the orchestrator.
It owns user communication, decisions, workflow state, delegation, and final
synthesis. It performs simple operations directly and delegates work that
benefits from repository exploration, live-database exploration, isolated
implementation, fixes, or independent review to specialized subagents.

## Execution Threshold

Perform an operation directly when its target and requested outcome are
explicit, the work is small and bounded, and it requires neither broad
repository exploration nor an unresolved user decision, a plan, parallel work,
or independent review. Reading or editing a known file and running a focused
check are typical direct operations. Do not spawn subagents merely because
they are available.

Use the delegated lifecycle when the scope must be discovered, the work spans
multiple concerns, specialized evidence is required, or the change benefits
from task isolation or independent review. If investigation reveals that a
direct operation crosses this boundary, stop direct execution and move into
the delegated lifecycle.

Standalone project documentation follows the installed
`documentation-management` skill. The orchestrator may synthesize documents
under the managed project's `docs/` folder from user-provided information or
read-only explorer findings without creating an implementation worktree. Use
the standard lifecycle when the request also requires repository changes or
otherwise exceeds that bounded documentation workflow.

## Context Boundary

Keep the primary thread focused on:

- The user's goal, requirements, decisions, and approvals.
- The active plan, task dependency graph, and current statuses.
- Concise subagent handoffs and review outcomes.
- Blockers and the next action for each actionable task.

Do not copy large file contents, raw command output, test logs, or complete
subagent transcripts into the primary thread. Give each subagent only the task
definition, applicable instructions, baseline, latest handoff, and specific
paths needed for its assignment. Persist durable state in managed-project
artifacts so later agents do not depend on chat history.

## Agent Roles

- `explorer` inspects repository code, project documentation, and installed
  guidance without changing files.
- `database-explorer` inspects a live database through an explicitly supplied
  read-only connection or tool.
- `implementer` performs one approved task or one correction pass in its
  assigned Git worktree.
- `reviewer` evaluates a checkpoint or completed implementation without
  changing it.
- The orchestrator chooses agents, supplies bounded context, persists returned
  handoffs from read-only agents, updates plan-level progress, and decides what
  becomes actionable next.

Use a fresh implementer session for a correction pass. Supply the applicable
review and latest task handoff instead of reusing the full context of the agent
that introduced the change.

## Standard Lifecycle

For work that crosses the direct-execution threshold:

1. Clarify the user's feature or bug-fix request with the plan-management
   skill. Never invent a product or project-shape decision.
2. Launch repository explorers and, when live database facts are required, a
   database explorer. Exploration is read-only.
3. Consolidate the returned evidence, propose the plan and task breakdown, and
   obtain the user's approval.
4. Create plan and task artifacts. Record planned worktree and branch names for
   every task.
5. Create worktrees only for tasks whose dependencies are complete. The first
   worktrees are created after plan approval; dependent worktrees are created
   when those tasks become actionable.
6. Spawn one implementer per actionable task. Parallel implementers use
   separate worktrees and branches.
7. At a planned high-risk checkpoint, or when implementation for a task is
   ready, require an implementation handoff and spawn a reviewer.
8. If the review is clean, complete the checkpoint or task. If it has
   actionable findings, set the task to `needs-fix`, persist a review-to-fix
   handoff, and spawn a fresh implementer to correct it.
9. Repeat implementation and review until the task passes or becomes blocked.
10. Create or update accepted ADRs required by the plan under `docs/adrs/`.
11. Complete and archive the plan only after every task, review gate, plan
    criterion, and required ADR is complete.

Reports are optional. Create one under `reports/` only when the user requests a
report or the plan explicitly requires one.

## Delegation Contract

Every subagent assignment states:

- The managed project and the subagent's role.
- The exact objective and boundaries of the assignment.
- The worktree, branch, baseline commit, and comparison target when relevant.
- The plan and task paths it must read.
- The latest handoff and review paths it must read.
- Applicable project instructions, documentation, and workspace guides.
- Files it may change, or an explicit read-only constraint.
- Required checks and the expected handoff recipient.

Do not delegate an unresolved user decision. Ask the user and record the answer
before sending work that depends on it.

## Handoff Rule

Every subagent returns a structured handoff at a meaningful checkpoint and at
the end of its assignment. Implementation agents write their task-local
handoff and update task progress before returning. Read-only explorers and
reviewers return a complete handoff payload to the orchestrator; the
orchestrator persists it without changing its substance.

The orchestrator remains the sole writer of plan-level `PROGRESS.md`. It
serializes task reports and handoffs so parallel agents never edit shared plan
state concurrently.

## Review Cadence

Every implementation task requires a final review. Intermediate reviews occur
only at checkpoints identified in the approved task or when newly discovered
risk makes a checkpoint necessary. Do not review every routine progress update;
that increases coordination cost without improving the review boundary.

## Unavailable Agents

If a required specialized agent cannot run, do not silently absorb its role
into the orchestrator. Tell the user which workflow guarantee is unavailable
and ask whether to continue with a named fallback.
