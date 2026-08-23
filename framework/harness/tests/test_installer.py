#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from install import render_codex_agent, source_files  # noqa: E402


class InstallerContractTests(unittest.TestCase):
    def test_source_files_excludes_interpreter_caches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "keep.txt").write_text("keep", encoding="utf-8")
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "ignored.pyc").write_bytes(b"cache")
            self.assertEqual([root / "keep.txt"], source_files(root))

    def test_codex_adapter_preserves_portable_policy_metadata(self) -> None:
        rendered = render_codex_agent(
            {
                "name": "sample-agent",
                "description": "Sample agent",
                "tools": "read",
                "permission_mode": "read-only",
            },
            "Use the workflow contract.",
        )
        self.assertIn("Portable agent contract:", rendered)
        self.assertIn("- tools: read", rendered)
        self.assertIn("- permission_mode: read-only", rendered)


if __name__ == "__main__":
    unittest.main()
