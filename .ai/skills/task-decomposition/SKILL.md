---
name: task-decomposition
description: Turn an approved goal into a dependency-aware task graph with stable acceptance criteria, scoped subtasks, ownership, verification, and safe parallelization decisions.
---

# Task Decomposition

Use this skill when a task needs multiple agents, implementation phases, cross-cutting changes, or a remediation plan.

## Workflow

1. Read the task spec, repository exploration, named ADRs, and applicable domain guides.
2. Define observable `AC-n` acceptance criteria before creating subtasks.
3. Split the work into independently verifiable vertical slices. Give every slice a `T-n` ID, one owner, explicit paths, dependencies, verification, and a `done_when` condition.
4. Mark a slice `parallelizable` only when its files, interfaces, and generated outputs do not overlap with another ready slice. Add an integration checkpoint when parallel work must converge.
5. Update `.local/tasks/<task-slug>/workflow.json` and mirror the graph in the human-readable task spec.
6. Validate that every acceptance criterion is covered by at least one subtask and that the dependency graph has no unknown nodes or cycles.

## Output

Return the task graph, dependency order, parallelization decisions, acceptance-criteria mapping, verification plan, risks, and any missing decision that blocks dispatch.

Read [references/decomposition-checklist.md](references/decomposition-checklist.md) for larger or cross-subsystem work.
