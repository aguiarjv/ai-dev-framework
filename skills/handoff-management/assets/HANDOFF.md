---
id: "<handoff-id>"
plan: "<plan-id>"
task: null
from_role: "<sender-role>"
to_role: "<recipient-role>"
created: "<YYYY-MM-DDTHH:MM:SSZ>"
outcome: "<completed|checkpoint|changes-requested|blocked>"
worktree: "<worktrees/worktree-folder-or-null>"
branch: "<branch-name-or-null>"
head_commit: "<full-commit-sha-or-null>"
---

# Handoff: <Handoff Title>

## Assignment

<State the bounded assignment and its scope.>

## Work Completed

- <Completed work or `None`>

## Files

- `<path>` - <inspected, created, or changed and why>

## Validation

- <Command or check and result, or `Not run` with reason>

## Decisions

- <Settled decision or `None`>

## Findings and Blockers

- <Finding, blocker, uncertainty, or `None`>

## Required Context

- <Plan, task, review, ADR, documentation, or guide path needed next>

## Next Action

<One exact action for the recipient.>
