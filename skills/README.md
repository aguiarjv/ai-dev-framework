# Skills

This directory contains reusable Agent Skills definitions that the framework
installs into target projects for both Codex and Claude Code.

Skills should be small, composable, and focused on one workflow or capability.
Keep their frontmatter within the open Agent Skills fields so the same authored
source remains portable. The installer renders discovery copies under both
`.agents/skills/` and `.claude/skills/`.

## Available Skills

- [Grill Me](grill-me/SKILL.md) stress-tests a plan, decision, or idea through
  structured rounds of questions.
- [Handoff Management](handoff-management/SKILL.md) creates and consumes
  durable, minimal-context agent handoffs.
- [Worktree Management](worktree-management/SKILL.md) manages isolated task
  worktrees, the plan integration branch, and delivery and cleanup boundaries.
- [Project Setup](project-setup/SKILL.md) creates a managed project workspace.
- [Plan Management](plan-management/SKILL.md) creates and manages structured
  plans, tasks, progress, handoffs, and completed-plan archives.
- [Task Execution](task-execution/SKILL.md) implements an approved task or
  correction pass and hands it off for review.
- [Review Management](review-management/SKILL.md) coordinates read-only task
  and plan integration reviews and applies their results to workflow state.
- [ADR Management](adr-management/SKILL.md) creates and supersedes architecture
  decision records under `docs/adrs/`.
- [Database Exploration](database-exploration/SKILL.md) performs bounded live
  database investigation through verified read-only access.
- [Commit Management](commit-management/SKILL.md) applies the workspace's
  Conventional Commits standard whenever a commit message is authored.
