---
id: "<review-id>"
title: "<review-title>"
created: "<YYYY-MM-DDTHH:MM:SSZ>"
plan: "<plan-id>"
task: "<task-id>"
review_kind: "<checkpoint|final>"
attempt: "<NNN>"
status: "<clean|actionable-findings|blocked>"
worktree: "worktrees/<worktree-folder>"
branch: "<branch-name>"
head_commit: "<full-commit-sha>"
comparison_base: "<base-ref-or-commit>"
---

# <Review Title>

## Target and Scope

<State the exact target, scope, exclusions, and reviewed head state.>

## Inputs

- Task: `<plan-relative-task-path>`
- Handoff: `<plan-relative-handoff-path>`
- Documentation and guides: <paths or `None`>

## Summary

<State the review result and its primary evidence.>

## Acceptance Criteria Coverage

| Criterion | Result | Evidence |
| --- | --- | --- |
| <criterion> | <pass|fail|not-reviewed> | <evidence> |

## Findings

### <F-001: Finding title or `None`>

- Severity: `<critical|high|medium|low>`
- Confidence: `<confirmed|likely|uncertain>`
- Status: `open`
- Location: `<repository-relative-path:line>`
- Impact: <impact>
- Evidence: <evidence>
- Required fix: <fix or decision>
- Verification: <verification step>

## Validation

- <Command or check and result>

## Unreviewed Areas and Residual Risk

- <Area, risk, or `None`>

## Open Questions

- <Question or `None`>
