---
name: documentation-management
description: Create or update Markdown documentation under a managed project's docs folder from user-provided information or read-only repository exploration. Organize subject-specific documents into kebab-case domain folders. Do not use for plans, handoffs, reviews, reports, or architecture decision records.
---

# Documentation Management

Use this skill from the orchestrator when the user wants to create or update
durable project documentation under `projects/<project-name>/docs/`.

## Resolve the Destination

- Confirm the managed project and the documentation goal. Ask the user when
  either is ambiguous and cannot be resolved from the workspace.
- Write Markdown files only inside the managed project's `docs/` folder, never
  the repository checkout's own documentation folder.
- Inspect the existing `docs/` structure before selecting a path. Reuse an
  existing domain folder when it already covers the subject.
- For a specific subject, choose a short kebab-case domain folder and a
  descriptive kebab-case filename: `docs/<domain>/<document-name>.md`. Classify
  by subject domain, not by document type.
- Keep genuinely cross-domain documentation directly under `docs/`.
- Do not create `README.md` files in `docs/`. Do not place ordinary
  documentation in the reserved `docs/adrs/` folder.

For example, a guide explaining how to run the project locally belongs at a
path such as `docs/dev-local/running-locally.md`, not `docs/guides/`.

If multiple domain names are equally reasonable and the choice would affect
navigation or an existing taxonomy, ask the user instead of creating competing
folders.

## Choose the Information Source

### User-provided information

When the user supplies the facts or source material, author the document
directly. Preserve the supplied meaning, reconcile it with relevant existing
project documentation, and identify contradictions or missing decisions rather
than silently inventing details. Do not spawn explorers merely to repeat
information the user already supplied.

### Project exploration

When the user asks to derive or verify the documentation from the project,
launch read-only `explorer` agents before writing:

1. Resolve the repository checkout, branch, and baseline commit that represent
   the documentation target.
2. Give each explorer a bounded investigation question, the applicable
   workspace and repository instructions, the documentation goal, and the
   required evidence. Use one explorer for a focused subject; use multiple
   explorers only for independent investigation areas that benefit from
   parallel work.
3. Require concrete source paths, commands, configuration, behavior, unknowns,
   and conflicting evidence. Explorers return their structured payloads to the
   orchestrator and do not write documentation files.
4. Consolidate the findings. If evidence is incomplete or contradictory,
   continue bounded exploration or ask the user about the unresolved decision.
5. Write the documentation from the verified evidence. Follow the workspace's
   handoff rules for explorer payloads when the request belongs to an existing
   plan.

Explorer-assisted documentation is a bounded documentation workflow. It does
not require a plan, implementation worktree, or implementation agent unless the
user's request also changes repository code or otherwise crosses into the
plan-driven development lifecycle.

## Write the Document

- Create the selected domain folder only when it does not already exist.
- Use a clear title and only the sections the subject needs. For procedural
  documentation, include prerequisites, steps, and a way to verify success when
  the available information supports them.
- Keep commands, paths, configuration keys, and prerequisites faithful to the
  supplied information or verified project evidence. Do not invent missing
  commands, environment variables, URLs, or behavior.
- Prefer durable explanations over snapshots of incidental implementation
  details. Add source-path references when they help future maintainers verify
  or update the document.
- Preserve unrelated documentation and existing navigation conventions. Do not
  replace an existing document unless the user requested an update to it.

## Validate and Report

Before finishing:

1. Confirm every created or modified file is below the selected managed
   project's `docs/` folder.
2. Re-read the document for internal consistency and verify referenced local
   paths against the selected project baseline.
3. Run applicable documentation checks when the workspace provides them.
4. Report the document paths, chosen domain, information source, validation,
   and any remaining uncertainty.
