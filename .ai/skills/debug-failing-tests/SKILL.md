---
name: debug-failing-tests
description: Diagnose failing tests, builds, CI failures, flaky behavior, or runtime logs. Use when Codex needs to reproduce a failure, isolate root cause, summarize logs, identify the smallest fix, or verify that a test/build failure is resolved.
---

# Debug Failing Tests

## Workflow

1. Capture the failing command, exit code, environment clues, and first relevant error.
2. Reproduce narrowly when possible. Avoid broad retries before understanding the failure.
3. Inspect the failing test, implementation, fixtures, config, and recent changes.
4. Separate symptom from root cause.
5. Prefer the smallest fix that addresses the root cause without weakening the test.
6. Re-run the failing command or the narrowest equivalent verification.

## Log Summaries

For long logs, run:

```bash
python3 .ai/skills/debug-failing-tests/scripts/summarize-test-log.py path/to/log.txt
```

Use the summary to navigate; still inspect source files before changing behavior.

Read `references/triage.md` when the failure has multiple plausible causes.
