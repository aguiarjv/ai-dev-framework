# Plan and Task Management

Use the `plans/` directory in a managed project to define work, track its
progress, and preserve enough context for another agent to continue it.

## Structure

```text
plans/
  done/
    <completed-plan-name>/
      PLAN.md
      PROGRESS.md
      handoffs/
      tasks/
        <task-folder>/
          TASK.md
          PROGRESS.md
          handoffs/
  <plan-name>/
    PLAN.md
    PROGRESS.md
    handoffs/
    tasks/
      001-<task-name>/
        TASK.md
        PROGRESS.md
        handoffs/
      002-<task-name>/
        TASK.md
        PROGRESS.md
        handoffs/
```

Use a descriptive name for each plan. Prefix task folders with a three-digit
number so their intended order is clear and their paths remain stable.

## File Responsibilities

Keep definitions separate from execution progress:

- `PLAN.md` defines the exploration baseline, goal, scope, approach, ordered
  tasks, dependencies, related repository paths, relevant documentation and
  guides, open questions, and completion criteria.
- The plan-level `PROGRESS.md` summarizes the state of the complete plan,
  including completed tasks, current and next tasks, blockers, and next
  actions.
- `TASK.md` defines one task's objective, requirements, dependencies, related
  repository paths, relevant documentation and guides, acceptance criteria,
  and validation expectations.
- The task-level `PROGRESS.md` records the task's current state, completed work,
  decisions, changed files, validation results, blockers, and exact next action.
- Plan-level `handoffs/` stores immutable exploration and coordination
  transitions that apply to the whole plan.
- Each task's `handoffs/` stores immutable implementation, review, correction,
  and completion transitions for that task.

Treat `PLAN.md` and `TASK.md` as stable definitions. Record ongoing work in the
corresponding `PROGRESS.md` files. If requirements or scope change, update the
definition's `updated` timestamp and note the change in the relevant progress
file.

Completion and acceptance checkbox state is the only lifecycle state kept in a
definition file. Checking an unchanged criterion does not require refreshing
the definition's `updated` timestamp; changing its wording or meaning does.

Store identifiers, creation dates, dependencies, statuses, and update
timestamps in YAML frontmatter. Use an ISO 8601 date for creation dates and an
ISO 8601 UTC timestamp for definition and progress updates.

The plan frontmatter also records the repository state explored during plan
creation:

- `worktree`: The checkout path relative to the managed project folder.
- `branch`: The branch checked out in that worktree.
- `baseline_commit`: The full commit SHA at `HEAD`, or YAML `null` when the
  repository has no commits.
- `approved_at`: The ISO 8601 UTC time when the user approved the proposed plan
  and task breakdown.

Each task definition records its intended isolated assignment:

- `planned_worktree`: A path below `worktrees/` relative to the managed project.
- `planned_branch`: The branch intended for the task.
- `review_required`: `true` for the required final implementation review.

## Statuses

Use these status values for plans:

- `not-started`: No implementation work has begun.
- `in-progress`: Work is actively underway.
- `blocked`: Work cannot continue until a recorded blocker is resolved.
- `completed`: Acceptance and completion criteria are satisfied and validation
  is recorded.

Tasks use those values and these review-loop states:

- `ready-for-review`: Implementation and focused validation are complete; the
  recorded head state is awaiting review.
- `needs-fix`: A review has actionable findings requiring a fresh correction
  pass.

The task-level `PROGRESS.md` is the source of truth for detailed task state. The
plan-level `PROGRESS.md` summarizes every task's status and the overall plan
state. Update both after a task status changes.

Apply these lifecycle rules:

- A task is actionable only when every task ID in its `depends_on` list has
  status `completed`. An unmet dependency does not by itself make a task
  `blocked`; leave the task `not-started` until its dependencies are complete.
- Every `depends_on` value must be an ID of another task in the same plan.
  Dependencies must not be self-referential or cyclic.
- A plan is `not-started` while all tasks are `not-started`.
- A plan is `in-progress` while work has begun and at least one incomplete task
  is active, actionable, ready for review, or needs a fix, or while all tasks
  are complete but plan-level completion criteria remain unfinished.
- A plan is `blocked` when incomplete tasks remain but no task can proceed
  because of one or more recorded unresolved blockers, including tasks that
  depend on blocked tasks.
- A plan is `completed` only under the completion rules below.
- Completed tasks and plans are terminal. Reopen one only when the user
  explicitly requests it. Record the reason, set the reopened item to
  `in-progress`, refresh its progress state, and, for a plan, move it from
  `plans/done/` back to `plans/` before continuing.
- When reopening a task makes a completed transitive dependent's dependency
  incomplete, reset that dependent to `not-started`, record why its prior
  completion must be reassessed, and repeat through the dependency graph. If
  the plan was completed, reopen and move the plan before changing its tasks.
- An implementer moves a task from `in-progress` to `ready-for-review`; it does
  not complete the task.
