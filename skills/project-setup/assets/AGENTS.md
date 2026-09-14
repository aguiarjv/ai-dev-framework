# <Project Name>

This folder is a managed project inside an AI Dev Framework meta repository.
The primary agent follows the meta-repository workspace instructions and acts
as the orchestrator.

## Project Paths

- Repository checkout: `worktrees/<default-branch-name>/`
- Project documentation: `docs/`
- Architecture decisions: `docs/adrs/`
- Active and completed plans: `plans/`
- Review artifacts: `reviews/`
- Optional reports: `reports/`

## Working Rules

- Read the instructions inside the applicable repository checkout before
  assigning or changing repository work.
- Keep plans, handoffs, reviews, reports, and project documentation in this
  managed project, not inside another project.
- Use a separate worktree and branch for every active implementation task.
- Treat task `PROGRESS.md` as the task-state source of truth and plan
  `PROGRESS.md` as the orchestrator-owned summary.
- Do not guess missing product, scope, architecture, or integration decisions.
- Do not merge, rebase, push, remove a worktree, or delete a branch unless the
  user or an applicable repository policy authorizes it.
