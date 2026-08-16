---
name: playwright-visual-review
description: Use registered Playwright or browser-based visual review workflows for frontend and full-stack UI work. Use when Codex needs to capture screenshots, inspect responsive layout, detect overlap/overflow/blank rendering, interpret visual QA reports, create a project-specific browser visual harness, or route visual findings through planner, implementer, and reviewer agents.
---

# Playwright Visual Review

## Workflow

1. Read `docs/tasks/<task-slug>.md` and `.local/tasks/<task-slug>/progress.md` when working inside an approved task.
2. Read `.ai/harnesses/registry.md` before choosing commands.
3. If a registered Playwright or browser visual harness applies, use that harness. Prefer `--help` for usage and `--dry-run` when available before launching browsers or local servers.
4. If no harness applies and repeatable browser visual review is needed, use `create-harness` to add a project-specific harness. Do not invent a one-off visual workflow when the result should be repeatable.
5. Run the real harness when local prerequisites allow it. Inspect the report, screenshots, JSON output, traces, or videos produced by the harness.
6. Treat confirmed overlap, overflow, clipped content, blank rendering, missing required content, broken responsive states, or inaccessible visual states as actionable findings.
7. Treat missing browser binaries, missing host libraries, app/server startup failure, port binding failure, credentials, or unavailable external services as blockers, not visual findings.
8. Route confirmed visual issues through the normal `planner` -> `implementer` -> `reviewer` loop. After fixes, rerun the visual harness when dependencies allow it.

## Harness Expectations

- Keep harnesses project-specific. The framework skill should not hardcode Storybook, Vite, Next.js, routes, selectors, ports, scenario names, or screenshot filenames.
- A visual harness should document prerequisites, startup command, target URLs or stories, viewport scenarios, output paths, success criteria, and expected failures in `.ai/harnesses/registry.md`.
- Prefer smoke-level visual checks unless the task explicitly asks for screenshot baselines or visual regression infrastructure.
- Write durable outputs that agents can hand off: Markdown report, screenshots, and structured findings when practical.
- Exit non-zero when confirmed visual issues or blockers prevent a clean review.

## Report Rules

- Cite report and screenshot paths in handoffs.
- Separate confirmed visual issues, manual observations, and environment blockers.
- Include viewport, browser, route/story, theme or mode, and screenshot filename for each issue when available.
- Prefer likely causes tied to concrete files, selectors, components, styles, or layout constraints.
- Do not claim screenshots were reviewed if the harness was blocked before capture.

## Fix Scope

- Fix demo/page composition, spacing, responsive constraints, visual states, and app-specific styles before changing public component APIs.
- Preserve existing user workflows, accessibility states, theme/mode controls, and test coverage unless the approved plan says otherwise.
- After fixes, run the visual harness plus the narrowest relevant unit/build checks. If browser prerequisites are unavailable, report the blocker and the command that should be run later.
