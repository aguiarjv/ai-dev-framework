---
name: plan-management
description: Create, resume, update, and complete structured plans and tasks in an AI Dev Framework managed project. Use when work must be planned, tracked across agent handoffs, or archived after completion.
---

# Plan Management

Use this skill for plans stored under a managed project's `plans/` directory.
Follow the [Plan and Task Management guide](../../guides/plan-and-task-management.md)
and use the templates in `assets/` without removing required metadata or
sections.

## Required Context

Before creating or changing files, identify:

- The managed project under `projects/<project-name>/`.
- The plan to create, resume, update, or complete.
- The repository worktree, branch, and commit the plan is based on.
- The goal, scope, completion criteria, and dependencies relevant to the work.
- The task breakdown and each task's acceptance criteria and validation needs.
- The planned worktree and branch for each task.
- The required final review and any high-risk intermediate review checkpoints.
- Whether the work makes a durable architectural decision and the ADR path when
  one is required.
- The existing and planned repository-relative files or folders related to the
  plan and each task.
- The existing or planned managed-project documentation and installed workspace
  guides relevant to the plan and each task.

Ask the user when missing information affects any of these decisions. Do not
invent requirements, scope, acceptance criteria, dependencies, task boundaries,
validation expectations, or completion evidence.

## Clarify a New Plan

Before writing a new plan or any of its tasks, interview the user until both of
you share an explicit understanding of the work. Do not treat a likely answer,
a convention, or the agent's recommendation as the user's decision.

Map the required decisions as a design tree: each unresolved decision branches
into the decisions that depend on it. Work through the tree in rounds. In each
round:

1. Identify the complete frontier: every unresolved decision whose
   prerequisites are already settled.
2. Ask all frontier questions together, number them, and give a recommended
   answer with a concise rationale for each one.
3. Wait for the user's answers before asking questions that depend on them.
4. Recompute the frontier from the answers and repeat until no required
   decision remains unresolved.

Ask even when one answer appears obvious. Recommendations help the user decide;
they do not authorize the agent to decide for them. At minimum, settle the
goal, in-scope and out-of-scope behavior, requirements, constraints,
dependencies, approach choices that affect behavior or project shape, task
boundaries, acceptance criteria, validation expectations, and documentation
deliverables.

Finding facts is the agent's responsibility. Inspect the repository and use the
required explorer subagents instead of asking the user for information that can
be established from the environment. If a fact is still unavailable after
reasonable investigation and it blocks a decision, explain what was checked
and ask the user for the missing information. Exploration may proceed while
unrelated frontier questions are being answered.

After exploration and all decision rounds are complete, summarize the proposed
plan and task breakdown, including the key decisions and completion criteria.
Ask the user to confirm that this represents the shared understanding. Do not
create the plan or task files until the user confirms it. Do not carry an
unresolved user decision into `Open Questions`; that section is only for
explicitly accepted, non-blocking uncertainty.

## Structure

Keep active plans in `plans/<plan-name>/`:

```text
<plan-name>/
  PLAN.md
  PROGRESS.md
  handoffs/
  tasks/
    001-<task-name>/
      TASK.md
      PROGRESS.md
      handoffs/
```

Prefix task folders with three-digit sequence numbers. Keep a task's identifier
equal to its folder name. Keep the plan identifier equal to its folder name.
Use handoff files as immutable transition records; `PROGRESS.md` remains the
source of truth for current state.

## Templates

Use these files as the canonical starting points:

- `assets/plan/PLAN.md` for the plan definition.
- `assets/plan/PROGRESS.md` for overall plan progress.
- `assets/task/TASK.md` for a task definition.
- `assets/task/PROGRESS.md` for task progress and handoff state.

Replace every placeholder when creating a file. Preserve the YAML frontmatter
keys and Markdown headings so agents and future automation can read the files
consistently.

Use an ISO 8601 UTC timestamp for `updated` and an ISO 8601 date for `created`.
Plan and task definitions both have an `updated` field. Refresh it whenever
their requirements, scope, dependencies, related paths, acceptance criteria, or
other definition content changes.

Completion and acceptance checkbox state is the only lifecycle state stored in
a definition file. Checking an unchanged criterion does not require an
`updated` timestamp change; changing its wording or meaning does.

## Statuses

Use only these values in plan progress frontmatter:

- `not-started`: No implementation work has begun.
- `in-progress`: Work is actively underway.
- `blocked`: Work cannot continue until a recorded blocker is resolved.
- `completed`: Acceptance and completion criteria are satisfied and validation
  is recorded.

Task progress also allows:

- `ready-for-review`: Implementation and focused validation are complete, and
  final review is the next action.
- `needs-fix`: An evidence-backed review has actionable findings that require a
  fresh implementation pass.

The task-level `PROGRESS.md` is the source of truth for detailed task state. The
plan-level `PROGRESS.md` summarizes task statuses and the overall plan state.
Keep both synchronized after a task status changes.

