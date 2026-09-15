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
- Use the `documentation-management` skill when creating or updating Markdown
  files under a managed project's `docs/` folder.
- Use the `plan-management` skill when creating, resuming, updating,
  validating, reopening, or completing a plan or task.
- Use the `worktree-management` skill to create the plan integration worktree,
  assign task worktrees, and integrate cleanly reviewed task branches after
  plan approval.
- Use the `handoff-management` skill to persist agent handoffs.
- Use the `task-execution` skill inside implementation agents.
- Use the `review-management` skill to coordinate task and final plan
  integration reviews.
- Use the `adr-management` skill for architecture decisions.
- Use the `database-exploration` skill for live database facts.

## Primary Agent Role

The primary agent always acts as the orchestrator. It owns user communication,
clarification, approvals, delegation, shared plan state, and final synthesis.
It performs simple, straightforward operations directly when the target and
requested outcome are explicit, the work is small and bounded, and it requires
neither broad repository exploration nor an unresolved user decision, a plan,
parallel work, or independent review. It does not spawn subagents merely
because they are available. Work beyond that boundary is delegated to the
applicable specialized agents.

Keep the primary context limited to requirements, user decisions, plan and task
state, blockers, concise handoffs, and review outcomes. Do not bring raw logs,
large file contents, or full subagent transcripts into the primary thread.

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
`docs/` folder and the workspace's `.agents/guides/` folder. Plans contain the
complete set of verified references; tasks contain the applicable subset.

Every subagent returns a structured handoff. Implementers write their own
task-local handoffs and task progress. Read-only explorers and reviewers return
complete handoff payloads for the orchestrator to persist. The orchestrator is
the sole writer of plan-level progress.

## Development Workflow

Simple operations may be performed directly under the threshold defined in the
orchestration workflow. For work beyond that threshold:

1. Clarify decisions and use plan-management to explore the project and
   propose a plan and tasks.
2. Obtain user approval before creating integration or task worktrees or starting
   implementation.
3. Create the plan integration worktree, then create task worktrees from its
   current head as tasks become actionable and delegate each to an implementer.
4. Require review after every task and at approved high-risk checkpoints.
5. A clean final task review makes it ready for integration. Merge reviewed
   task branches into the plan integration branch serially; only successful
   integration and validation completes a task.
6. Complete required ADRs, run combined validation, and obtain a clean final
   review of the plan integration head before completing and archiving the
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
- Plan approval authorizes only the task-to-plan integrations defined by the
  worktree-management guide. Do not deliver the plan branch, otherwise merge or
  rebase, push, remove worktrees, delete branches, overwrite, or reuse existing
  project artifacts unless the user or an applicable project policy authorizes
  it.
