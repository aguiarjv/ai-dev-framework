---
name: implement-from-plan
description: Execute an accepted implementation plan in a codebase with disciplined scope control, preservation of user changes, tests, and verification. Use when Codex has a concrete plan or checklist and should make code, config, documentation, or test changes.
---

# Implement From Plan

## Workflow

1. Read the plan and identify required behavior, files, tests, and constraints.
2. Read the task contract and assigned handoff. Confirm the current subtask is ready and its dependencies are complete.
3. Inspect the current repository state before editing. Treat existing uncommitted changes as user work unless proven otherwise.
4. Make changes in the smallest coherent sequence. Prefer existing local patterns and helper APIs.
5. Add or update tests when behavior, contracts, or regressions are involved.
6. Run focused verification first. Run broader checks when shared behavior or public interfaces changed.
7. Return an `R-n` result mapping acceptance criteria to evidence and distinguishing failed, blocked, and unrun checks.

## Guardrails

- Do not silently broaden scope.
- Do not revert unrelated changes.
- Do not overwrite project-specific configuration without evidence that it is generated or framework-owned.
- Do not finish after only editing files when reasonable verification is available.

Read `references/change-discipline.md` for larger or riskier changes.
