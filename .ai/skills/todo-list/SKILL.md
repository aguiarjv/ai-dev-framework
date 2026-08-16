---
name: todo-list
description: Maintain a lightweight local todo reminder list. Use when Codex should remember tasks for later, append short todo reminders, create a simple todo file, or read/show/list existing todo reminders without creating a full task spec or project plan.
---

# Todo List

## Default Storage

- Use `.local/todos.md` unless the user explicitly provides another path.
- Treat `.local/todos.md` as local working state, not durable project documentation.
- Create `.local/` and `.local/todos.md` when appending and the file does not exist.
- Start a new todo file with `# Todo`.

## Append Todos

1. Convert each requested item into a short, single-line reminder.
2. Preserve the user's intent, but remove extra explanation, background, and implementation detail.
3. Append each item as a Markdown checklist entry:

```markdown
- [ ] short reminder
```

4. Do not add priorities, due dates, owners, sections, or tags unless the user explicitly asks.
5. After appending, report the added reminders and the todo file path.

## Show Todos

1. Read the selected todo file.
2. Display the current checklist items in file order.
3. If the file does not exist or has no checklist items, say that there are no saved todos yet.

## Boundaries

- Do not create `docs/tasks/` specs, ADRs, plans, commits, or tracked repository files for todo-only requests unless the user separately asks.
- Do not mark items complete, delete items, or reorganize the list unless the user explicitly requests that behavior.
- If the user gives a long list, keep every item but shorten each description to reminder length.
