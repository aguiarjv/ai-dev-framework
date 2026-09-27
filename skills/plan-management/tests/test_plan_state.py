from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_validate_plan import PlanFixture


SCRIPT_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("plan_management_plan_state", SCRIPT_DIR / "plan_state.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PlanStateTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture = PlanFixture(Path(temporary.name))
        self.fixture.write(
            statuses={"001-build": "ready-for-review", "002-test": "not-started"},
            plan_status="in-progress",
        )
        self.review = "reviews/demo-plan/demo-plan-001-build-review-001.md"
        self.handoff = (
            "plans/demo-plan/tasks/001-build/handoffs/"
            "002-reviewer-to-orchestrator.md"
        )
        self.fixture._write_review("001-build", "clean")
        handoff_path = self.fixture.project_root / self.handoff
        handoff_path.write_text("# Clean reviewer handoff\n", encoding="utf-8")

    def transition(self, **kwargs: object) -> bool:
        return MODULE.transition_ready_for_integration(
            self.fixture.plan_dir, "001-build", self.review, self.handoff,
            **kwargs,
        )

    def test_transition_updates_three_files_and_is_idempotent(self) -> None:
        self.assertEqual([], self.fixture.errors())
        self.assertTrue(self.transition(accept_all=True))
        self.assertEqual([], self.fixture.errors())
        task = self.fixture.plan_dir / "tasks/001-build"
        self.assertIn("- [x] The task result", (task / "TASK.md").read_text())
        self.assertIn("status: ready-for-integration", (task / "PROGRESS.md").read_text())
        self.assertIn("`ready-for-integration`", (self.fixture.plan_dir / "PROGRESS.md").read_text())
        self.assertFalse(self.transition(accept_all=True))

    def test_dry_run_keeps_files_untouched(self) -> None:
        progress = self.fixture.plan_dir / "PROGRESS.md"
        before = progress.read_bytes()
        self.assertTrue(self.transition(accept_all=True, dry_run=True))
        self.assertEqual(before, progress.read_bytes())

    def test_unchecked_criteria_require_explicit_acceptance(self) -> None:
        with self.assertRaisesRegex(MODULE.TransitionError, "Acceptance criteria"):
            self.transition(accept_all=False)

    def test_bad_review_does_not_modify_files(self) -> None:
        self.fixture._write_review("001-build", "actionable-findings")
        progress = self.fixture.plan_dir / "PROGRESS.md"
        before = progress.read_bytes()
        with self.assertRaisesRegex(MODULE.TransitionError, "validation failed"):
            self.transition(accept_all=True)
        self.assertEqual(before, progress.read_bytes())

    def test_write_failure_rolls_back_prior_files(self) -> None:
        paths = [
            self.fixture.plan_dir / "tasks/001-build/TASK.md",
            self.fixture.plan_dir / "tasks/001-build/PROGRESS.md",
            self.fixture.plan_dir / "PROGRESS.md",
        ]
        before = {path: path.read_bytes() for path in paths}
        original_write = MODULE.atomic_write
        calls = 0

        def fail_second(path: Path, content: str) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated write failure")
            original_write(path, content)

        with patch.object(MODULE, "atomic_write", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "simulated write failure"):
                self.transition(accept_all=True)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})
        self.assertEqual([], self.fixture.errors())


if __name__ == "__main__":
    unittest.main()
