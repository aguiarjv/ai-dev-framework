---
name: workflow-handoff
description: Create or consume compact, evidence-backed agent handoffs and results without losing task scope, assumptions, verification state, or review context.
---

# Workflow Handoff

Use this skill whenever work moves between explorer, architect, planner, implementer, debugger, or reviewer agents.

## Handoff Rules

- Read the task spec, task contract, workflow state, progress file, and named ADRs before acting.
- Give every delegation an `H-n` ID and every result an `R-n` ID.
- Pass artifact paths and source revision alongside summaries so downstream agents can recover context without trusting an incomplete paraphrase.
- Separate confirmed facts with evidence from assumptions, decisions, constraints, and unresolved questions.
- State the exact subtask scope, acceptance-criteria IDs, dependencies, verification commands, required output, and do-not-change boundaries.
- Return changed files, acceptance-criteria evidence, verification status, blockers, residual risks, and a next action.

Use `.ai/templates/handoff.md` and `.ai/templates/agent-result.md` for the durable artifact shape. Do not mark a criterion or command as complete without evidence.
