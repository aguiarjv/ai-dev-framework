---
name: adr-management
description: Decide when an architecture decision record is required and create or supersede ADRs under a managed project's docs/adrs directory.
---

# ADR Management

Follow the [Architecture Decision Records guide](../../guides/adr-management.md)
and start new records from `assets/ADR.md`.

## Determine the Need

Create an ADR only for a durable decision affecting architecture, interfaces,
data ownership, security boundaries, deployment, or long-term technical
constraints. During planning, present the decision and material alternatives to
the user. Do not infer acceptance from an implementation preference.

If no ADR is required, record `No ADR required` and the agreed rationale in the
plan. If an architectural decision emerges during implementation, pause work
that depends on it and return the choice to the orchestrator and user.

## Create an ADR

1. Search `docs/adrs/` and relevant documentation for an existing record of the
   decision.
2. Select the next unused four-digit sequence and a kebab-case filename.
3. Fill every field and section in `assets/ADR.md` after the user accepts the
   decision.
4. Write the record to `docs/adrs/<NNNN>-<decision-title>.md` relative to the
   managed project folder.
5. Link it from the plan and applicable task documentation tables.
6. Validate that implementation and tests match the accepted decision before
   plan completion.

Never renumber or overwrite an existing ADR. Supersede an accepted ADR with a
new record and update the old record's status and superseding link without
rewriting its historical decision.
