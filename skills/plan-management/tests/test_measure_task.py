from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "measure_task.py"
SPEC = importlib.util.spec_from_file_location("plan_management_measurement", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CodexUsageTests(unittest.TestCase):
    def test_reports_one_complete_turn(self) -> None:
        collector = MODULE.CodexUsage()
        collector.observe(
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 120,
                        "cached_input_tokens": 40,
                        "output_tokens": 25,
                    },
                }
            )
        )
        self.assertEqual(
            (
                "reported",
                {"input_tokens": 120, "cached_input_tokens": 40, "output_tokens": 25},
            ),
            collector.result(),
        )

    def test_missing_cached_usage_is_unknown(self) -> None:
        collector = MODULE.CodexUsage()
        collector.observe(
            json.dumps(
                {"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 3}}
            )
        )
        status, usage = collector.result()
        self.assertEqual("reported", status)
        self.assertIsNone(usage["cached_input_tokens"])

    def test_ambiguous_stream_never_claims_token_totals(self) -> None:
        collector = MODULE.CodexUsage()
        event = json.dumps(
            {"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 3}}
        )
        collector.observe(event)
        collector.observe(event)
        status, usage = collector.result()
        self.assertEqual("ambiguous", status)
        self.assertIsNone(usage["input_tokens"])


class MeasurementCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.task_dir = Path(self.temporary.name) / "001-build"
        self.task_dir.mkdir()
        (self.task_dir / "TASK.md").write_text("# Task\n", encoding="utf-8")
        (self.task_dir / "PROGRESS.md").write_text("# Progress\n", encoding="utf-8")

    def invoke(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_run_records_reported_usage_and_summary(self) -> None:
        event = {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "input_tokens_details": {"cached_tokens": 30},
                "output_tokens": 20,
            },
        }
        child_code = f"print({json.dumps(json.dumps(event))})"
        result = self.invoke(
            "run",
            "--target-dir",
            str(self.task_dir),
            "--phase",
            "implementation",
            "--role",
            "implementer",
            "--",
            sys.executable,
            "-c",
            child_code,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('"type": "turn.completed"', result.stdout)

        metrics = self.task_dir / "METRICS.jsonl"
        record = json.loads(metrics.read_text(encoding="utf-8"))
        self.assertEqual("reported", record["usage_status"])
        self.assertEqual(100, record["usage"]["input_tokens"])
        self.assertEqual(30, record["usage"]["cached_input_tokens"])
        self.assertEqual(20, record["usage"]["output_tokens"])
        self.assertGreaterEqual(record["elapsed_ms"], 0)

        summary = self.invoke("summarize", "--target-dir", str(self.task_dir), "--json")
        self.assertEqual(0, summary.returncode, summary.stderr)
        phase = json.loads(summary.stdout)["phases"]["implementation"]
        self.assertEqual(1, phase["reported_usage_runs"])
        self.assertEqual(100, phase["known_input_tokens"])

    def test_failed_run_keeps_time_and_unknown_usage(self) -> None:
        result = self.invoke(
            "run",
            "--target-dir",
            str(self.task_dir),
            "--phase",
            "validation",
            "--role",
            "orchestrator",
            "--",
            sys.executable,
            "-c",
            "raise SystemExit(7)",
        )
        self.assertEqual(7, result.returncode)
        record = json.loads((self.task_dir / "METRICS.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(7, record["exit_code"])
        self.assertEqual("unavailable", record["usage_status"])
        self.assertIsNone(record["usage"]["input_tokens"])


if __name__ == "__main__":
    unittest.main()
