# Review Checklist

Check for:

- Acceptance-criteria coverage: every `AC-n` maps to implementation and verification evidence.
- Intent mismatch: implementation does not satisfy the PR description, task spec, acceptance criteria, docs, or changed tests.
- User-visible behavior regressions, including empty/loading/error states and accessibility regressions for UI changes.
- Public API, schema, type, route, CLI, config, file format, or event contract breaks.
- Backward compatibility gaps, missing migration paths, version skew, or unannounced behavior changes.
- Incorrect validation, authentication, authorization, tenancy, ownership, or feature-flag assumptions.
- Privacy and secret-handling issues, including sensitive logging, unsafe error messages, and over-broad telemetry.
- Injection, unsafe deserialization, path traversal, SSRF, XSS, CSRF, command execution, and dependency trust risks.
- Data loss, duplicate writes, partial writes, unsafe migrations, rollback hazards, or inconsistent read/write models.
- Race conditions, retries, idempotency gaps, locking issues, async ordering bugs, and timeout/cancellation problems.
- Error handling that hides failures, retries impossible operations, swallows partial failure, or leaks sensitive data.
- Performance regressions on hot paths, large inputs, N+1 queries, unnecessary network calls, unbounded memory use, missing pagination, or cache invalidation mistakes.
- Test gaps for changed behavior, security boundaries, migrations, failure paths, integration contracts, and previous bug classes.
- Documentation or ADR drift when a durable decision, compatibility contract, migration behavior, or testing strategy changes.
- Harness gaps: missing or ignored registered validation for the changed behavior.
- Handoff/result gaps: missing `H-n` or `R-n` artifacts, unsupported claims, or stale source revisions.

Severity guide:

- Critical: exploitable security issue, data loss/corruption, or release-blocking outage risk.
- High: likely user-visible regression, broken contract, privilege/tenant boundary risk, unsafe migration, or severe performance regression.
- Medium: edge-case correctness issue, incomplete compatibility, meaningful missing test, or recoverable operational risk.
- Low: minor maintainability concern that can plausibly cause future defects.

Every actionable finding should have an `F-n` ID, confidence, location, impacted criterion IDs, evidence, required fix, and verification step.
