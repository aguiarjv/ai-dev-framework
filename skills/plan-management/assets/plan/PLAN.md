---
id: "<plan-name>"
title: "<plan-title>"
created: "<YYYY-MM-DD>"
updated: "<YYYY-MM-DDTHH:MM:SSZ>"
worktree: "worktrees/<worktree-folder>"
branch: "<branch-name>"
baseline_commit: "<full-commit-sha>"
approved_at: "<YYYY-MM-DDTHH:MM:SSZ>"
---

# <Plan Title>

## Goal

<Describe the outcome this plan must achieve.>

## Context

<Describe the relevant background and current situation.>

## Scope

### In Scope

- <Included work>

### Out of Scope

- <Excluded work>

## Approach

<Describe the agreed implementation or investigation approach.>

## Dependencies

- <Dependency or `None`>

## Related Files and Folders

| Path | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- |
| `<repository-relative-path>` | `existing` or `planned` | `inspect`, `modify`, or `create` | <Why this path is related to the plan> | <Explorer evidence supporting this entry> |

## Relevant Documentation and Guides

| Path | Source | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- | --- |
| `docs/<documentation-path>` | `project-docs` | `existing` or `planned` | `inspect`, `modify`, or `create` | <How this document informs the plan> | <Explorer evidence supporting this entry> |
| `.agents/guides/<guide-path>` | `workspace-guide` | `existing` | `inspect` | <How this guide informs the plan> | <Explorer evidence supporting this entry> |

## Open Questions

- <Unresolved non-blocking question or `None`>

## Architecture Decisions

| Decision | ADR Required | Path | Rationale |
| --- | --- | --- | --- |
| <Decision or `No ADR required`> | <yes|no> | <`docs/adrs/NNNN-title.md` or `None`> | <Why an ADR is or is not required> |

## Tasks

| ID | Task | Depends on |
| --- | --- | --- |
| `001-<task-name>` | [<Task title>](tasks/001-<task-name>/TASK.md) | None |

## Completion Criteria

- [ ] <Plan-level completion criterion>
