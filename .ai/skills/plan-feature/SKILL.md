---
name: plan-feature
description: Convert rough feature requests, bug-fix ideas, refactors, migrations, or product changes into decision-complete implementation plans. Use when the user wants planning, design, sequencing, acceptance criteria, or a handoff plan before code changes.
---

# Plan Feature

## Workflow

1. Ground the plan in repository facts. Read relevant code, configs, schemas, routes, tests, and docs before asking questions.
2. Separate discoverable facts from product preferences. Ask only for decisions that materially change implementation.
3. Define success criteria, in-scope behavior, out-of-scope behavior, constraints, and compatibility requirements.
4. Specify the implementation approach at the interface and data-flow level.
5. Include edge cases, failure modes, migrations, test coverage, and verification commands.
6. Keep the final plan decision-complete. The implementer should not need to choose APIs, file locations, or behavior.

## Final Plan Shape

Use this compact structure unless the task requires more detail:

```markdown
# Title

## Summary

## Key Changes

## Interfaces

## Test Plan

## Assumptions
```

Read `references/planning-checklist.md` when the requested change crosses multiple subsystems or has ambiguous product behavior.
