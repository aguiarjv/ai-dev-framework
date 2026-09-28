from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "native_metrics.py"
SPEC = importlib.util.spec_from_file_location("plan_management_native_metrics", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NativeMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.worktree = (
            self.root
            / "projects/tracker/worktrees/example-plan/001-example/apps/web"
        )
        self.worktree.mkdir(parents=True)
        task = self.root / "projects/tracker/workspace-plans/example-plan/tasks/001-example"
        task.mkdir(parents=True)
        (task.parent.parent / "PLAN.md").write_text("# Plan\n", encoding="utf-8")
        (task / "TASK.md").write_text("# Task\n", encoding="utf-8")

    def event(self, name: str, **extra: object) -> dict[str, object]:
        return {
            "hook_event_name": name,
            "session_id": "parent-session",
            "turn_id": "parent-turn",
            "cwd": str(self.worktree),
            "model": "example-model",
            "prompt": "private prompt must not be retained",
            **extra,
        }

    def records(self) -> list[dict[str, object]]:
        path = self.root / MODULE.METRICS_RELATIVE
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_subagent_run_records_time_and_numeric_usage_only(self) -> None:
        transcript = self.root / "subagent.jsonl"
        transcript.write_text(
            json.dumps({
                "type": "token_usage_record",
                "payload": {
                    "thread_token_usage": {
                        "input_tokens": 120,
                        "cached_input_tokens": 40,
                        "output_tokens": 25,
                        "reasoning_output_tokens": 5,
                        "total_tokens": 145,
                    }
                },
            }) + "\n",
            encoding="utf-8",
        )
        self.assertTrue(MODULE.record_hook(
            self.root,
            self.event("SubagentStart", agent_id="agent-1", agent_type="implementer"),
            "2026-09-27T10:00:00Z",
        ))
        self.assertTrue(MODULE.record_hook(
            self.root,
            self.event(
                "SubagentStop", agent_id="agent-1", agent_type="implementer",
                agent_transcript_path=str(transcript),
            ),
            "2026-09-27T10:00:03Z",
        ))
        records = self.records()
        self.assertEqual(2, len(records))
        self.assertEqual({"project": "tracker", "plan": "example-plan", "task": "001-example"},
                         {key: records[1][key] for key in ("project", "plan", "task")})
        self.assertEqual("observed", records[1]["usage_status"])
        self.assertEqual("example-model", records[1]["model"])
        self.assertNotIn("private prompt", json.dumps(records))
        self.assertNotIn(str(transcript), json.dumps(records))
        summary = MODULE.summarize(self.root)
        self.assertEqual(3000, summary["roles"]["implementer"]["elapsed_ms"])
        self.assertEqual(120, summary["roles"]["implementer"]["known_input_tokens"])
        self.assertEqual(25, summary["roles"]["implementer"]["known_output_tokens"])

    def test_missing_or_unrecognized_usage_stays_unknown(self) -> None:
        transcript = self.root / "unknown.jsonl"
        transcript.write_text('{"type":"something-else"}\n', encoding="utf-8")
        MODULE.record_hook(
            self.root,
            self.event("SubagentStop", agent_id="agent-2", agent_type="reviewer",
                       agent_transcript_path=str(transcript)),
        )
        record = self.records()[0]
        self.assertEqual("unavailable", record["usage_status"])
        self.assertIsNone(record["usage"])
        group = MODULE.summarize(self.root)["roles"]["reviewer"]
        self.assertEqual(1, group["missing_start"])
        self.assertEqual(1, group["missing_usage"])
        self.assertEqual(0, group["known_input_tokens"])

    def test_root_usage_requires_matching_turn(self) -> None:
        transcript = self.root / "root.jsonl"
        lines = []
        for turn, input_tokens in (("earlier-turn", 900), ("parent-turn", 30)):
            lines.append(json.dumps({
                "type": "token_usage_record",
                "payload": {
                    "turn_id": turn,
                    "turn_token_usage": {
                        "input_tokens": input_tokens,
                        "cached_input_tokens": 0,
                        "output_tokens": 7,
                    },
                },
            }))
        transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
        MODULE.record_hook(self.root, self.event("UserPromptSubmit"), "2026-09-27T10:00:00Z")
        MODULE.record_hook(self.root, self.event("Stop", transcript_path=str(transcript)),
                           "2026-09-27T10:00:01Z")
        self.assertEqual(30, self.records()[1]["usage"]["input_tokens"])
        self.assertEqual(30, MODULE.summarize(self.root)["roles"]["orchestrator"]["known_input_tokens"])


if __name__ == "__main__":
    unittest.main()
