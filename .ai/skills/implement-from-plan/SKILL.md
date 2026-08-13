---
name: implement-from-plan
description: Execute an accepted implementation plan in a codebase with disciplined scope control, preservation of user changes, tests, and verification. Use when Codex has a concrete plan or checklist and should make code, config, documentation, or test changes.
---

# Implement From Plan

## Workflow

1. Read the plan and identify required behavior, files, tests, and constraints.
2. Inspect the current repository state before editing. Treat existing uncommitted changes as user work unless proven otherwise.
3. Make changes in the smallest coherent sequence. Prefer existing local patterns and helper APIs.
4. Add or update tests when behavior, contracts, or regressions are involved.
5. Run focused verification first. Run broader checks when shared behavior or public interfaces changed.
6. Summarize changed behavior, files touched, verification run, and any remaining risk.

## Guardrails

- Do not silently broaden scope.
- Do not revert unrelated changes.
- Do not overwrite project-specific configuration without evidence that it is generated or framework-owned.
- Do not finish after only editing files when reasonable verification is available.

Read `references/change-discipline.md` for larger or riskier changes.
