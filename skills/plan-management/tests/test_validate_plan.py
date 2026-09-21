from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_plan.py"
SPEC = importlib.util.spec_from_file_location("plan_management_validator", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
PlanValidator = MODULE.PlanValidator


class PlanFixture:
    task_ids = ("001-build", "002-test")

    def __init__(self, root: Path) -> None:
        self.project_root = root
        self.plan_dir = root / "plans" / "demo-plan"
        self.plan_dir.mkdir(parents=True)
        (self.plan_dir / "handoffs").mkdir()
        (root / "reviews" / "demo-plan").mkdir(parents=True)

    def write(
        self,
        *,
        statuses: dict[str, str] | None = None,
        plan_status: str = "not-started",
        plan_criteria_checked: bool = False,
        dependencies: dict[str, list[str]] | None = None,
        plan_dependencies: dict[str, list[str]] | None = None,
        next_actions: list[str] | None = None,
        plan_blocker: str = "None.",
        task_blockers: dict[str, str] | None = None,
        assignments: dict[str, tuple[str, str]] | None = None,
        plan_related_path: str = "src/app.py",
        include_documentation: bool = True,
        include_integration_review: bool | None = None,
    ) -> None:
        statuses = statuses or {task_id: "not-started" for task_id in self.task_ids}
        dependencies = dependencies or {
            "001-build": [],
            "002-test": ["001-build"],
        }
        plan_dependencies = plan_dependencies or dependencies
        task_blockers = task_blockers or {}
        assignments = assignments or {}
        if include_integration_review is None:
            include_integration_review = plan_status == "completed"

        task_rows: list[str] = []
        completed_task_ids = [
            task_id for task_id in self.task_ids if statuses[task_id] == "completed"
        ]
        last_completed_task = completed_task_ids[-1] if completed_task_ids else None

        for task_id in self.task_ids:
            depends_on = plan_dependencies[task_id]
            dependency_cell = (
                ", ".join(f"`{dependency}`" for dependency in depends_on)
                if depends_on
                else "None"
            )
            task_rows.append(
                f"| `{task_id}` | [{task_id}](tasks/{task_id}/TASK.md) | "
                f"{dependency_cell} |"
            )

        checked = "x" if plan_criteria_checked else " "
        plan_documentation_rows = (
            "| `docs/architecture.md` | `project-docs` | `existing` | `inspect` "
            "| Defines architecture. | Explorer read its design section. |\n"
            "| `.agents/guides/plan-and-task-management.md` | `workspace-guide` "
            "| `existing` | `inspect` | Defines planning rules. "
            "| Explorer read the installed guide. |"
            if include_documentation
            else ""
        )
        self._write(
            self.plan_dir / "PLAN.md",
            f"""---
id: "demo-plan"
title: "Demo plan"
created: "2026-09-13"
updated: "2026-09-13T12:00:00Z"
worktree: "worktrees/main"
branch: "main"
baseline_commit: "{'a' * 40}"
planned_integration_worktree: "worktrees/demo-plan/plan-integration"
planned_integration_branch: "plan/demo-plan"
delivery_branch: "main"
approved_at: "2026-09-13T12:00:00Z"
---

# Demo plan

## Goal

Build and test the feature.

## Context

The feature does not exist yet.

## Scope

### In Scope

- Build and test.

### Out of Scope

- Deployment.

## Approach

Implement before testing.

## Integration

- Task integration: Merge cleanly reviewed task branches into `plan/demo-plan`.
- Integration order: Task sequence among simultaneously ready tasks.
- Integration validation: Run the complete automated test suite.
- Delivery: Merge to `main` only with separate authorization.

## Dependencies

- None.

## Related Files and Folders

| Path | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- |
| `{plan_related_path}` | `existing` | `inspect`, `modify` | Owns behavior. | Explorer found it. |
| `tests/test_app.py` | `planned` | `create` | Covers behavior. | Tests establish the location. |

## Relevant Documentation and Guides

| Path | Source | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- | --- |
{plan_documentation_rows}

## Open Questions

- None.

## Architecture Decisions

| Decision | ADR Required | Path | Rationale |
| --- | --- | --- | --- |
| No ADR required | no | None | This fixture changes no architecture. |

## Tasks

| ID | Task | Depends on |
| --- | --- | --- |
{chr(10).join(task_rows)}

## Completion Criteria

- [{checked}] All planned work is validated.
""",
        )

        current_tasks = [
            task_id for task_id, status in statuses.items() if status == "in-progress"
        ]
        if next_actions is None:
            if all(status == "completed" for status in statuses.values()):
                completion_ready = plan_criteria_checked and include_integration_review
                next_actions = [] if completion_ready else ["plan"]
            elif plan_status == "completed":
                next_actions = []
            else:
                next_actions = [
                    task_id
                    for task_id, status in statuses.items()
                    if status
                    in {
                        "in-progress",
                        "ready-for-review",
                        "ready-for-integration",
                        "needs-fix",
                        "blocked",
                    }
                    or (
                        status == "not-started"
                        and all(
                            statuses.get(dependency) == "completed"
                            for dependency in dependencies[task_id]
                        )
                    )
                ]
        action_rows = "\n".join(
            f"| `{task_id}` | Continue {task_id}. |" for task_id in next_actions
        )
        status_rows = "\n".join(
            f"| `{task_id}` | `{status}` | {status.replace('-', ' ').title()}. |"
            for task_id, status in statuses.items()
        )
        integration_created = any(
            status != "not-started" for status in statuses.values()
        ) or plan_status != "not-started"
        integration_worktree = (
            '"worktrees/demo-plan/plan-integration"' if integration_created else "null"
        )
        integration_branch = '"plan/demo-plan"' if integration_created else "null"
        integration_head = f'"{"c" * 40}"' if integration_created else "null"
        integration_uncommitted = "false" if integration_created else "null"
        latest_plan_review = (
            '"reviews/demo-plan/demo-plan-integration-review-001.md"'
            if include_integration_review
            else "null"
        )
        if include_integration_review:
            self._write_plan_review("clean")
        integration_validation = (
            "Complete automated test suite passed."
            if all(status == "completed" for status in statuses.values())
            and plan_criteria_checked
            else "Not run."
        )
        self._write(
            self.plan_dir / "PROGRESS.md",
            f"""---
plan: "demo-plan"
status: {plan_status}
updated: "2026-09-13T12:00:00Z"
current_tasks: {json.dumps(current_tasks)}
integration_worktree: {integration_worktree}
integration_branch: {integration_branch}
integration_head_commit: {integration_head}
integration_uncommitted_changes: {integration_uncommitted}
latest_handoff: null
latest_review: {latest_plan_review}
---

# Plan Progress: Demo plan

## Summary

Current plan state.

## Integration

- State: Current.
- Integrated tasks: Recorded by completed task status.
- Validation: {integration_validation}
- Review: Recorded in latest_review when complete.
- Delivery: Not performed.

## Task Status

| Task | Status | Result or blocker |
| --- | --- | --- |
{status_rows}

## Blockers

- {plan_blocker}

## Next Actions

| Task | Action |
| --- | --- |
{action_rows}
""",
        )

        for task_id in self.task_ids:
            task_dir = self.plan_dir / "tasks" / task_id
            task_dir.mkdir(parents=True)
            (task_dir / "handoffs").mkdir()
            task_path = "src/app.py" if task_id == "001-build" else "tests/test_app.py"
            task_state = "existing" if task_id == "001-build" else "planned"
            task_use = "modify" if task_id == "001-build" else "create"
            documentation_rows = ""
            if include_documentation:
                documentation_rows = (
                    "| `docs/architecture.md` | `project-docs` | `existing` "
                    "| `inspect` | Defines architecture. | Explorer read it. |"
                )
                if task_id == "001-build":
                    documentation_rows += (
                        "\n| `.agents/guides/plan-and-task-management.md` "
                        "| `workspace-guide` | `existing` | `inspect` "
                        "| Defines planning rules. | Explorer read it. |"
                    )
            acceptance_checked = (
                "x"
                if statuses[task_id] in {"ready-for-integration", "completed"}
                else " "
            )
            self._write(
                task_dir / "TASK.md",
                f"""---
id: "{task_id}"
plan: "demo-plan"
title: "{task_id}"
created: "2026-09-13"
updated: "2026-09-13T12:00:00Z"
depends_on: {json.dumps(dependencies[task_id])}
planned_worktree: "worktrees/demo-plan/{task_id}"
planned_branch: "task/demo-plan/{task_id}"
review_required: true
---

# {task_id}

## Objective

Complete {task_id}.

## Requirements

- Preserve existing behavior.

## Related Files and Folders

| Path | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- |
| `{task_path}` | `{task_state}` | `{task_use}` | Required by task. | Explorer found it. |

## Relevant Documentation and Guides

| Path | Source | State | Expected Use | Relevance | Evidence |
| --- | --- | --- | --- | --- | --- |
{documentation_rows}

## Acceptance Criteria

- [{acceptance_checked}] The task result is observable.

## Validation

- Run the relevant automated test.

## Review Checkpoints

- Final review after implementation is ready.
""",
            )

            status = statuses[task_id]
            if status == "not-started":
                worktree = branch = head_commit = uncommitted = "null"
            else:
                assigned_worktree, assigned_branch = assignments.get(
                    task_id,
                    (
                        f"worktrees/demo-plan/{task_id}",
                        f"task/demo-plan/{task_id}",
                    ),
                )
                worktree = f'"{assigned_worktree}"'
                branch = f'"{assigned_branch}"'
                head_commit = f'"{"b" * 40}"'
                uncommitted = "false"
            latest_handoff = "null"
            latest_review = "null"
            review_result = "Not run."
            if status == "ready-for-review":
                latest_handoff = (
                    f'"plans/demo-plan/tasks/{task_id}/handoffs/'
                    '001-implementer-to-reviewer.md"'
                )
                review_result = "Awaiting final review."
            elif status == "needs-fix":
                latest_handoff = (
                    f'"plans/demo-plan/tasks/{task_id}/handoffs/'
                    '002-reviewer-to-implementer.md"'
                )
                latest_review = (
                    f'"reviews/demo-plan/demo-plan-{task_id}-review-001.md"'
                )
                review_result = "Actionable findings."
                self._write_review(task_id, "actionable-findings")
            elif status == "ready-for-integration":
                latest_handoff = (
                    f'"plans/demo-plan/tasks/{task_id}/handoffs/'
                    '002-reviewer-to-orchestrator.md"'
                )
                latest_review = (
                    f'"reviews/demo-plan/demo-plan-{task_id}-review-001.md"'
                )
                review_result = "Clean; awaiting integration."
                self._write_review(task_id, "clean")
            elif status == "completed":
                latest_handoff = (
                    f'"plans/demo-plan/tasks/{task_id}/handoffs/'
                    '002-reviewer-to-orchestrator.md"'
                )
                latest_review = (
                    f'"reviews/demo-plan/demo-plan-{task_id}-review-001.md"'
                )
                review_result = "Clean."
                self._write_review(task_id, "clean")
            blocker = task_blockers.get(
                task_id,
                "Waiting for required input." if status == "blocked" else "None.",
            )

            validation = (
                "Automated tests passed."
                if status
                in {
                    "ready-for-review",
                    "ready-for-integration",
                    "needs-fix",
                    "completed",
                }
                else "Not run."
            )
            next_action = "None." if status == "completed" else f"Continue {task_id}."
            if status != "completed":
                integrated_commit = "null"
            elif task_id == last_completed_task:
                integrated_commit = f'"{"c" * 40}"'
            else:
                integrated_commit = f'"{"d" * 40}"'
            self._write(
                task_dir / "PROGRESS.md",
                f"""---
task: "{task_id}"
status: {status}
updated: "2026-09-13T12:00:00Z"
worktree: {worktree}
branch: {branch}
head_commit: {head_commit}
integrated_commit: {integrated_commit}
uncommitted_changes: {uncommitted}
latest_handoff: {latest_handoff}
latest_review: {latest_review}
---

# Task Progress: {task_id}

## Summary

Current task state.

## Work Completed

- None.

## Decisions

- None.

## Changed Files

- None.

## Validation

- {validation}

## Blockers

- {blocker}

## Review

- Required: Yes.
- Latest review: {latest_review.strip('"') if latest_review != 'null' else 'None.'}
- Result: {review_result}

## Next Action

{next_action}
""",
            )

    def _write_review(self, task_id: str, status: str) -> None:
        self._write(
            self.project_root
            / "reviews"
            / "demo-plan"
            / f"demo-plan-{task_id}-review-001.md",
            f"""---
plan: "demo-plan"
task: "{task_id}"
review_kind: "task-final"
status: {status}
worktree: "worktrees/demo-plan/{task_id}"
branch: "task/demo-plan/{task_id}"
head_commit: "{'b' * 40}"
uncommitted_changes: false
---

# Review
""",
        )

    def _write_plan_review(self, status: str) -> None:
        self._write(
            self.project_root
            / "reviews"
            / "demo-plan"
            / "demo-plan-integration-review-001.md",
            f"""---
plan: "demo-plan"
task: null
review_kind: "plan-integration"
status: {status}
worktree: "worktrees/demo-plan/plan-integration"
branch: "plan/demo-plan"
head_commit: "{'c' * 40}"
uncommitted_changes: false
---

# Integration Review
""",
        )

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def errors(self) -> list[str]:
        return PlanValidator(self.plan_dir).run()


class PlanValidatorTests(unittest.TestCase):
    def run_fixture(self, **kwargs: object) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(**kwargs)
            return fixture.errors()

    def test_initial_plan_is_valid(self) -> None:
        self.assertEqual(self.run_fixture(), [])

    def test_plan_without_relevant_documentation_keeps_empty_tables(self) -> None:
        self.assertEqual(self.run_fixture(include_documentation=False), [])

    def test_all_tasks_can_finish_before_plan_criteria(self) -> None:
        errors = self.run_fixture(
            statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
            plan_status="in-progress",
        )
        self.assertEqual(errors, [])

    def test_completed_plan_requires_checked_plan_criteria(self) -> None:
        errors = self.run_fixture(
            statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
            plan_status="completed",
            next_actions=[],
        )
        self.assertTrue(any("unchecked plan completion criteria" in error for error in errors))

    def test_completed_plan_is_valid_when_all_criteria_are_checked(self) -> None:
        errors = self.run_fixture(
            statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
            plan_status="completed",
            plan_criteria_checked=True,
        )
        self.assertEqual(errors, [])

    def test_completed_tasks_and_criteria_wait_for_integration_review(self) -> None:
        errors = self.run_fixture(
            statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
            plan_status="in-progress",
            plan_criteria_checked=True,
            include_integration_review=False,
        )
        self.assertEqual(errors, [])

    def test_completed_plan_requires_current_clean_integration_review(self) -> None:
        errors = self.run_fixture(
            statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
            plan_status="completed",
            plan_criteria_checked=True,
            include_integration_review=False,
        )
        self.assertTrue(
            any("clean review of the current integration head" in error for error in errors)
        )

    def test_completed_plan_requires_combined_integration_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
                plan_status="completed",
                plan_criteria_checked=True,
            )
            progress_path = fixture.plan_dir / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            progress_path.write_text(
                content.replace(
                    "- Validation: Complete automated test suite passed.",
                    "- Validation: Not run.",
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any("must record combined integration validation" in error for error in errors)
        )

    def test_started_task_requires_completed_dependencies(self) -> None:
        errors = self.run_fixture(
            statuses={"001-build": "not-started", "002-test": "in-progress"},
            plan_status="in-progress",
        )
        self.assertTrue(any("incomplete dependencies: 001-build" in error for error in errors))

    def test_ready_for_review_task_is_valid(self) -> None:
        errors = self.run_fixture(
            statuses={"001-build": "ready-for-review", "002-test": "not-started"},
            plan_status="in-progress",
        )
        self.assertEqual(errors, [])

    def test_ready_for_integration_task_is_valid(self) -> None:
        errors = self.run_fixture(
            statuses={
                "001-build": "ready-for-integration",
                "002-test": "not-started",
            },
            plan_status="in-progress",
        )
        self.assertEqual(errors, [])

    def test_ready_for_integration_review_must_match_task_head(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={
                    "001-build": "ready-for-integration",
                    "002-test": "not-started",
                },
                plan_status="in-progress",
            )
            review_path = (
                fixture.project_root
                / "reviews"
                / "demo-plan"
                / "demo-plan-001-build-review-001.md"
            )
            content = review_path.read_text(encoding="utf-8")
            review_path.write_text(
                content.replace(
                    f'head_commit: "{"b" * 40}"',
                    f'head_commit: "{"e" * 40}"',
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any("latest_review head_commit must be" in error for error in errors)
        )

    def test_needs_fix_task_is_valid(self) -> None:
        errors = self.run_fixture(
            statuses={"001-build": "needs-fix", "002-test": "not-started"},
            plan_status="in-progress",
        )
        self.assertEqual(errors, [])

    def test_ready_for_review_requires_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={"001-build": "ready-for-review", "002-test": "not-started"},
                plan_status="in-progress",
            )
            progress_path = fixture.plan_dir / "tasks" / "001-build" / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            content = content.replace(
                'latest_handoff: "plans/demo-plan/tasks/001-build/handoffs/'
                '001-implementer-to-reviewer.md"',
                "latest_handoff: null",
            )
            progress_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(
            any("ready-for-review task must record latest_handoff" in error for error in errors)
        )

    def test_completed_task_requires_clean_review_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
                plan_status="completed",
                plan_criteria_checked=True,
            )
            progress_path = fixture.plan_dir / "tasks" / "001-build" / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            content = content.replace(
                'latest_review: "reviews/demo-plan/demo-plan-001-build-review-001.md"',
                "latest_review: null",
            )
            progress_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(
            any("completed task must record the clean latest_review" in error for error in errors)
        )

    def test_task_review_path_must_use_plan_subfolder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={
                    "001-build": "ready-for-integration",
                    "002-test": "not-started",
                },
                plan_status="in-progress",
            )
            progress_path = fixture.plan_dir / "tasks" / "001-build" / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            progress_path.write_text(
                content.replace(
                    "reviews/demo-plan/demo-plan-001-build-review-001.md",
                    "reviews/demo-plan-001-build-review-001.md",
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any(
                "latest_review must be a normalized Markdown path below "
                "reviews/demo-plan/" in error
                for error in errors
            )
        )

    def test_completed_task_requires_integrated_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
                plan_status="completed",
                plan_criteria_checked=True,
            )
            progress_path = fixture.plan_dir / "tasks" / "001-build" / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            progress_path.write_text(
                content.replace(f'integrated_commit: "{"d" * 40}"', "integrated_commit: null"),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any("completed task must record its integrated_commit" in error for error in errors)
        )

    def test_completed_plan_review_must_match_integration_head(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
                plan_status="completed",
                plan_criteria_checked=True,
            )
            review_path = (
                fixture.project_root
                / "reviews"
                / "demo-plan"
                / "demo-plan-integration-review-001.md"
            )
            content = review_path.read_text(encoding="utf-8")
            review_path.write_text(
                content.replace(f'head_commit: "{"c" * 40}"', f'head_commit: "{"e" * 40}"'),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any("integration latest_review head_commit must be" in error for error in errors)
        )

    def test_plan_review_path_must_use_plan_subfolder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
                plan_status="completed",
                plan_criteria_checked=True,
            )
            progress_path = fixture.plan_dir / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            progress_path.write_text(
                content.replace(
                    "reviews/demo-plan/demo-plan-integration-review-001.md",
                    "reviews/demo-plan-integration-review-001.md",
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any(
                "latest_review must be a normalized Markdown path below "
                "reviews/demo-plan/" in error
                for error in errors
            )
        )

    def test_completed_task_requires_clean_review_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
                plan_status="completed",
                plan_criteria_checked=True,
            )
            review_path = (
                fixture.project_root
                / "reviews"
                / "demo-plan"
                / "demo-plan-001-build-review-001.md"
            )
            content = review_path.read_text(encoding="utf-8")
            review_path.write_text(
                content.replace("status: clean", "status: actionable-findings"),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any("latest_review must have status 'clean'" in error for error in errors)
        )

    def test_needs_fix_task_requires_actionable_review_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={"001-build": "needs-fix", "002-test": "not-started"},
                plan_status="in-progress",
            )
            review_path = (
                fixture.project_root
                / "reviews"
                / "demo-plan"
                / "demo-plan-001-build-review-001.md"
            )
            content = review_path.read_text(encoding="utf-8")
            review_path.write_text(
                content.replace("status: actionable-findings", "status: clean"),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any(
                "latest_review must have status 'actionable-findings'" in error
                for error in errors
            )
        )

    def test_plan_integration_worktree_uses_plan_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            plan_path = fixture.plan_dir / "PLAN.md"
            content = plan_path.read_text(encoding="utf-8")
            plan_path.write_text(
                content.replace(
                    "worktrees/demo-plan/plan-integration",
                    "worktrees/demo-plan-integration",
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any(
                "planned_integration_worktree must be "
                "'worktrees/demo-plan/plan-integration'" in error
                for error in errors
            )
        )

    def test_task_worktree_uses_plan_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            task_path = fixture.plan_dir / "tasks" / "001-build" / "TASK.md"
            content = task_path.read_text(encoding="utf-8")
            task_path.write_text(
                content.replace(
                    "worktrees/demo-plan/001-build",
                    "worktrees/demo-plan-001-build",
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any(
                "planned_worktree must be 'worktrees/demo-plan/001-build'" in error
                for error in errors
            )
        )

    def test_actual_task_worktree_matches_planned_path(self) -> None:
        errors = self.run_fixture(
            statuses={"001-build": "in-progress", "002-test": "not-started"},
            plan_status="in-progress",
            assignments={
                "001-build": (
                    "worktrees/demo-plan/unplanned",
                    "task/demo-plan/001-build",
                )
            },
        )
        self.assertTrue(
            any("worktree must match planned_worktree" in error for error in errors)
        )

    def test_planned_assignments_must_be_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            task_path = fixture.plan_dir / "tasks" / "002-test" / "TASK.md"
            content = task_path.read_text(encoding="utf-8")
            content = content.replace(
                "worktrees/demo-plan/002-test",
                "worktrees/demo-plan/001-build",
            )
            task_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(any("share planned_worktree" in error for error in errors))

    def test_task_assignment_cannot_share_plan_integration_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            task_path = fixture.plan_dir / "tasks" / "001-build" / "TASK.md"
            content = task_path.read_text(encoding="utf-8")
            task_path.write_text(
                content.replace(
                    "worktrees/demo-plan/001-build",
                    "worktrees/demo-plan/plan-integration",
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(any("planned_integration_worktree" in error for error in errors))

    def test_started_task_requires_plan_integration_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={"001-build": "in-progress", "002-test": "not-started"},
                plan_status="in-progress",
            )
            progress_path = fixture.plan_dir / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            content = content.replace(
                'integration_worktree: "worktrees/demo-plan/plan-integration"',
                "integration_worktree: null",
            )
            content = content.replace(
                'integration_branch: "plan/demo-plan"',
                "integration_branch: null",
            )
            content = content.replace(
                f'integration_head_commit: "{"c" * 40}"',
                "integration_head_commit: null",
            )
            content = content.replace(
                "integration_uncommitted_changes: false",
                "integration_uncommitted_changes: null",
            )
            progress_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(
            any("started task work requires" in error for error in errors)
        )

    def test_actual_integration_assignment_must_match_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={"001-build": "in-progress", "002-test": "not-started"},
                plan_status="in-progress",
            )
            progress_path = fixture.plan_dir / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            progress_path.write_text(
                content.replace(
                    'integration_branch: "plan/demo-plan"',
                    'integration_branch: "plan/wrong"',
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any("integration_branch must match planned_integration_branch" in error for error in errors)
        )

    def test_integration_head_must_match_latest_completed_task_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={"001-build": "completed", "002-test": "not-started"},
                plan_status="in-progress",
            )
            progress_path = fixture.plan_dir / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            progress_path.write_text(
                content.replace(
                    f'integration_head_commit: "{"c" * 40}"',
                    f'integration_head_commit: "{"e" * 40}"',
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any("must match a completed task integration" in error for error in errors)
        )

    def test_required_adr_must_use_docs_adrs_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            plan_path = fixture.plan_dir / "PLAN.md"
            content = plan_path.read_text(encoding="utf-8")
            content = content.replace(
                "| No ADR required | no | None |",
                "| Durable decision | yes | None |",
            )
            plan_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(any("below docs/adrs/" in error for error in errors))

    def test_reopened_prerequisite_invalidates_completed_dependents(self) -> None:
        errors = self.run_fixture(
            statuses={"001-build": "in-progress", "002-test": "completed"},
            plan_status="in-progress",
        )
        self.assertTrue(
            any(
                "completed task has incomplete dependencies: 001-build" in error
                for error in errors
            )
        )

    def test_plan_task_dependencies_must_match_task_definition(self) -> None:
        errors = self.run_fixture(
            plan_dependencies={"001-build": [], "002-test": []},
        )
        self.assertTrue(any("but TASK.md has" in error for error in errors))

    def test_related_paths_must_be_repository_relative(self) -> None:
        errors = self.run_fixture(plan_related_path="/etc/passwd")
        self.assertTrue(any("normalized repository-relative path" in error for error in errors))

    def test_related_path_values_and_evidence_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            plan_path = fixture.plan_dir / "PLAN.md"
            content = plan_path.read_text(encoding="utf-8")
            content = content.replace("`existing` | `inspect`, `modify`", "`unknown` | `execute`")
            content = content.replace("Explorer found it.", "None.")
            plan_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(any("invalid State" in error for error in errors))
        self.assertTrue(any("invalid Expected Use" in error for error in errors))
        self.assertTrue(any("needs concrete evidence" in error for error in errors))

    def test_task_related_path_state_must_match_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            task_path = fixture.plan_dir / "tasks" / "001-build" / "TASK.md"
            content = task_path.read_text(encoding="utf-8")
            task_path.write_text(
                content.replace("| `src/app.py` | `existing`", "| `src/app.py` | `planned`"),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(any("but the plan uses 'existing'" in error for error in errors))

    def test_documentation_sources_enforce_their_path_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            plan_path = fixture.plan_dir / "PLAN.md"
            content = plan_path.read_text(encoding="utf-8")
            plan_path.write_text(
                content.replace("`docs/architecture.md`", "`README.md`"),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(any("project-docs path must be below docs/" in error for error in errors))

    def test_workspace_guides_are_existing_and_inspect_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            plan_path = fixture.plan_dir / "PLAN.md"
            content = plan_path.read_text(encoding="utf-8")
            content = content.replace(
                "| `workspace-guide` | `existing` | `inspect`",
                "| `workspace-guide` | `planned` | `modify`",
            )
            plan_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(
            any("workspace-guide reference must be existing" in error for error in errors)
        )
        self.assertTrue(
            any("workspace-guide reference must be inspect-only" in error for error in errors)
        )

    def test_planned_project_documentation_requires_create(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            plan_path = fixture.plan_dir / "PLAN.md"
            content = plan_path.read_text(encoding="utf-8")
            content = content.replace(
                "| `project-docs` | `existing` | `inspect`",
                "| `project-docs` | `planned` | `inspect`",
            )
            plan_path.write_text(content, encoding="utf-8")
            errors = fixture.errors()

        self.assertTrue(
            any(
                "planned project-docs reference must include create" in error
                for error in errors
            )
        )

    def test_downstream_task_can_modify_document_planned_by_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            plan_path = fixture.plan_dir / "PLAN.md"
            plan_content = plan_path.read_text(encoding="utf-8")
            plan_content = plan_content.replace(
                "| `docs/architecture.md` | `project-docs` | `existing` | `inspect` "
                "| Defines architecture. | Explorer read its design section. |",
                "| `docs/architecture.md` | `project-docs` | `existing` | `inspect` "
                "| Defines architecture. | Explorer read its design section. |\n"
                "| `docs/testing.md` | `project-docs` | `planned` "
                "| `create`, `modify` | Defines testing. | Explorer found the gap. |",
            )
            plan_path.write_text(plan_content, encoding="utf-8")

            task_path = fixture.plan_dir / "tasks" / "002-test" / "TASK.md"
            task_content = task_path.read_text(encoding="utf-8")
            task_content = task_content.replace(
                "| `docs/architecture.md` | `project-docs` | `existing` | `inspect` "
                "| Defines architecture. | Explorer read it. |",
                "| `docs/testing.md` | `project-docs` | `planned` | `modify` "
                "| Defines testing. | Explorer found the gap. |",
            )
            task_path.write_text(task_content, encoding="utf-8")

            errors = fixture.errors()

        self.assertEqual(errors, [])

    def test_task_documentation_must_be_present_in_plan_table(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            task_path = fixture.plan_dir / "tasks" / "002-test" / "TASK.md"
            content = task_path.read_text(encoding="utf-8")
            task_path.write_text(
                content.replace("`docs/architecture.md`", "`docs/testing.md`"),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(
            any(
                "'project-docs' 'docs/testing.md' is missing from the plan table"
                in error
                for error in errors
            )
        )

    def test_next_actions_must_list_every_available_action(self) -> None:
        errors = self.run_fixture(next_actions=[])
        self.assertTrue(any("Next Actions must exactly list" in error for error in errors))

    def test_blocked_task_and_plan_require_blockers(self) -> None:
        errors = self.run_fixture(
            statuses={"001-build": "blocked", "002-test": "not-started"},
            plan_status="blocked",
            plan_blocker="None.",
            task_blockers={"001-build": "None."},
        )
        self.assertTrue(any("blocked task must record" in error for error in errors))
        self.assertTrue(any("blocked plan must record" in error for error in errors))

    def test_completed_task_requires_checked_acceptance_criteria(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write(
                statuses={task_id: "completed" for task_id in PlanFixture.task_ids},
                plan_status="completed",
                plan_criteria_checked=True,
            )
            task_path = fixture.plan_dir / "tasks" / "001-build" / "TASK.md"
            content = task_path.read_text(encoding="utf-8")
            task_path.write_text(
                content.replace("- [x] The task result", "- [ ] The task result"),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(any("acceptance criterion checked" in error for error in errors))

    def test_task_status_table_must_match_task_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlanFixture(Path(temporary))
            fixture.write()
            progress_path = fixture.plan_dir / "PROGRESS.md"
            content = progress_path.read_text(encoding="utf-8")
            progress_path.write_text(
                content.replace(
                    "| `001-build` | `not-started`",
                    "| `001-build` | `in-progress`",
                ),
                encoding="utf-8",
            )
            errors = fixture.errors()

        self.assertTrue(any("but task progress is 'not-started'" in error for error in errors))

    def test_parallel_tasks_require_distinct_assignments(self) -> None:
        errors = self.run_fixture(
            statuses={"001-build": "in-progress", "002-test": "in-progress"},
            plan_status="in-progress",
            dependencies={"001-build": [], "002-test": []},
            assignments={
                "001-build": ("worktrees/demo-plan/shared", "task/shared"),
                "002-test": ("worktrees/demo-plan/shared", "task/shared"),
            },
        )
        self.assertTrue(any("share worktree" in error for error in errors))
        self.assertTrue(any("share branch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
