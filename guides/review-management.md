# Review Management

Use the `reviews/` directory in a managed project for durable results of code,
design, security, documentation, process, and other project reviews.

A review evaluates a defined target against stated expectations and records
findings. Use `reports/` instead when the artifact primarily summarizes facts,
research, status, or analysis without judging a target against review criteria.

## Location and Naming

Create each review as a Markdown file directly inside the applicable managed
project:

```text
projects/
  <project-name>/
    reviews/
      <review-name>.md
```

Use a concise, descriptive, kebab-case filename that identifies the target or
purpose of the review. Do not store a managed project's review in the repository
checkout, another managed project, `docs/`, or `reports/`.

For plan-task reviews, use
`<plan-id>-<task-id>-review-<NNN>.md`, where the sequence is local to that plan
and task. Append a new review for every attempt; never replace earlier evidence.
For a final plan integration review, use
`<plan-id>-integration-review-<NNN>.md`, with a sequence local to that plan.

Before writing, check whether the target path already exists. Do not overwrite
or repurpose an existing review unless the user explicitly asks to update that
review. Ask the user when choosing between updating an existing review and
creating a new one would change the meaning or history of the artifact.

## Required Context

Before reviewing, establish:

- The managed project and repository worktree being reviewed.
- The review target, such as a diff, commit, branch, pull request, design,
  document, workflow, or explicitly named files.
- The review purpose, scope, and exclusions.
- The requirements, acceptance criteria, policies, guides, or other standards
  against which the target will be assessed.
- The relevant repository baseline and comparison point, when applicable.
- The intended audience and any decision the review is expected to inform.

Inspect the environment for facts that can be established from the project,
repository, plan, task, documentation, or installed guides. Ask the user when a
missing choice affects the review target, scope, criteria, severity, or intended
outcome. Do not invent review requirements or silently expand the review.

## Review Baseline

Make the reviewed state reproducible. Record the applicable worktree, branch,
full commit SHA, comparison base, uncommitted-change state, document version,
or other stable identifier available for the target. Use `null` or state that a
value is unavailable rather than fabricating one.

If the target changes during the review, either restart from a clearly recorded
baseline or state which findings apply to which version. Do not present evidence
from different target states as one consistent snapshot.

## Review File Contents

Every review file should contain enough context for another person or agent to
understand the result without reconstructing the review session. Include:

- A title and stable review identifier.
- The creation time and, when updated, the last-update time.
- The review target, purpose, scope, exclusions, and baseline.
- The criteria and sources used to assess the target.
- A short conclusion or overall status.
- Findings ordered by severity, followed by residual risks and open questions.
- The validation or checks performed and any areas that could not be reviewed.

Use these overall results when a compact status is useful:

- `clean`: No actionable findings were identified in the reviewed scope.
- `actionable-findings`: One or more findings require a decision or change.
- `blocked`: The review could not reach a reliable conclusion because required
  access, context, evidence, or a user decision was unavailable.

A clean result does not imply that unreviewed areas are safe. State the reviewed
scope and residual risk explicitly.

## Findings

Give each finding a stable identifier such as `F-001`. Preserve that identifier
when a finding is discussed, remediated, verified, waived, or rejected.

Each actionable finding must record:

- Severity: `critical`, `high`, `medium`, or `low`.
- Confidence: `confirmed`, `likely`, or `uncertain`.
- Status: `open`, `fixed`, `rejected`, or `waived`.
- The affected requirement or acceptance criterion, when one exists.
- A concrete location, such as a repository-relative path and line number.
- The observed behavior or defect and its impact.
- Evidence supporting the finding.
- The required or recommended correction.
- A verification step that can demonstrate resolution.

Use severity to communicate impact, not certainty:

- `critical`: Exploitable security failure, data loss or corruption, or an
  immediate release-blocking outage risk.
- `high`: Likely user-visible regression, broken contract, authorization or
  tenant-boundary failure, unsafe migration, or severe operational risk.
- `medium`: Edge-case correctness issue, incomplete compatibility, meaningful
  missing validation, or recoverable operational risk.
- `low`: Limited-impact defect or maintainability problem with a plausible path
  to future failure.

Do not create findings for personal style preferences unless they cause a
concrete correctness, safety, compatibility, operability, or maintainability
risk. If evidence is incomplete, lower the confidence or record an open
question instead of overstating the conclusion.

## Workflow

1. Resolve the review target, scope, criteria, audience, and intended output.
2. Capture the target baseline before drawing conclusions.
3. Read applicable project instructions, plans, tasks, documentation, and
   installed workspace guides. A plan integration review includes every
   completed task's final review and integrated commit.
4. Inspect the target and enough surrounding context to evaluate its contracts
   and effects.
5. Run safe, relevant checks needed to support or disprove suspected findings.
6. Return a complete review payload and handoff payload to the orchestrator.
7. The orchestrator writes the review under
   `projects/<project-name>/reviews/`. It writes the handoff under the task's
   `handoffs/` directory for task reviews or the plan-level `handoffs/`
   directory for plan integration reviews.
8. Recheck every finding against its cited evidence and clearly state any
   unreviewed areas or unresolved limitations.

Reviewing does not by itself authorize remediation. Do not change the reviewed
target unless the user separately asks for implementation.

Reviewers remain sandboxed read-only. They do not write review, handoff, task,
or plan files. The orchestrator persists their payloads without weakening
findings or uncertainty.

For a final task review, `clean` moves the task to `ready-for-integration`,
`actionable-findings` moves it to `needs-fix`, and `blocked` records a blocker.
A clean intermediate checkpoint review leaves the task `in-progress`.

A plan integration review targets the clean integration worktree and exact head
recorded in plan progress after every task is integrated and combined
validation has passed. A clean result permits plan completion when the other
completion conditions are satisfied. Actionable findings keep the plan
`in-progress` and require a correction task; a blocked result records the
limitation and resolution action. Any later integration invalidates the prior
plan review and requires a new review of the new head.

## Updating a Review

Treat every plan-task and plan-integration review as an immutable record of a
specific target state. When verifying fixes, create the next numbered review,
reference the earlier finding IDs, and record whether each finding is fixed,
still open, rejected, or waived. Do not edit or replace the earlier review.

For a standalone review that is intentionally maintained over time, update the
existing artifact only when the user explicitly requests that behavior. Keep
finding IDs stable and preserve enough history to distinguish each reviewed
baseline.
