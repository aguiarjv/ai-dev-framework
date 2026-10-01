# AI Development Workspace

This meta repository coordinates AI-assisted work across projects stored under
`projects/`.

## Guidance Routing

Read only the guides and skills needed for the current operation. The list
below is a routing index, not a request to load every guide at session start.

- Follow `.agents/guides/orchestration-workflow.md` when using the delegated
  development lifecycle and context boundaries.
- Follow `.agents/guides/multi-project-workspace.md` when resolving workspace structure.
- Follow `.agents/guides/plan-and-task-management.md` when orchestrating plan
  lifecycle state; implementers use the task-execution skill for routine task
  progress and consult the guide only for unclear lifecycle rules.
- Follow `.agents/guides/handoff-management.md` when recording an agent transition.
- Follow `.agents/guides/worktree-management.md` when managing isolated task worktrees.
- Follow `.agents/guides/review-management.md` for project reviews.
- Follow `.agents/guides/report-management.md` when creating project reports.
- Follow `.agents/guides/adr-management.md` for decisions under `workspace-docs/adrs/`.
- Follow `.agents/guides/database-exploration.md` for live database inspection.
- Follow `.agents/guides/commit-management.md` for every authored Git commit
  message.
- Use the `grill-me` skill when the user explicitly asks to stress-test an idea
  outside the new-plan workflow.
- Use the `project-setup` skill when adding a managed project.
- Use the `documentation-management` skill when creating or updating Markdown
  files under a managed project's `workspace-docs/` folder.
- Use the `plan-management` skill when creating, resuming, updating,
  validating, reopening, or completing a plan or task.
- Use the `worktree-management` skill to create the plan integration worktree,
  assign task worktrees, and integrate cleanly reviewed task branches after
  the later explicit implementation request.
- Use the `handoff-management` skill to persist agent handoffs.
- Use the `task-execution` skill inside implementation agents.
- Use the `review-management` skill to coordinate task and final plan
  integration reviews.
- Use the `adr-management` skill for architecture decisions.
- Use the `database-exploration` skill for live database facts.
- Use the `frontend-design` skill for new or substantially redesigned web UI.
- Use the `webapp-testing` skill for browser-level checks of local web apps.
- Use the `commit-management` skill whenever creating, amending, squashing,
  merging, reverting, or proposing a Git commit.

## Primary Agent Role

The primary agent normally acts as the orchestrator. It owns user communication,
clarification, approvals, delegation, shared plan state, and final synthesis.
It performs simple, straightforward operations directly when the target and
requested outcome are explicit, the work is small and bounded, and it requires
neither broad repository exploration nor an unresolved user decision, a plan,
parallel work, or independent review. It does not spawn subagents merely
because they are available. Work beyond that boundary is delegated to the
applicable specialized agents.

An explicitly assigned dedicated Codex implementation thread acts as the
implementer for its named task and uses the task-execution skill directly.
It follows the same task scope, worktree, progress, and handoff contract as an
implementer subagent. It does not coordinate the plan or spawn an implementer.
Use subagents by default; dedicated implementation threads require the user's
selection of `execution_mode: thread` and explicit authorization to create
the separate task. This pilot is Codex-only; Claude Code uses subagents.
Follow `.agents/skills/task-execution/references/codex-threads.md` for thread
bootstrap, registration, monitoring, and resume.

Keep the primary context limited to requirements, user decisions, plan and task
state, blockers, concise handoffs, and review outcomes. Do not bring raw logs,
large file contents, or full subagent transcripts into the primary thread.
For high-volume tests, browser checks, and log polling, use bounded commands or
an appropriately scoped non-fork agent and return a concise result plus an
artifact path. Delegation should save main-context space without multiplying
work unnecessarily. Do not create conversation forks for framework work;
use fresh-context specialized agents when delegation is warranted.

## Agent Roles

- Use `explorer` for read-only repository investigation and planning evidence.
- Use `database-explorer` for live database facts through verified read-only
  access.
- Use `implementer` for one approved task or correction pass in its assigned
  worktree.