Keep `current_tasks` limited to tasks whose status is `in-progress`.
`ready-for-review`, `needs-fix`, and `blocked` tasks remain actionable through
their plan-level `Next Actions` rows but are not current implementation work.

A task is actionable only after every task ID in `depends_on` is `completed`.
Dependencies must reference other tasks in the same plan and must not be
self-referential or cyclic. Unmet dependencies leave a task `not-started`; they
do not by themselves make it `blocked`.

Set the plan to `blocked` when incomplete tasks remain but none can proceed due
to recorded unresolved blockers, including downstream tasks waiting on blocked
tasks. Completed tasks and plans are terminal unless the user explicitly asks
to reopen them. Record the reopening reason, set the item to `in-progress`, and
move a reopened plan from `plans/done/` back to `plans/`.

If reopening a task makes a completed transitive dependent's dependency
incomplete, reset that dependent to `not-started`, record why its prior
completion must be reassessed, and continue through the dependency graph. If
the plan was completed, reopen and move the plan before changing its tasks.

Never renumber or reuse task IDs. New tasks receive the next unused three-digit
sequence after the highest sequence already assigned.

Every task requires a final review. An implementation agent sets a task to
`ready-for-review`; only the orchestrator may set it to `completed` after a
clean review. A review with actionable findings sets it to `needs-fix`. Before
spawning a fresh implementer for the correction pass, the orchestrator sets it
back to `in-progress` and supplies the latest review and review-to-fix handoff.

Keep exactly one plan Tasks-table row for every task folder. Link it to that
task's `TASK.md`, and express `Depends on` as `None` or a comma-separated list
matching the task's `depends_on` frontmatter.

## Explore the Project

During plan creation, the orchestrator must launch explorer subagents before
finalizing the plan and task definitions. Exploration is read-only.

Before launching explorers, resolve the exploration baseline:

- `worktree`: The checkout path relative to the managed project folder.
- `branch`: The branch checked out in that worktree.
- `baseline_commit`: The full commit SHA at `HEAD`, or YAML `null` when the
  repository has no commits.

Give every explorer the same baseline so their findings describe one consistent
repository state. Store the baseline in the plan frontmatter.

Give each explorer a clear area to investigate and ask for:

- A summary of the relevant current implementation or project state.
- Concrete paths to existing files and folders related to the proposed work.
- Probable new files or folders required by the proposed work.
- The expected use of each path: `inspect`, `modify`, or `create`.
- Evidence for each finding and any unresolved uncertainty.
- Relevant files under the managed project's `docs/` folder.
- Applicable installed guidance under `.agents/guides/`.
- Probable project documentation that the work must create or update.

Every explorer must inspect the managed project's `docs/` folder for material
relevant to its investigation area and check `.agents/guides/` for applicable
shared guidance. Read candidate files before treating them as relevant; a
filename alone is not evidence. Report explicitly when a folder is empty or no
relevant documentation or guide exists.

Consolidate the explorer findings before writing the plan. Add the complete set
of probable paths to the plan's `Related Files and Folders` section, then add
the relevant subset to each task's matching section. Preserve supporting
evidence in both tables and record unresolved, non-blocking uncertainty in the
plan's `Open Questions` section.

Use `existing` only for paths verified during exploration. Use `planned` for
paths expected to be created. Do not invent paths. If explorers disagree or a
required path cannot be verified, continue exploring or ask the user.

Record related paths relative to the repository checkout root. Do not use
absolute paths or paths relative to the managed project folder.

In related-path tables, use one path per row, keep `State` to `existing` or
`planned`, and use a comma-separated combination of `inspect`, `modify`, and
`create` for `Expected Use`. Give every row concrete, non-empty relevance and
evidence.

Add relevant documentation and guides to the matching table in `PLAN.md` and
`TASK.md`:

- `project-docs` entries begin with `docs/` and are relative to the managed
  project folder. They may be existing or planned and may use `inspect`,
  `modify`, or `create`. A planned plan-level entry includes `create`; a
  downstream task may use only later operations after another task creates it.
  Existing entries do not use `create`.
- `workspace-guide` entries begin with `.agents/guides/` and are relative to the
  meta-repository root. They must be existing and use only `inspect`.

The plan table contains the complete set. Each task table contains its relevant
subset with matching source and state; task expected-use values must be a
subset of the plan entry. Leave only the table header when no documentation or
guide applies.

If the environment cannot launch explorer subagents, tell the user and ask how
to proceed instead of silently skipping exploration.

## Create a Plan

1. Confirm `plans/<plan-name>/` does not already exist. If it does, ask the user
   whether to resume it or choose another name; do not overwrite it.
2. Begin the new-plan clarification process. Launch explorer subagents as soon
   as factual prerequisites become clear, while continuing with unrelated
   frontier questions.
