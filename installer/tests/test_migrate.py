from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


INSTALLER_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(INSTALLER_DIRECTORY))

import install  # noqa: E402
import migrate  # noqa: E402


class MigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name) / "workspace"
        self.target.mkdir()
        actions = install.build_actions()
        inventory = []
        for action in actions:
            path = self.target / action.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            content = action.content
            if action.relative_path == Path("AGENTS.md"):
                content = content.replace(b"workspace-docs/", b"docs/")
            path.write_bytes(content)
            inventory.append({
                "path": action.relative_path.as_posix(),
                "sha256": hashlib.sha256(content).hexdigest(),
            })
        manifest = {
            "framework": install.FRAMEWORK_NAME,
            "schema_version": install.MANIFEST_SCHEMA_VERSION,
            "framework_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00+00:00",
            "source_revision": None,
            "source_dirty": None,
            "files": inventory,
        }
        (self.target / install.MANIFEST_PATH).write_text(json.dumps(manifest), encoding="utf-8")
        project = self.target / "projects" / "sample"
        project.mkdir()
        (project / "AGENTS.md").write_text(
            "# Sample\n\n## Project Paths\n\n- Project documentation: `docs/`\n"
            "- Active and completed plans: `plans/`\n\n## Other Rules\n\n"
            "- The checkout may have `docs/` of its own.\n",
            encoding="utf-8",
        )
        (project / "README.md").write_text("See `docs/` in the checkout.\n", encoding="utf-8")
        for name in migrate.FOLDERS:
            (project / name).mkdir()
        (project / "docs" / "adrs").mkdir()
        (project / "docs" / "adrs" / "0001-design.md").write_text("# Design\n", encoding="utf-8")
        (project / "scripts" / "helper.py").write_text(
            "from pathlib import Path\nfolder = Path('plans')\n", encoding="utf-8"
        )
        (project / "reviews" / "example").mkdir()
        (project / "reviews" / "example" / "review.md").write_text("# Review\n", encoding="utf-8")
        for relative in ("example", "done/finished"):
            plan = project / "plans" / relative
            plan.mkdir(parents=True)
            plan_id = plan.name
            (plan / "PLAN.md").write_text(
                f'latest_review: "reviews/{plan_id}/review.md"\n'
                f'latest_handoff: "plans/{plan_id}/handoffs/one.md"\n'
                "| `docs/architecture.md` | `project-docs` | existing |\n"
                "| `docs/source.md` | `repo-file` | existing |\n"
                "| `docs/adrs/repo-decision.md` | `repo-file` | existing |\n"
                "## Architecture Decisions\n"
                "| Decision | `docs/adrs/0001-design.md` |\n",
                encoding="utf-8",
            )
        checkout = project / "worktrees" / "main" / "docs"
        checkout.mkdir(parents=True)
        (checkout / "source.md").write_text("Repository docs\n", encoding="utf-8")
        self.project = project

    def run_migration(self, apply: bool) -> str:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(0, migrate.migrate(self.target, apply))
        return output.getvalue()

    def test_preview_and_apply_preserve_checkout_paths(self) -> None:
        preview = self.run_migration(False)
        self.assertIn("MOVE projects/sample/docs -> projects/sample/workspace-docs", preview)
        self.assertIn("REVIEW", preview)
        self.assertIn("workspace-scripts/helper.py", preview)
        self.assertTrue((self.project / "docs").is_dir())
        self.assertFalse((self.project / "workspace-docs").exists())

        self.run_migration(True)
        for name in migrate.FOLDERS:
            self.assertFalse((self.project / name).exists())
            self.assertTrue((self.project / f"workspace-{name}").is_dir())
        self.assertTrue((self.project / "worktrees/main/docs/source.md").is_file())
        self.assertIn("`workspace-docs/`", (self.project / "AGENTS.md").read_text())
        self.assertIn("`docs/` of its own", (self.project / "AGENTS.md").read_text())
        text = (self.project / "workspace-plans/example/PLAN.md").read_text()
        self.assertIn("workspace-reviews/example/review.md", text)
        self.assertIn("workspace-plans/example/handoffs/one.md", text)
        self.assertIn("`workspace-docs/architecture.md`", text)
        self.assertIn("`workspace-docs/adrs/0001-design.md`", text)
        self.assertIn("`docs/source.md` | `repo-file`", text)
        self.assertIn("`docs/adrs/repo-decision.md` | `repo-file`", text)
        self.assertTrue((self.project / "workspace-plans/done/finished/PLAN.md").is_file())
        manifest = json.loads((self.target / install.MANIFEST_PATH).read_text())
        self.assertEqual("0.2.0", manifest["framework_version"])
        self.assertIn("already migrated", self.run_migration(True))

    def test_collision_and_modified_install_stop_before_writes(self) -> None:
        (self.project / "workspace-docs").mkdir()
        with self.assertRaises(migrate.MigrationError):
            migrate.migrate(self.target, True)
        self.assertTrue((self.project / "docs").is_dir())
        self.assertFalse((self.target / migrate.JOURNAL).exists())
        (self.project / "workspace-docs").rmdir()
        (self.target / "AGENTS.md").write_text("Modified\n", encoding="utf-8")
        with self.assertRaisesRegex(migrate.MigrationError, "was modified"):
            migrate.migrate(self.target, True)
        self.assertTrue((self.project / "docs").is_dir())

    def test_symlinked_metadata_is_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        (self.project / "docs" / "linked").symlink_to(self.project / "worktrees")
        with self.assertRaisesRegex(migrate.MigrationError, "symlink"):
            migrate.migrate(self.target, True)
        self.assertFalse((self.project / "workspace-docs").exists())

    def test_interrupted_apply_recovers_then_retries(self) -> None:
        original = migrate.atomic_write

        def interrupt_on_update(path: Path, content: bytes, mode: int) -> None:
            if path == self.target / "AGENTS.md":
                raise KeyboardInterrupt
            original(path, content, mode)

        with contextlib.redirect_stdout(io.StringIO()), patch.object(
            migrate, "atomic_write", side_effect=interrupt_on_update
        ):
            with self.assertRaises(KeyboardInterrupt):
                migrate.migrate(self.target, True)
        self.assertTrue((self.target / migrate.JOURNAL).exists())
        self.assertTrue((self.project / "workspace-docs").exists())
        self.run_migration(True)
        self.assertFalse((self.target / migrate.JOURNAL).exists())
        self.assertTrue((self.project / "workspace-docs").exists())
        self.assertFalse((self.project / "docs").exists())

    def test_write_failure_rolls_back(self) -> None:
        original = migrate.atomic_write
        interrupted = False

        def fail_once(path: Path, content: bytes, mode: int) -> None:
            nonlocal interrupted
            if path == self.project / "AGENTS.md" and not interrupted:
                interrupted = True
                raise OSError("simulated write failure")
            original(path, content, mode)

        with contextlib.redirect_stdout(io.StringIO()), patch.object(
            migrate, "atomic_write", side_effect=fail_once
        ):
            with self.assertRaisesRegex(OSError, "simulated write failure"):
                migrate.migrate(self.target, True)
        self.assertFalse((self.target / migrate.JOURNAL).exists())
        self.assertTrue((self.project / "docs").is_dir())
        self.assertFalse((self.project / "workspace-docs").exists())
        self.assertIn("`docs/`", (self.project / "AGENTS.md").read_text())
        manifest = json.loads((self.target / install.MANIFEST_PATH).read_text())
        self.assertEqual("0.1.0", manifest["framework_version"])

    def test_manifest_is_upgraded_when_files_already_match(self) -> None:
        shutil.rmtree(self.project)
        action = next(
            item for item in install.build_actions() if item.relative_path == Path("AGENTS.md")
        )
        (self.target / "AGENTS.md").write_bytes(action.content)
        manifest_path = self.target / install.MANIFEST_PATH
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest["files"]:
            if item["path"] == "AGENTS.md":
                item["sha256"] = hashlib.sha256(action.content).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.run_migration(True)
        upgraded = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("0.2.0", upgraded["framework_version"])


if __name__ == "__main__":
    unittest.main()
