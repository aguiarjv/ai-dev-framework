# Database Exploration

Use repository exploration for schemas, migrations, query code, and database
configuration stored in the checkout. Use the `database-explorer` agent only
when a plan or task needs facts from a live database.

## Access Boundary

Connect only through a database principal, connection, or tool explicitly
supplied for read-only exploration. If read-only access cannot be verified,
stop and report the limitation instead of connecting.

Do not execute mutations, migrations, DDL, grants, maintenance operations,
stored procedures with unknown effects, write-capable transaction statements,
or commands that acquire disruptive locks. Do not use a production database
for load testing or broad scans.

## Data Minimization

- Prefer catalogs, metadata, query plans, counts, and bounded samples.
- Select only columns needed for the investigation.
- Apply restrictive filters and row limits to samples.
- Do not return credentials, tokens, personal data, secrets, or complete data
  dumps in chat or handoffs.
- Summarize sensitive values and redact any incidental exposure.

Avoid expensive queries. Use a non-executing query plan when available. Run an
executing plan only when the query is verified read-only, its cost is bounded,
and the assignment explicitly requires it.

## Evidence

Record the database engine and environment, the read-only access mechanism,
the exploration time, and enough query text or catalog references to reproduce
the finding safely. Distinguish observed database facts from inferences about
application behavior.

Return a structured handoff to the orchestrator. The handoff should summarize
schema objects, relationships, constraints, representative data characteristics,
query evidence, uncertainty, and any repository paths that should be inspected.
The database explorer remains read-only and does not write the handoff file.
