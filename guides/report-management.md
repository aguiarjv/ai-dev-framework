# Report Management

Use the `reports/` directory in a managed project for durable project reports,
including investigation summaries, research results, status snapshots,
operational analyses, inventories, and other evidence-based syntheses.

Reports are optional. Do not create a completion report for every plan unless
the user requests it or the approved plan includes it as a deliverable.

A report explains what was found, measured, or concluded for a stated purpose.
Use `reviews/` instead when the primary purpose is to evaluate a target against
criteria and produce actionable findings. Use `docs/` for durable project
documentation that should describe the project independently of a particular
reporting event.

## Location and Naming

Create each report as a Markdown file directly inside the applicable managed
project:

```text
projects/
  <project-name>/
    reports/
      <report-name>.md
```

Use a concise, descriptive, kebab-case filename that identifies the report's
subject or purpose. Do not store a managed project's report in the repository
checkout, another managed project, `docs/`, or `reviews/`.

Before writing, check whether the target path already exists. Do not overwrite
or repurpose an existing report unless the user explicitly asks to update it.
Ask the user when choosing between a new point-in-time report and an update to
an existing report would affect how its history should be interpreted.

## Required Context

Before producing a report, establish:

- The managed project the report belongs to.
- The report's purpose, question, scope, and exclusions.
- The intended audience and the decision or activity it should support.
- The relevant time range, repository state, environment, or other baseline.
- The required sources, checks, measurements, and level of detail.
- Whether the report is a point-in-time snapshot or a maintained artifact.

Inspect the available project, repository, plan, task, review, documentation,
and installed-guide context before asking the user for discoverable facts. Ask
the user when a missing choice affects the report's purpose, scope, audience,
interpretation, or expected conclusions. Do not invent data, evidence, or
requirements.

## Evidence and Baseline

Make the report's basis clear enough that another person or agent can reproduce
or challenge its conclusions. Record the relevant `as of` time and, when the
repository state matters, the worktree, branch, full commit SHA, and whether
uncommitted changes were included.

Identify sources precisely. Prefer repository-relative paths and line numbers
for local evidence, exact commands or checks for generated evidence, and direct
references to related plans, tasks, reviews, or project documentation. Record
when a source was unavailable or could not be verified.

Separate these categories in the writing:

- Observed facts: directly supported by inspected sources or measurements.
- Inferences: conclusions drawn from the observed facts.
- Recommendations: proposed actions or decisions, when the report calls for
  them.

Label uncertainty and conflicting evidence. Do not present an inference or
recommendation as an observed fact.

## Report File Contents

Every report file should contain enough context to understand its result without
reconstructing the reporting session. Include:

- A title and stable report identifier.
- The creation time and, when updated, the last-update time.
- The purpose, audience, scope, exclusions, time range, and baseline.
- The method, checks, and sources used.
- An executive summary proportional to the report's size.
- Evidence-backed observations and analysis.
- Recommendations or next actions when requested or supported by the purpose.
- Limitations, unresolved questions, and material gaps in evidence.

Adapt the body to the report type. For example, a status report may organize
work by completed, active, blocked, and next actions, while an investigation
report may organize evidence by hypothesis. Do not force unrelated report types
into one fixed section structure.

## Workflow

1. Resolve the report's purpose, audience, scope, baseline, sources, and desired
   level of detail.
2. Read applicable project instructions, plans, tasks, reviews, documentation,
   and installed workspace guides.
3. Gather evidence with read-only inspection and safe, relevant checks.
4. Reconcile conflicting sources or record the conflict and its effect on the
   conclusions.
5. Separate observed facts, inferences, and recommendations while synthesizing
   the result.
6. Write the report to
   `projects/<project-name>/reports/<report-name>.md`.
7. Verify that material claims have evidence and that limitations, timestamps,
   and repository baselines are accurate.

Creating a report does not by itself authorize changes to the project or an
external system. Present recommended follow-up work for user approval unless it
is already part of the authorized task.

## Updating a Report

Preserve the meaning of point-in-time reports. Create a new report for a new
period, baseline, or materially different question unless the user explicitly
requests an update to the existing artifact. For a maintained report, record
the update time and revise its baseline, sources, conclusions, and limitations
together so the report does not mix incompatible snapshots.
