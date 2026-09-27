from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "claude_usage.py"
SPEC = importlib.util.spec_from_file_location("plan_management_claude_usage", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ClaudeUsageTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write_event(self, path: Path, identifier: str, *, output: int, cached: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "type": "assistant",
            "timestamp": "2026-09-27T10:00:00Z",
            "prompt": "private prompt",
            "message": {
                "id": identifier,
                "model": "claude-example",
                "content": "private answer",
                "usage": {
                    "input_tokens": 10,
                    "cache_creation_input_tokens": 5,
                    "cache_read_input_tokens": cached,
                    "output_tokens": output,
                },
            },
        }
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event) + "\n")

    def test_deduplicates_message_updates_and_separates_cache_classes(self) -> None:
        main = self.root / "session.jsonl"
        child = self.root / "subagents" / "agent-one.jsonl"
        self.write_event(main, "msg-1", output=1, cached=210_000)
        self.write_event(main, "msg-1", output=3, cached=210_000)
        self.write_event(child, "msg-2", output=2, cached=20)
        result = MODULE.summarize(self.root)
        self.assertEqual(2, result["overall"]["requests"])
        self.assertEqual(5, result["overall"]["output_tokens"])
        self.assertEqual(210_020, result["overall"]["cache_read_input_tokens"])
        self.assertEqual(1, result["overall"]["requests_above_200k_context"])
        self.assertEqual(210_015, result["overall"]["context_input_tokens_above_200k"])
        self.assertEqual(1, result["groups"]["subagent:claude-example"]["requests"])
        self.assertNotIn("private", json.dumps(result))

    def test_missing_usage_and_corrupt_tail_are_ignored(self) -> None:
        path = self.root / "session.jsonl"
        path.write_text('{"type":"assistant","message":{"id":"x"}}\n{', encoding="utf-8")
        result = MODULE.summarize(self.root)
        self.assertEqual(1, result["overall"]["files"])
        self.assertEqual(0, result["overall"]["requests"])
        self.assertEqual("unavailable", result["usage_status"])

    def test_no_transcripts_is_reported_as_empty_not_zero_usage_evidence(self) -> None:
        self.assertEqual(0, MODULE.summarize(self.root)["overall"]["files"])


if __name__ == "__main__":
    unittest.main()