- A clean final review moves `ready-for-review` to `completed`. Actionable
  findings move it to `needs-fix`; the orchestrator moves it to `in-progress`
  when assigning a fresh correction agent.

Never renumber or reuse an existing task ID. Add a task with the next unused
three-digit sequence after the highest sequence already assigned, even when an
earlier task was removed.

Keep exactly one `PLAN.md` Tasks-table row for every task folder. Its link must
target that task's `TASK.md`, and `Depends on` must be `None` or a
comma-separated list matching the task's `depends_on` frontmatter.

## Project Exploration

Before finalizing a new plan and its tasks, the orchestrator launches explorer
subagents to analyze the project's current state. Exploration is read-only and
must identify:

- Relevant current behavior or structure.
- Existing files and folders likely to be used or changed.
- Probable new files and folders needed by the work.
- Whether each path is expected to be inspected, modified, or created.
- Evidence for the findings and any unresolved uncertainty.
- Existing documentation under the managed project's `docs/` folder that
  constrains, explains, or otherwise materially informs the work.
- Installed workspace guides under `.agents/guides/` that apply to the work.
- Probable project documentation that the work must create or update.

Resolve the worktree, checked-out branch, and baseline commit before launching
the explorers. Give every explorer the same baseline so their findings describe
one consistent repository state, then store that baseline in `PLAN.md`.

The orchestrator gives each explorer a clear investigation area and
consolidates their findings. If findings conflict or required paths remain
uncertain, continue exploring or ask the user rather than guessing.

Every explorer checks the managed project's `docs/` folder for documentation
relevant to its investigation area. It also checks `.agents/guides/` for
applicable shared guidance. Inspect candidate files before declaring them
relevant; do not rely on filenames alone. An empty folder or the absence of a
relevant file is a valid finding and must be reported explicitly.

Both `PLAN.md` and `TASK.md` contain a `Related Files and Folders` table with
these columns:

- `Path`: A file or folder path relative to the repository checkout root.
- `State`: `existing` for a verified path or `planned` for a path expected to
  be created.
- `Expected Use`: One or more of `inspect`, `modify`, or `create`.
- `Relevance`: Why the path matters to the plan or task.
- `Evidence`: The explorer finding that supports the entry.

Use one repository-relative path per row. Keep `State` to `existing` or
`planned`, and express `Expected Use` as a comma-separated combination of
`inspect`, `modify`, and `create`. `Relevance` and `Evidence` must be concrete
and non-empty.

The plan contains the complete set of probable related paths. Each task contains
only the subset relevant to that task. Do not mark a path as `existing` unless
an explorer verified it.

Record unresolved, non-blocking uncertainty in the plan's `Open Questions`
section. Ask the user about questions that affect scope, requirements,
dependencies, acceptance criteria, or other decisions needed to finalize the
plan.

Before writing the plan, work through unresolved user decisions in dependency
order, give a recommendation for each, and obtain explicit confirmation of the
complete plan and task breakdown. Exploration establishes facts; it does not
replace user decisions.

In `Related Files and Folders`, do not use absolute paths or paths relative to
the managed project folder. Repository-relative paths remain stable when work
moves between worktrees.

Both `PLAN.md` and `TASK.md` also contain a `Relevant Documentation and Guides`
table with these columns:

- `Path`: A documentation or guide path using the source-specific root below.
- `Source`: `project-docs` or `workspace-guide`.
- `State`: `existing` or `planned`.
- `Expected Use`: One or more of `inspect`, `modify`, or `create`.
- `Relevance`: How the document or guide informs the plan or task.
- `Evidence`: The explorer finding that established its relevance.

For `project-docs`, use a path beginning with `docs/`, relative to the managed
project folder. These entries may be existing or planned and may be inspected,
modified, or created. A planned entry in the plan table must include `create`;
a downstream task may use only `inspect` or `modify` after another task creates
it. Existing entries must not use `create`. For `workspace-guide`, use a path
beginning with `.agents/guides/`, relative to the meta-repository root.
Workspace guides must be existing and are inspected, not modified by
managed-project work.

The plan contains the complete set of relevant documentation and guides. Each
task contains only its applicable subset, with matching source and state; its
expected use must be a subset of the plan entry's expected use. If none apply,
keep the table header and omit data rows.

If explorer subagents are unavailable, the orchestrator tells the user and asks
how to proceed instead of silently skipping exploration.

## Creating a Plan

1. Clarify the plan's goal, scope, requirements, task boundaries, completion
   criteria, review checkpoints, and ADR needs without guessing.
2. Resolve the exploration baseline, launch explorer subagents, and consolidate
   the current-state findings, probable related paths, relevant project
   documentation and workspace guides, supporting evidence, and open questions.
3. Record planned worktree and branch names for every task and present the
   complete plan and task breakdown to the user.
4. After user approval, create `plans/<plan-name>/` with `PLAN.md`,
   `PROGRESS.md`, `handoffs/`, and `tasks/`.
