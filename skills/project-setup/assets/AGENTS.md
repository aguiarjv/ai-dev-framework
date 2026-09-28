# <Project Name>

This folder is a managed project inside an AI Dev Framework meta repository.
The primary agent follows the meta-repository workspace instructions and acts
as the orchestrator.

## Project Paths

All paths below are relative to this managed project folder. Workspace folders
store coordination files outside the repository checkouts in `worktrees/`.

- Repository checkout: `worktrees/<default-branch-name>/`
- Project documentation: `workspace-docs/`
- Architecture decisions: `workspace-docs/adrs/`
- Active and completed plans: `workspace-plans/`
- Project workspace scripts: `workspace-scripts/`
- Review artifacts: `workspace-reviews/`
- Optional reports: `workspace-reports/`

## Working Rules

- Read the instructions inside the applicable repository checkout before
  assigning or changing repository work.
- Keep plans, handoffs, reviews, reports, project documentation, and workspace
  helper scripts in this managed project, not inside another project.
- Use an orchestrator-owned plan integration worktree and a separate worktree
  and branch for every active implementation task.
- Treat task `PROGRESS.md` as the task-state source of truth and plan
  `PROGRESS.md` as the orchestrator-owned summary.
- Do not guess missing product, scope, architecture, or integration decisions.
- An approved plan authorizes only its recorded task-to-plan integrations. Do
  not deliver the plan branch, otherwise merge or rebase, push, remove a
  worktree, or delete a branch unless the user or an applicable repository
  policy authorizes it.
