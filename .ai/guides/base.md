# Project AI Guidance

Use this guidance for routine development in this project.

## Default Orchestration

- Treat the main chat as the `orchestrator` for new tasks.
- The orchestrator may answer simple questions directly, but should delegate non-trivial repository work to specialist agents.
- For new development tasks, clarify intent first, then create or update `docs/tasks/<task-slug>.md` before implementation.
- For non-trivial or unclear implementation tasks, call `explorer` before finalizing the task spec to map relevant code, tests, configs, commands, conventions, risks, and relevant ADRs.
- Before approval, the task spec must include repository context, acceptance criteria, a concise implementation plan, and classified tasks or subtasks.
- Do not begin implementation, run formatters, or make code changes until the task spec is explicitly approved by the user.
- After approval and before code-changing implementation, remediation, or debugging, create or reuse a dedicated git worktree for the task.
- Use `../<repo>-worktrees/<task-slug>` as the default worktree path and `ai/<task-slug>` as the default branch.
- If the task branch or worktree already exists, inspect it and reuse it only when it matches the active task; report conflicts instead of overwriting or deleting existing worktrees.
- Record the task worktree path and branch in `docs/tasks/<task-slug>.md`, `.local/tasks/<task-slug>/progress.md`, and implementation, review, and debugging handoffs.
- Keep current task progress in `.local/tasks/<task-slug>/progress.md`; `.local/` must remain gitignored.
- Record exploration findings and handoffs in `.local/tasks/<task-slug>/progress.md` as working state.
- Add durable decisions and important implementation context to `docs/adr/<YYYY-MM-DD>-<task-slug>.md`.
- Only `explorer` should perform broad ADR discovery. Other agents should use ADR summaries and named ADR references from the task spec, progress file, or handoff, and should not scan all ADRs as routine context.
- Before planning, implementing, reviewing, or debugging an active task, read the relevant `docs/tasks/<task-slug>.md`.
- When creating tasks or subtasks, classify each item as `frontend`, `backend`, `full-stack`, `docs`, `test`, or `infra`.
- For frontend or full-stack UI work, read `.ai/guides/frontend.md` and apply it.
- For backend or full-stack server/API/data work, read `.ai/guides/backend.md` and apply it.
- During implementation and debugging, update `.local/tasks/<task-slug>/progress.md` with current state, handoffs, verification, and review-loop status.
- When architecture choices, durable tradeoffs, testing strategy, or important implementation outcomes emerge, create or update the relevant `docs/adr/<YYYY-MM-DD>-<task-slug>.md`.
- Before testing, reviewing, or debugging, read `.ai/harnesses/registry.md` and prefer registered harnesses over ad hoc commands.
- Keep delegation centralized. Worker agents should not spawn other agents; the orchestrator owns the chain.
- Use compact handoffs that include only the goal, relevant paths, constraints, prior conclusions, acceptance criteria, and required output.
- Implementation, review, and debugging agents must operate from the assigned task worktree when one is expected.
- After any implementation, always run `reviewer`.
- If `reviewer` returns actionable findings, run `planner` to create a remediation plan, then run `implementer`, then run `reviewer` again.
- Stop the review loop after a clean review, explicit user stop, or two remediation cycles. Report unresolved findings if the loop stops before clean review.
- After a clean review, inspect `git status --short` from the task worktree, summarize the task-owned changes, suggest a Conventional Commits message such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, or `chore:`, and ask the user whether they want those changes committed.
- Do not commit without explicit user approval. If approved, stage only files that belong to the completed task; leave unrelated, pre-existing, or user-owned changes unstaged unless the user explicitly includes them.

## Operating Principles

- Read the relevant code, tests, configs, schemas, and existing patterns before changing behavior.
- Prefer the project's current architecture and conventions over new abstractions.
- Keep edits scoped to the requested behavior and the directly necessary supporting code.
- Preserve user changes. Do not revert unrelated work or clean up files outside the task without explicit approval.
- Use primary documentation for unstable external APIs, libraries, product behavior, pricing, rules, or current facts.

## Implementation Discipline

- State assumptions when they affect implementation.
- Make the smallest coherent change that solves the user-visible problem.
- Add or update tests when behavior, contracts, or regressions are involved.
- Run the narrowest useful verification first, then broader checks when the change has wider blast radius.
- If a command fails, diagnose the failure before retrying or changing code.

## Review Discipline

- For reviews, lead with bugs, regressions, security risks, data loss risks, and missing tests.
- Reference files and lines whenever possible.
- Separate confirmed issues from questions or assumptions.

## Frontend Discipline

- Build the real usable interface as the first screen for apps and tools.
- Keep UI dense, clear, and domain-appropriate.
- Verify responsive behavior and obvious visual overlap before finishing.

## Completion Standard

Finish with a concise summary of what changed and what was verified. Call out checks that could not be run. When the work is ready after review, include the commit checkpoint with the intended scoped files and a suggested Conventional Commits message.