5. Create each numbered task folder with `TASK.md`, `PROGRESS.md`, and
   `handoffs/`.
6. Persist accepted explorer handoffs at plan level and initialize progress
   with the first actionable tasks.
7. Create worktrees for immediately actionable tasks. Create dependent task
   worktrees only after their dependencies complete.

Do not invent missing scope, requirements, dependencies, or acceptance
criteria. Ask the user when those details affect the plan.

## Managing Progress

Before starting or resuming work, read `PLAN.md`, the plan-level `PROGRESS.md`,
and every current task's `TASK.md` and `PROGRESS.md`.

The orchestrator is the sole writer of the plan-level `PROGRESS.md`. A task
agent writes only its own task-level `PROGRESS.md`, then reports its checkpoint
or result to the orchestrator. The orchestrator serializes those reports into
the shared plan progress file. This ownership rule also applies when tasks run
in parallel.

Tasks may run in parallel when their dependencies are satisfied. The plan-level
`current_tasks` list contains every `in-progress` task. Each task-level
`PROGRESS.md` records that task's exact next action, while the plan-level `Next
Actions` table summarizes the actions available across the plan.

The plan-level `Next Actions` table contains every `in-progress` task and every
`not-started` task whose dependencies are complete. It also contains every
`ready-for-review` task, every `needs-fix` task, and every `blocked` task whose
next action describes resolving or waiting on its blocker. Use the literal
`plan` as the task value when all tasks are complete but a plan-level completion
action remains. A completed plan has no next-action rows.

The plan and task `Blockers` sections list unresolved blockers only. Use
`None.` when no unresolved blocker exists. A `blocked` status requires a
concrete blocker. Use `None.` in a completed task's `Next Action` section.

Keep exactly one plan-level `Task Status` row for every task. Its status must
match the task progress frontmatter, and its result-or-blocker cell must briefly
explain the current state.

Before starting a task, use its approved `planned_worktree` and
`planned_branch` to create or resolve the isolated checkout, then record the
actual worktree and branch in task progress. Refresh `head_commit` and
`uncommitted_changes` at every meaningful checkpoint and before a handoff. When
two or more tasks run in parallel, each must use a distinct Git worktree and
branch; parallel agents must not edit the same checkout.

Update the task-level `PROGRESS.md` after a meaningful checkpoint and before a
handoff. Keep it concise and make the next action specific enough that another
agent can resume without reconstructing prior work.

Set `latest_handoff` in plan or task progress whenever a new transition is
accepted. Set `latest_review` in task progress whenever a reviewer result is
persisted. Both values use paths relative to the managed project and must point
to existing artifacts.

## Reviewing a Task

Every task requires a final read-only review of the exact worktree and head
state recorded by the implementer. Additional reviews occur only at high-risk
checkpoints named in the approved task or when new evidence makes one necessary.

The reviewer returns complete review and handoff payloads. Because the reviewer
is sandboxed read-only, the orchestrator writes them under `reviews/` and the
task's `handoffs/` directory. A clean checkpoint review leaves the task
`in-progress`. A clean final review completes it. Actionable findings set it to
`needs-fix` and require a fresh implementer session followed by another review.

When implementation is ready:

1. Confirm its requirements and required focused validation are satisfied.
2. Create an implementation-to-review handoff and set the task to
   `ready-for-review`.
3. Run the final review. If it has findings, persist the review-to-fix handoff,
   set `needs-fix`, and run another implementation and review cycle.
4. After a clean review, mark every satisfied or explicitly accepted acceptance
   criterion as checked and set the task to `completed`.
5. Record the review and validation in task progress. The orchestrator updates
   plan progress and selects the next actionable task or tasks.

## Architecture Decisions

Record whether the plan requires an ADR and why. Add every planned ADR under
`docs/adrs/` to the plan documentation table and assign its creation or update
to a task. An implementation agent must return a newly discovered architectural
choice to the orchestrator and user instead of deciding it silently.

## Completing a Plan

A plan is complete when all required tasks and the plan's completion criteria
are satisfied and no unresolved blocker prevents completion.

Mark every satisfied plan completion criterion as checked. When every task is
complete but any plan criterion is still unchecked, keep the plan
`in-progress` and record a `plan` next action. Set the plan to `completed` only
after every criterion is checked.

Record the final outcome in the plan-level `PROGRESS.md`, then move the entire
plan folder to `plans/done/<plan-name>/`. Keep the plan and task files together
so their definitions, decisions, validation, and progress history remain
available.

Do not complete a plan until every required final review is clean and every ADR
required by the approved plan exists and reflects the accepted decision.
Reports are optional unless the user or approved plan requires one.

## Validation

Run the plan-management validator after creating or structurally updating a
plan and before completing it:

```text
python3 .agents/skills/plan-management/scripts/validate_plan.py <path-to-plan>
```

Resolve every reported structural or state-consistency error before proceeding.
