# Commit Management

Use Conventional Commits for every commit message authored by an agent or
prepared for a user. This includes ordinary commits, amended and squashed
commits, merge commits, and reverts.

## Message Format

The first line must use this format:

```text
<type>[optional scope][!]: <description>
```

- Write the type in lowercase.
- Use a short, imperative description in lowercase without a trailing period.
- Add a scope only when it identifies a clear codebase area. Follow an existing
  repository scope convention when one exists; otherwise use a concise
  lowercase kebab-case name.
- Add `!` before the colon for a breaking change and explain the break in a
  `BREAKING CHANGE:` footer.
- Keep the first line self-contained. Add a body or footers after a blank line
  when the reason, consequences, migration work, or issue references matter.

Examples:

```text
feat: add project setup command
fix(installer): prevent duplicate skill copies
docs: explain the worktree layout
refactor(config)!: replace the legacy configuration format
```

## Types

Choose the type that describes the commit's primary purpose:

- `feat`: Add or extend user-visible functionality.
- `fix`: Correct faulty behavior.
- `docs`: Change documentation only.
- `refactor`: Restructure code without changing its intended behavior.
- `test`: Add or revise tests without changing production behavior.
- `chore`: Perform maintenance that fits no more specific type.
- `build`: Change build tooling, packaging, or dependencies.
- `ci`: Change continuous-integration configuration or automation.
- `perf`: Improve performance without otherwise changing behavior.
- `style`: Change formatting or other non-functional code style.
- `revert`: Revert an earlier commit.

Do not use `feat` as a synonym for any change or `chore` when a more specific
type applies. If independently useful changes have different primary purposes,
split them into separate commits when that is within the authorized work.

## Bodies, Footers, and Breaking Changes

Use the optional body to explain why the change was needed and material
behavior or tradeoffs that are not clear from the diff. Do not use the body as
a file-by-file change log.

Use Git trailers or Conventional Commit footers for issue references and other
metadata. A breaking change should use both a `!` in the first line and a
footer that explains the impact and required migration:

```text
feat(api)!: remove legacy authentication endpoint

BREAKING CHANGE: clients must use the token exchange endpoint.
```

## Special Commits

- Merge commits authored by the framework must receive an explicit compliant
  message. Use the integrated change's primary type when the merge has one,
  such as `feat: integrate project setup`; use `chore: integrate <identifier>`
  for a mixed-purpose integration.
- Squashed and amended commits must validate as complete messages rather than
  preserving a noncompliant first line.
- Reverts use `revert: <original description>` and identify the reverted commit
  in the body.
- Initial commits follow the same type rules; they are not automatically
  `chore` commits.

## Repository Compatibility

Honor stricter repository rules when they remain compatible with this format.
If a repository requires an incompatible commit format, stop and ask the user
which convention should govern instead of silently bypassing either rule.

This convention controls message format. It does not authorize creating,
amending, squashing, merging, reverting, or pushing a commit.
