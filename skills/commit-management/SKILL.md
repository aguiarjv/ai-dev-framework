---
name: commit-management
description: Author Git commit messages using the workspace Conventional Commits standard. Use whenever creating, amending, squashing, merging, reverting, or proposing a commit; not for read-only history inspection.
---

# Commit Management

Follow the [Commit Management guide](../../guides/commit-management.md) whenever
authoring a Git commit message. This skill standardizes an already-authorized
commit; it does not grant permission to commit, merge, rewrite history, or push.

## Prepare the Commit

1. Read the applicable repository instructions and inspect the worktree,
   staged changes, and relevant diff.
2. Confirm that the intended operation is authorized and that the staged
   content contains only the coherent change being committed. Do not stage or
   include unrelated user changes.
3. Identify the primary purpose of the staged change and select the most
   specific applicable type from the guide.
4. Add a scope only when the repository already defines one or a concise scope
   clearly improves the message. Do not invent issue identifiers or scopes.
5. Write a first line in this form:

   ```text
   <type>[optional scope][!]: <description>
   ```

6. Add a body or footers only when they preserve useful rationale, references,
   or breaking-change information.

If staged changes contain unrelated purposes, split them into separate commits
when doing so is safe and authorized. Otherwise stop and ask how the user wants
the commit divided; do not hide an incoherent change behind a generic type.

## Create and Verify

- Supply the complete message explicitly so Git does not open an editor or
  substitute a default merge, squash, or revert message.
- After the commit succeeds, inspect the resulting commit subject and identity.
- If a hook rewrites the message or the commit fails, report the result. Do not
  bypass verification hooks or rewrite published history unless explicitly
  authorized.

Before completing, verify that the subject begins with an allowed lowercase
type, optional scope, optional `!`, and exactly `: ` before its description.
