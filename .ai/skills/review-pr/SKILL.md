---
name: review-pr
description: Perform rigorous code review of diffs, branches, pull requests, or changed files. Use when Codex should find bugs, regressions, security risks, data-loss risks, compatibility issues, or missing tests instead of implementing changes.
---

# Review PR

## Workflow

1. Identify the diff and changed behavioral surface.
2. Read nearby implementation, tests, schemas, configs, and public interfaces affected by the change.
3. Look for concrete failures: incorrect logic, broken contracts, missed edge cases, security/privacy issues, migrations, concurrency, performance, and missing tests.
4. Prioritize confirmed findings. Avoid style-only comments unless they block maintainability or correctness.
5. Report findings first, ordered by severity, with file and line references.

## Output

Use this shape:

```markdown
Findings:
- Severity - path:line - issue and impact.

Open questions:
- Question or assumption.

Residual risk:
- Tests not run or areas not inspected.
```

If no issues are found, state that clearly and mention residual risk. Read `references/review-checklist.md` for broad or high-risk reviews.
