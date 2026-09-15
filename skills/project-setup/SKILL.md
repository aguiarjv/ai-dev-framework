---
name: project-setup
description: Create a managed project workspace in a multi-project AI dev framework repository by cloning an existing GitHub repository or initializing a new Git project.
---

# Project Setup

Use this skill when the user wants to add a project to a multi-project AI dev
framework repository.

The outcome is a new managed project folder under `projects/<project-name>/`
with the standard project workspace structure. The actual Git repository lives
under `projects/<project-name>/worktrees/<default-branch-name>/`.

## Required Inputs

Ask the user for any missing information before making changes:

- The project name to use under `projects/`.
- Whether to clone an existing GitHub repository or create a new Git project.
- The GitHub repository URL when cloning.
- The initial branch name when creating a new Git project.

When cloning, detect the repository default branch after cloning and use that
branch name for the worktree folder.

## Project Structure

Create this structure for each managed project:

```text
  projects/
  <project-name>/
    AGENTS.md
    CLAUDE.md
    README.md
    docs/
      adrs/
    plans/
      done/
    scripts/
    worktrees/
      <default-branch-name>/
    reviews/
    reports/
```

## Folder Roles

- `AGENTS.md` contains project-specific AI instructions shared by supported
  coding agents.
- `CLAUDE.md` imports the shared instructions for Claude Code.
- `README.md` explains the managed project workspace.
- `docs/` contains project documentation created as needed. Architecture
  decision records live under `docs/adrs/`.
- `plans/` contains plans for new features, bug fixes, and related task lists.
  Completed plan folders are stored under `plans/done/`.
- `scripts/` contains helper automation for the managed project workspace.
  Scripts that are part of the project's source code remain in its repository
  checkout.
- `worktrees/` contains Git checkouts or worktrees for the project.
- `reviews/` contains review results.
- `reports/` contains generated reports.

## Workflow

1. Confirm the current repository is a multi-project AI dev framework repository.
   It should have root `AGENTS.md` and `CLAUDE.md` files, `.codex/agents/`,
   `.claude/agents/`, `.claude/skills/`, `.agents/guides/`, `.agents/skills/`,
   and `projects/`.
2. Resolve the project folder as `projects/<project-name>/`.
3. Stop and ask the user before overwriting or reusing an existing project
   folder.
4. Create the project metadata folders, including `docs/adrs/` and `scripts/`.
5. If cloning, clone the GitHub repository into
   `projects/<project-name>/worktrees/<default-branch-name>/`.
6. If creating a new Git project, create the repository in
   `projects/<project-name>/worktrees/<initial-branch-name>/` and initialize Git
   there.
7. Create the project-level `AGENTS.md` from `assets/AGENTS.md`, replacing every
   placeholder with the managed project name and checkout information.
8. Create the project-level `CLAUDE.md` from `assets/CLAUDE.md`. It imports the
   sibling `AGENTS.md`; do not copy or fork the shared instructions.

## Safety

- Do not guess missing project setup decisions. Ask the user first.
- Do not delete, replace, or overwrite an existing repository or project folder
  without explicit user approval.
- Treat network operations, such as cloning from GitHub, as actions that may
  require permission in restricted environments.
- Keep generated instructions reusable and avoid adding private project-specific
  rules unless the user provides them.
