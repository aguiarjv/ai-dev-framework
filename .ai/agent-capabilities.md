# Agent Capability Registry

Use this registry to route work deliberately. The orchestrator owns delegation; workers do not spawn other agents.

| Agent | Use when | Skills | Required context | Required output |
| --- | --- | --- | --- | --- |
| `orchestrator` | Any non-trivial task, delegation, review loop, or final synthesis | `task-decomposition`, `workflow-handoff`, `plan-feature`, `review-pr`, `release-readiness`, `todo-list` | User intent, task spec, workflow contract, workflow state, progress | Phase transition, handoff IDs, result/review synthesis, final status |
| `explorer` | Repository or subsystem facts are unknown or non-trivial | `repo-onboarding`, `workflow-handoff` | User goal, relevant paths, current revision | Evidence-backed repository map and unresolved questions |
| `architect` | Cross-system design, migrations, public interfaces, or risky tradeoffs | `workflow-handoff` | Task spec, named ADRs, exploration findings, applicable guides | Decision-complete architecture and ADR-ready content |
| `planner` | A task needs implementation sequencing or review remediation | `task-decomposition`, `plan-feature`, `workflow-handoff` | Approved task contract, current state, architect/reviewer output | `T-n` graph updates, dependencies, acceptance mapping, verification |
| `implementer` | One ready subtask is approved for code or documentation changes | `implement-from-plan`, `workflow-handoff`, `create-harness` | `H-n` handoff, task contract, worktree, applicable guides | `R-n` result, changed files, evidence, risks, review scope |
| `reviewer` | Any implementation or remediation needs independent quality review | `review-pr`, `workflow-handoff`, `playwright-visual-review` | Task contract, diff, `R-n` result, acceptance criteria, harness registry | Coverage matrix, `F-n` findings, severity, residual risk, review status |
| `test-debugger` | A required check fails or behavior is flaky | `debug-failing-tests`, `workflow-handoff`, `create-harness` | Failure command/log, task state, worktree, recent result | Root cause, fix or blocker, verification, updated result |
| `docs-researcher` | Unstable external API, framework, library, or product behavior needs primary-source research | `workflow-handoff` | Exact question, version/context, relevant interface | Cited facts, constraints, uncertainty |

## Routing Rules

- Load a skill when its “Use when” condition matches the active phase or risk area; do not load every skill by default.
- Use `task-decomposition` before dispatching more than one implementation subtask.
- Use `workflow-handoff` whenever context crosses an agent boundary.
- Use `review-pr` after every implementation and add focused review slices for high-risk work.
- Use `playwright-visual-review` only for frontend or full-stack UI work with a registered browser harness.
- Use `release-readiness` for a pre-release risk scan and `todo-list` only for lightweight reminders that do not need a task contract.
