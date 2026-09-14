---
id: "<task-id>"
plan: "<plan-name>"
title: "<task-title>"
created: "<YYYY-MM-DD>"
updated: "<YYYY-MM-DDTHH:MM:SSZ>"
depends_on: []
planned_worktree: "worktrees/<plan-name>-<task-id>"
planned_branch: "task/<plan-name>/<task-id>"
review_required: true
---

# <Task Title>

## Objective

<Describe the result this task must produce.>

## Requirements

- <Requirement>

## Related Files and Folders

| Path | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- |
| `<repository-relative-path>` | `existing` or `planned` | `inspect`, `modify`, or `create` | <Why this path is related to this task> | <Explorer evidence supporting this entry> |

## Relevant Documentation and Guides

| Path | Source | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- | --- |
| `docs/<documentation-path>` | `project-docs` | `existing` or `planned` | `inspect`, `modify`, or `create` | <How this document informs this task> | <Explorer evidence supporting this entry> |
| `.agents/guides/<guide-path>` | `workspace-guide` | `existing` | `inspect` | <How this guide informs this task> | <Explorer evidence supporting this entry> |

## Acceptance Criteria

- [ ] <Observable condition required for completion>

## Validation

- <Command, check, or review needed to validate this task>

## Review Checkpoints

- Final review after implementation is ready.
- <Additional high-risk checkpoint or `None`>
