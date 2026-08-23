---
name: repo-onboarding
description: Map an unfamiliar repository or subsystem before implementation, review, debugging, or planning. Use when Codex needs to discover project structure, conventions, commands, frameworks, ownership boundaries, risks, or likely change points before acting.
---

# Repo Onboarding

## Workflow

1. Inspect the top-level shape: files, package manifests, build configs, test configs, docs, and existing AI guidance.
2. Identify the stack from primary repo evidence, not filenames alone.
3. Find entrypoints, core modules, tests, generated files, and local conventions.
4. Map likely commands for install, build, test, lint, format, and dev server.
5. Note risks: missing tests, unclear generated outputs, migrations, deployment configs, or unusual permissions.
6. Record confirmed facts with path or command evidence and keep assumptions separate.
7. Produce concise operating notes with concrete paths and commands suitable for an `H-n` handoff.

## Output

Return:

- project purpose as inferred from repo evidence;
- stack and important tools;
- key directories and ownership boundaries;
- verification commands and confidence level;
- likely change points for the requested task;
- unresolved questions that cannot be answered from the repository.

Read `references/repo-map.md` when the user asks for a persistent onboarding note or repo map.
