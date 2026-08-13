---
name: create-harness
description: Create, update, validate, and register project validation harness scripts. Use when Codex needs to add a repeatable test/review/debug command, standardize ad hoc verification, create a local or CI-safe harness script, or update the harness registry used by reviewer, tester, implementer, and debugger agents.
---

# Create Harness

## Workflow

1. Read `.ai/harnesses/registry.md` to check existing harnesses.
2. Ask focused questions only when the harness purpose, target behavior, command safety, required inputs, or success/failure signal is unclear.
3. Create or update `.ai/harnesses/scripts/<harness-slug>.sh` using `.ai/templates/harness-script.sh` as the baseline.
4. Keep the script deterministic, self-documenting, and safe for local execution. Support `--help`; support `--dry-run` when the real harness is expensive or mutating.
5. Validate the harness with the narrowest safe command, usually `--help`, `--dry-run`, or a fixture/sample invocation.
6. Add or update the matching entry in `.ai/harnesses/registry.md` using `.ai/templates/harness-entry.md`.
7. Update `.local/tasks/<task-slug>/progress.md` when this skill is used during an active task.
8. Add an ADR only when the harness encodes a durable project testing strategy or non-obvious validation decision.

## Required Questions

Ask only for unknowns that cannot be discovered from the repository:

- What behavior or workflow should the harness validate?
- Which files, packages, services, or fixtures are in scope?
- What command should count as success?
- What failure mode should the harness catch?
- Is the harness safe for local execution and CI?
- Are external services, credentials, network, databases, or generated artifacts involved?

## Registry Contract

Every registry entry must include:

```markdown
### <harness-name>

Purpose:
Applies to:
Command:
Working directory:
Inputs:
Expected success:
Expected failure:
Maintenance notes:
```

## Script Rules

- Use `#!/usr/bin/env bash` and `set -euo pipefail` for shell harnesses.
- Prefer project-standard package manager commands and existing test entrypoints.
- Avoid destructive cleanup unless explicitly requested and documented.
- Avoid network, production services, and credential-dependent flows unless the registry entry clearly states the prerequisite.
- Print enough context for reviewer and debugger agents to understand failures.
- Exit non-zero when validation fails.

Read `references/harness-authoring.md` when the harness has external dependencies, mutating behavior, multiple modes, or CI/local differences.
