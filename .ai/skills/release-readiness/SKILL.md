---
name: release-readiness
description: Run a pre-release readiness check for code, configuration, migrations, documentation, tests, monitoring, rollback, and user-facing behavior. Use before shipping a feature, deploying a service, merging a risky change, or cutting a release.
---

# Release Readiness

## Workflow

1. Identify what is being released and the user-visible or operational surface area.
2. Check tests, build, lint, migrations, configuration, docs, feature flags, and compatibility.
3. Inspect failure and rollback paths for risky changes.
4. Confirm observability or logging exists where operational diagnosis will be needed.
5. Produce a concise readiness report with blockers first.

## Output

Use:

```markdown
Blockers:

Risks:

Verification:

Rollback:

Notes:
```

Read `references/release-checklist.md` for complex releases.
