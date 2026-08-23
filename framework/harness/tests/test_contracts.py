#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts import validate_contract, validate_state_transition  # noqa: E402


class WorkflowContractTests(unittest.TestCase):
    def test_valid_task_contract_has_a_usable_dependency_graph(self) -> None:
        errors = validate_contract(valid_task(), "task-contract.schema.json")
        self.assertEqual(errors, [])

    def test_task_contract_rejects_unknown_dependencies_and_cycles(self) -> None:
        document = valid_task()
        document["subtasks"][0]["depends_on"] = ["T-2"]
        document["subtasks"][1]["depends_on"] = ["T-1"]
        document["subtasks"].append(
            {
                "id": "T-3",
                "title": "Unreachable task",
                "task_type": "test",
                "owner": "implementer",
                "status": "pending",
                "depends_on": ["T-404"],
                "paths": [],
                "acceptance_criteria": ["AC-1"],
                "verification": ["python3 -m unittest"],
                "parallelizable": False,
                "done_when": "The test is present.",
            }
        )
        errors = validate_contract(document, "task-contract.schema.json")
        self.assertTrue(any("unknown task" in error for error in errors))
        self.assertTrue(any("dependency cycle" in error for error in errors))

    def test_task_contract_rejects_uncovered_acceptance_criteria(self) -> None:
        document = valid_task()
        document["acceptance_criteria"].append(
            {
                "id": "AC-2",
                "statement": "The edge case is covered.",
                "verification": ["python3 -m unittest"],
            }
        )
        errors = validate_contract(document, "task-contract.schema.json")
        self.assertTrue(any("not assigned to a subtask" in error for error in errors))

    def test_handoff_requires_evidence_for_facts(self) -> None:
        document = {
            "schema_version": "1",
            "handoff_id": "H-1",
            "task_id": "sample-task",
            "subtask_id": "T-1",
            "from_agent": "planner",
            "to_agent": "implementer",
            "phase": "implementation",
            "goal": "Implement the assigned slice.",
            "scope": {"in": ["src/feature.py"], "out": ["unrelated cleanup"]},
            "source": {
                "task_spec": "docs/tasks/sample-task.md",
                "progress_file": ".local/tasks/sample-task/progress.md",
                "worktree": "../sample-task-worktree",
                "branch": "ai/sample-task",
                "revision": "abc123",
            },
            "facts": [{"statement": "The function exists.", "evidence": []}],
            "assumptions": [],
            "constraints": [],
            "acceptance_criteria": ["AC-1"],
            "verification": ["python3 -m unittest"],
            "required_output": ["agent-result"],
        }
        errors = validate_contract(document, "handoff.schema.json")
        self.assertTrue(any("at least 1 items" in error for error in errors))

    def test_review_finding_requires_actionable_evidence_and_fix(self) -> None:
        document = {
            "schema_version": "1",
            "finding_id": "F-1",
            "severity": "high",
            "confidence": "confirmed",
            "status": "open",
            "location": "src/feature.py:42",
            "criterion_ids": ["AC-1"],
            "impact": "The request can bypass validation.",
            "evidence": ["The changed branch skips the validator."],
            "required_fix": "Validate the request before persistence.",
            "verification": ["python3 -m unittest tests/test_feature.py"],
        }
        self.assertEqual(validate_contract(document, "review-finding.schema.json"), [])

    def test_workflow_transition_allows_review_remediation_loop_but_not_skips(self) -> None:
        self.assertEqual(validate_state_transition("review", "remediation"), [])
        self.assertEqual(validate_state_transition("remediation", "review"), [])
        self.assertTrue(validate_state_transition("planning", "done"))
        self.assertTrue(validate_state_transition("blocked", "implementation"))


def valid_task() -> dict:
    return {
        "schema_version": "1",
        "task_id": "sample-task",
        "title": "Sample task",
        "status": "approved",
        "task_type": "backend",
        "objective": "Deliver the sample behavior.",
        "scope": {"in": ["the sample behavior"], "out": ["unrelated cleanup"]},
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "statement": "The behavior works.",
                "verification": ["python3 -m unittest"],
            }
        ],
        "subtasks": [
            {
                "id": "T-1",
                "title": "Implement behavior",
                "task_type": "backend",
                "owner": "implementer",
                "status": "pending",
                "depends_on": [],
                "paths": ["src/feature.py"],
                "acceptance_criteria": ["AC-1"],
                "verification": ["python3 -m unittest"],
                "parallelizable": False,
                "done_when": "The behavior and regression test pass.",
            },
            {
                "id": "T-2",
                "title": "Verify behavior",
                "task_type": "test",
                "owner": "implementer",
                "status": "pending",
                "depends_on": ["T-1"],
                "paths": ["tests/test_feature.py"],
                "acceptance_criteria": ["AC-1"],
                "verification": ["python3 -m unittest"],
                "parallelizable": False,
                "done_when": "The focused test passes.",
            },
        ],
        "risk": {"level": "medium", "areas": ["behavior"]},
        "review_policy": {"required": True, "max_remediation_cycles": 2, "slices": ["correctness"]},
    }


if __name__ == "__main__":
    unittest.main()
