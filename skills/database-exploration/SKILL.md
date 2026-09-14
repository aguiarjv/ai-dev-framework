---
name: database-exploration
description: Safely gather schema, query, and bounded data facts from a live database through a verified read-only connection.
---

# Database Exploration

Use this skill inside a `database-explorer` agent and follow the
[Database Exploration guide](../../guides/database-exploration.md).

## Preconditions

Require the orchestrator to provide the environment, investigation question,
allowed scope, and a read-only connection or tool. Verify the access mode before
querying. If it cannot be verified, return a blocked handoff payload.

## Explore

- Prefer catalogs, metadata, constraints, indexes, query plans, aggregates, and
  bounded samples.
- Select only necessary columns and limit all samples.
- Avoid expensive scans and disruptive locks.
- Never run mutations, DDL, migrations, grants, maintenance operations, or
  unknown stored procedures.
- Never return credentials, secrets, tokens, personal data, or raw data dumps.
- Separate observed database facts from application inferences.

## Return

Return a complete plan- or task-level handoff payload. Include safe reproduction
details, schema objects, relationships, constraints, representative aggregate
characteristics, query evidence, limitations, uncertainty, relevant repository
paths, and one exact recommended next action. Do not write files from the
read-only agent; the orchestrator persists the payload.
