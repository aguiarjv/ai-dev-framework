# Architecture Decision Records

Use architecture decision records for durable decisions that materially affect
system structure, interfaces, data ownership, security boundaries, deployment,
or long-term technical constraints.

Do not require an ADR for routine implementation choices or bug fixes that do
not establish a durable architectural decision. A plan that needs no ADR should
record `No ADR required` with a concise rationale.

## Structure and Naming

Store ADRs in the managed project's documentation area:

```text
projects/
  <project-name>/
    docs/
      adrs/
        0001-<decision-title>.md
```

Use the next unused four-digit sequence and a descriptive kebab-case title.
Never renumber an existing ADR or reuse its number. Before creating an ADR,
check for an existing record of the same decision and update or supersede it
instead of creating a duplicate.

## When to Create an ADR

During planning, identify candidate architectural decisions and ask the user
whether each decision should be accepted. For every accepted decision that
meets the ADR threshold:

- Add the planned ADR path to the plan's documentation table.
- Assign ADR creation or update to an explicit task.
- Complete the ADR before the plan is completed.

Implementation may expose a new architectural decision. Stop work that depends
on that decision, return it to the user through the orchestrator, and update the
plan after the decision is made. Do not let an implementation agent silently
turn a local choice into project architecture.

## Required Contents

Start from `.agents/skills/adr-management/assets/ADR.md`. Record:

- The title, date, status, decision owners, and related plan or task.
- The context and forces that made the decision necessary.
- The options considered and their material tradeoffs.
- The accepted decision.
- Positive and negative consequences.
- Implementation and validation implications.
- Links to ADRs that this decision supersedes or depends on.

Use `proposed`, `accepted`, `superseded`, or `deprecated` for ADR status. Do not
edit an accepted ADR to make history appear different. Record later changes in
a new ADR and mark the old record as superseded when appropriate.

## Workflow

1. Verify that the decision is architectural and not already documented.
2. Gather relevant plans, tasks, code evidence, project documentation, and
   installed guidance.
3. Present unresolved options and tradeoffs to the user; do not guess the
   decision.
4. Create the ADR after the user accepts the decision.
5. Link the ADR from the plan and applicable task.
6. Validate that the implementation and tests reflect the accepted decision.
