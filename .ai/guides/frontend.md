# Frontend Guide

Use this guide for UI, client-side state, browser behavior, views, pages, components, styling, accessibility, and frontend tests.

## Structure

- Separate UI components from business, data, and orchestration logic.
- Keep components focused on rendering, composition, local UI state, and calling functions or methods from other files.
- Put reusable logic in separate modules, hooks, services, stores, actions, or helpers according to the project's conventions.
- Avoid embedding data fetching, persistence, validation, routing side effects, or complex transformations directly inside presentational components.
- Prefer small component APIs with explicit props and callbacks over components that know too much about the wider application.

## Implementation

- Follow existing design system, file naming, routing, state-management, and test patterns.
- Keep accessibility, loading, empty, error, and disabled states aligned with the surrounding UI.
- Test behavior at the logic boundary and user-facing flow, not internal component details unless the project already does that.
- When a task mixes UI and logic, create separate subtasks for component work and logic/module work.
- For UI work where browser rendering matters, prefer registered visual harnesses when available. Use `playwright-visual-review` for responsive layout, overlap, overflow, blank-render, screenshot report, or visual QA workflows.
