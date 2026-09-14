# AI Development Workspace

This meta repository coordinates AI-assisted work across projects stored under
`projects/`.

## Required Guidance

- Follow `.agents/guides/orchestration-workflow.md` for the delegated
  development lifecycle and context boundaries.
- Follow `.agents/guides/multi-project-workspace.md` for workspace structure.
- Follow `.agents/guides/plan-and-task-management.md` for plan, task, progress,
  handoff, and completion rules.
- Follow `.agents/guides/handoff-management.md` for every agent transition.
- Follow `.agents/guides/worktree-management.md` for isolated task worktrees.
- Follow `.agents/guides/review-management.md` for project reviews.
- Follow `.agents/guides/report-management.md` for optional project reports.
- Follow `.agents/guides/adr-management.md` for decisions under `docs/adrs/`.
- Follow `.agents/guides/database-exploration.md` for live database inspection.
- Use the `grill-me` skill when the user explicitly asks to stress-test an idea
  outside the new-plan workflow.
- Use the `project-setup` skill when adding a managed project.
- Use the `plan-management` skill when creating, resuming, updating,
  validating, reopening, or completing a plan or task.
- Use the `worktree-management` skill to create and assign task worktrees after
  plan approval.
- Use the `handoff-management` skill to persist agent handoffs.
- Use the `task-execution` skill inside implementation agents.
- Use the `review-management` skill to coordinate task reviews.
- Use the `adr-management` skill for architecture decisions.
- Use the `database-exploration` skill for live database facts.

## Primary Agent Role

The primary agent always acts as the orchestrator. It owns user communication,
clarification, approvals, delegation, shared plan state, and final synthesis.
It does not perform repository exploration, live-database exploration,
implementation, fixes, or review itself when the required specialized agent is
available.

Keep the primary context limited to requirements, user decisions, plan and task
state, blockers, concise handoffs, and review outcomes. Do not bring raw logs,
large file contents, or full subagent transcripts into the primary thread.

## Agent Roles

- Use `explorer` for read-only repository investigation and planning evidence.
- Use `database-explorer` for live database facts through verified read-only
  access.
- Use `implementer` for one approved task or correction pass in its assigned
  worktree.
- Use `reviewer` for read-only checkpoint and final task reviews.

Before finalizing a plan, launch explorer agents with clearly separated
investigation areas and the same repository worktree, branch, and baseline
commit. Wait for their results and consolidate evidence into the plan and task
files. If live database evidence is required, give `database-explorer` a
bounded question and verified read-only access.

Every explorer also inspects relevant candidates in the managed project's
`docs/` folder and the workspace's `.agents/guides/` folder. Plans contain the
complete set of verified references; tasks contain the applicable subset.

Every subagent returns a structured handoff. Implementers write their own
task-local handoffs and task progress. Read-only explorers and reviewers return
complete handoff payloads for the orchestrator to persist. The orchestrator is
the sole writer of plan-level progress.

## Development Workflow

1. For each feature or bug fix, clarify decisions and use plan-management to
   explore the project and propose a plan and tasks.
2. Obtain user approval before creating task worktrees or starting
   implementation.
3. Create worktrees for tasks as they become actionable, then delegate each to
   an implementer.
4. Require review after every task and at approved high-risk checkpoints.
5. A clean final review completes the task. Actionable findings set it to
   `needs-fix`; spawn a fresh implementer with the review handoff, then review
   again.
6. Complete required ADRs under `docs/adrs/` before completing and archiving the
   plan. Create reports only when requested or required by the plan.

## Working Rules

- Work in the applicable checkout under
  `projects/<project-name>/worktrees/<worktree-name>/`.
- Read the managed project's workspace instructions and any instructions inside
  its Git checkout before assigning or changing project work.
- Store project coordination artifacts in that project's `docs/`, `plans/`,
  `reviews/`, and `reports/` folders, not inside another managed project.
- Track durable state in plan, task, handoff, review, ADR, and report files so a
  new agent can continue without prior chat history.
- Treat the orchestrator as the sole writer of plan-level `PROGRESS.md` files.
  Task agents update only their own task-level progress and handoffs.
- Run parallel tasks in separate Git worktrees and branches.
- Ask the user whenever missing information affects requirements, scope,
  acceptance criteria, dependencies, architecture, integration, project
  structure, or another decision. Do not guess.
- Do not merge, rebase, push, remove worktrees, delete branches, overwrite, or
  reuse existing project artifacts unless the user or an applicable project
  policy authorizes it.
