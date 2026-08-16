---
name: review-pr
description: Perform rigorous code review of diffs, branches, pull requests, or changed files with intent reconstruction, related docs/ADR analysis, security/performance/test scrutiny, and comment-ready findings. Use when Codex should review a PR or change set, create a review handoff report, or find bugs, regressions, security risks, data-loss risks, compatibility issues, edge cases, or missing tests instead of implementing changes.
---

# Review PR

## Workflow

1. Identify the review target: PR metadata when available, compared branches, commits, changed files, task spec, or explicit diff.
2. Reconstruct the intended behavior before judging the code. Use the PR title/body, commit messages, task spec, acceptance criteria, tests, docs, and changed public interfaces.
3. Read relevant context:
   - For approved framework tasks, use the task spec, progress file, handoff, and named ADRs.
   - For standalone PR reviews, inspect nearby docs and do targeted ADR discovery from changed paths, component names, domains, schemas, APIs, migrations, or config names. Do not deep-read every ADR by default.
   - Read nearby implementation, tests, schemas, configs, routes, public interfaces, and harness registry entries affected by the change.
4. Review the change against intent and surrounding contracts. Look for incorrect behavior, broken contracts, missed edge cases, security/privacy issues, auth/authorization gaps, data loss, migrations, concurrency, performance, and meaningful missing tests.
5. For broad or high-risk reviews, ask the orchestrator to split focused read-only sub-reviews and synthesize their compact handoffs. Useful review slices include security/data, performance, test coverage, frontend/backend behavior, and docs/ADR consistency.
6. Prioritize confirmed findings. Avoid style-only comments unless they affect correctness, safety, compatibility, or maintainability.
7. Produce a comment-ready report with findings first, ordered by severity, with file and line references.

## Output

Use this shape:

```markdown
Review status: clean | actionable-findings | blocked
Intent understood:
Scope reviewed:
Docs and ADRs checked:
Findings:
- Severity - path:line - issue, impact, and concrete fix.
Required fixes:
Test gaps:
Sub-review handoffs:
Comment-ready findings:
- path:line - concise PR-comment-ready finding with severity and fix.
Open questions:
Residual risk:
```

Use these severity labels:

```markdown
Critical - exploitable security issue, data loss/corruption, or release-blocking outage risk.
High - likely user-visible regression, broken contract, privilege/tenant boundary risk, unsafe migration, or severe performance regression.
Medium - edge-case correctness issue, incomplete compatibility, meaningful missing test for changed behavior, or recoverable operational risk.
Low - minor maintainability concern that can plausibly cause future defects.
```

Each actionable finding must be specific enough for an implementer to fix without redoing the whole review. Include a concrete file/line when available; use the nearest changed or affected line when the exact root cause spans multiple files.

If no issues are found, state that clearly and mention residual risk. Read `references/review-checklist.md` for broad or high-risk reviews.
