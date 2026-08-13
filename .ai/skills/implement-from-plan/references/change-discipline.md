# Change Discipline

Before editing:

- Check current status if the project uses version control.
- Read nearby code and tests.
- Identify generated files and avoid hand-editing them unless the project expects that.

During edits:

- Keep related behavior and tests together.
- Prefer structured parsers or framework APIs over string manipulation.
- Add comments only where they prevent misunderstanding.

Before finishing:

- Run the narrowest test that proves the changed behavior.
- Run formatting or lint only when it is project-standard and not unexpectedly destructive.
- Report commands exactly enough that another engineer can reproduce them.
