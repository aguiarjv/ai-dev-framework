# Decomposition Checklist

- Each acceptance criterion is observable and has a verification method.
- Each subtask has one owner and a bounded path/interface scope.
- Dependencies are explicit and point only to existing task IDs.
- Parallel subtasks do not share writable files, generated outputs, or contract ownership.
- Production behavior, tests, migrations, documentation, and harnesses are included where they are required for completion.
- An integration checkpoint exists when independently implemented slices must be composed or verified together.
- Every subtask has a concrete completion condition and a failure or blocker path.