- Use `reviewer` for read-only task checkpoints, final task reviews, and final
  plan integration reviews.

Before finalizing a plan, launch explorer agents with clearly separated
investigation areas and the same repository worktree, branch, and baseline
commit. Wait for their results and consolidate evidence into the plan and task
files. If live database evidence is required, give `database-explorer` a
bounded question and verified read-only access.

Every explorer also inspects relevant candidates in the managed project's
`workspace-docs/` folder and the workspace's `.agents/guides/` folder. Plans contain the
complete set of verified references; tasks contain the applicable subset.

Every subagent returns a structured handoff. Implementers write their own
task-local handoffs and task progress. Read-only explorers and reviewers return
complete handoff payloads for the orchestrator to persist. The orchestrator is
the sole writer of plan-level progress.

## Development Workflow

Simple operations may be performed directly under the threshold defined in the
orchestration workflow. Before planning a fix, inspect related active and
completed plans and the recorded delivery state. Continue an unintegrated
task, add a correction task to an active plan, or propose reopening a completed
but undelivered plan when the fix serves its goal. Keep the approval steps for
the correction task and its later implementation request. For delivered work,
use the direct-operation threshold for a small fix under repository rules and
a new plan for broader or distinct work. For work beyond that threshold with
no suitable existing plan:

1. Clarify decisions and use plan-management to explore the project and
   propose a plan and tasks.
2. Obtain approval to create the plan and task files. Create and validate them,
   summarize their paths, then end the turn. Wait for a later user message
   explicitly requesting implementation of that plan.
3. After that implementation request, create the plan integration worktree.
   Create task worktrees from its current head as tasks become actionable and
   assign each to an implementer using its recorded execution mode.
4. Require review after every task and at approved high-risk checkpoints.
5. A clean final task review makes it ready for integration. Merge reviewed
   task branches into the plan integration branch serially; only successful
   integration and validation completes a task.
6. Complete required ADRs, run combined validation, and obtain a clean final
   review of the plan integration head before completing and archiving the
   plan. Create reports only when requested or required by the plan.

An approved follow-up correction task joins at step 3 after its later explicit
implementation request. Verify or restore the existing integration checkout,
then create its task worktree from the current plan head.

At plan approval and after a task integration, the orchestrator may offer a
context reset once state is durable and no agents are running. The user runs
`/clear` in Claude Code; resume from the plan's `PLAN.md` and `PROGRESS.md`
using the plan-management skill. Never reset while a review, merge, or agent
handoff is in flight.

## Working Rules

- Resolve `workspace-docs/`, `workspace-plans/`, `workspace-scripts/`,
  `workspace-reviews/`, and `workspace-reports/` relative to the managed
  project's `projects/<project-name>/` folder, never relative to a worktree.
- Work in the applicable checkout under
  `projects/<project-name>/worktrees/<default-branch-name>/` for the initial
  checkout or `projects/<project-name>/worktrees/<plan-id>/<worktree-name>/`
  for plan integration and task worktrees.
- Read the managed project's workspace instructions and any instructions inside
  its Git checkout before assigning or changing project work.
- Store project coordination artifacts in that project's `workspace-docs/`, `workspace-plans/`,
  `workspace-reviews/`, and `workspace-reports/` folders, not inside another managed project.
- Track durable state in plan, task, handoff, review, ADR, and report files so a
  new agent can continue without prior chat history.
- Treat the orchestrator as the sole writer of plan-level `PROGRESS.md` files.
  Task agents update only their own task-level progress and handoffs.
- Run parallel tasks in separate Git worktrees and branches.
- Ask the user whenever missing information affects requirements, scope,
  acceptance criteria, dependencies, architecture, integration, project
  structure, or another decision. Do not guess.
- A later explicit request to implement the created plan or an approved
  follow-up correction task authorizes its task work, recorded worktrees, and
  task-to-plan integrations defined by the worktree-management guide. Do not
  deliver the plan branch, otherwise merge or rebase, push, remove worktrees,
  delete branches, overwrite, or reuse existing project artifacts unless the
  user or an applicable project policy authorizes it.