3. Consolidate all explorer findings about the current project state, probable
   related paths, relevant project documentation, and applicable workspace
   guides.
4. Recompute the decision frontier from those findings and continue asking the
   user until every required decision is settled.
5. Summarize the resulting plan and task breakdown and obtain the user's
   confirmation of the shared understanding.
6. Record a planned worktree, branch, final review, intermediate high-risk
   checkpoints, and ADR decision for every task.
7. Create the plan folder, plan-level `handoffs/`, `tasks/`, `PLAN.md`, and the
   plan-level `PROGRESS.md`.
8. Fill the plan templates with the exploration baseline, approval time,
   agreed goal, scope, approach, dependencies, related paths, documentation and
   guide references, evidence, open questions, architecture decisions, task
   index, and completion criteria.
9. Create one numbered folder and `handoffs/` directory per task and fill its
   `TASK.md` and `PROGRESS.md` templates.
10. Persist accepted explorer handoff payloads under the plan-level `handoffs/`
    directory and set `latest_handoff` in plan progress.
11. Initialize the plan and every task with `status: not-started`.
12. Leave `current_tasks` empty while all tasks are `not-started`, and list each
   immediately actionable task under `Next Actions`.
13. After approval, use the worktree-management skill to create worktrees for
    immediately actionable tasks. Create dependent worktrees only when their
    dependencies complete.
14. Run `scripts/validate_plan.py <path-to-plan>` and resolve every error.

## Resume or Update Work

1. Read the plan definition and progress files, then every current task's
   definition and progress files.
2. Verify that recorded state agrees with observable work before changing it.
3. Update the task progress after meaningful checkpoints and before handing
   work to another agent.
4. Record concise completed work, decisions, changed files, validation,
   blockers, and one exact next action.
5. Report the checkpoint to the orchestrator. The orchestrator updates the plan
   progress whenever the set of active tasks, a task status, a blocker, or a
   next action changes.

The orchestrator is the sole writer of the plan-level `PROGRESS.md`. Task
agents write only their own task-level `PROGRESS.md`. The orchestrator
serializes task reports into the shared plan progress file so parallel agents
do not overwrite one another.

Tasks may run in parallel when their dependencies are satisfied. List every
`in-progress` task in `current_tasks`, and keep a separate next action in each
task's progress file.

The plan-level `Next Actions` table lists every `in-progress` task and every
`not-started` task whose dependencies are complete. It also lists every
`ready-for-review` task with its review action, every `needs-fix` task with its
fix assignment, and every `blocked` task with its blocker-resolution or waiting
action. Use the literal `plan` for a remaining plan-level action after all tasks
complete. Completed plans have no next-action rows. Keep only unresolved
blockers in `Blockers`, use `None.` when there are none, and use `None.` as a
completed task's next action. Keep one plan-level `Task Status` row per task,
synchronized with task progress and carrying a concise result-or-blocker
summary.

Before starting a task, use its planned assignment to create and record its
actual worktree and branch in task progress. Update `head_commit`,
`uncommitted_changes`, `latest_handoff`, and `latest_review` at meaningful
checkpoints and before handoff. Parallel tasks must use separate Git worktrees
and branches; do not let parallel agents edit the same checkout.

If requirements or scope change, update the appropriate definition file and
its `updated` timestamp, then record the change in its progress file. Run
`scripts/validate_plan.py <path-to-plan>` after structural or state changes.

## Complete a Task

An implementer never completes a task directly. It sets the task to
`ready-for-review`, creates an implementation handoff, and returns control to
the orchestrator.

Set a task to `completed` only after its acceptance criteria are satisfied, its
required validation has passed or the user has explicitly accepted a documented
exception, and its final review is clean. Mark every satisfied or explicitly
accepted acceptance criterion as checked. Record the review path, outcome, and
validation, set its next action to `None.`, and update plan progress before
selecting the next actionable task or tasks.

A final review with actionable findings sets the task to `needs-fix`. Persist
the review and reviewer handoff, then spawn a fresh implementer with only the
task, latest implementation handoff, accepted findings, and required context.

## Complete a Plan

Set a plan to `completed` only when all required tasks are complete, the plan's
completion criteria are satisfied, and no unresolved blocker prevents
completion.

Every ADR marked required in the approved plan must exist under `docs/adrs/`
and reflect the accepted decision before completion. Reports are required only
when the approved plan explicitly lists one as a deliverable.

Mark satisfied completion criteria as checked. If all tasks are complete while
any plan criterion remains unchecked, keep the plan `in-progress` and add a
`plan` row to `Next Actions`. Set the plan to `completed` only after every
criterion is checked.

Record the final outcome in the plan-level `PROGRESS.md`, then move the complete
plan folder to `plans/done/<plan-name>/`. If that destination already exists,
stop and ask the user instead of merging or overwriting it.

Run `scripts/validate_plan.py <path-to-plan>` before moving the plan and again
against its final path under `plans/done/`.
