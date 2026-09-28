from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


INSTALLER_DIRECTORY = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = INSTALLER_DIRECTORY.parent
sys.path.insert(0, str(INSTALLER_DIRECTORY))

import install  # noqa: E402
import update  # noqa: E402


class UpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name) / "workspace"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, install.install(self.target))
        self.actions = install.build_actions()
        self.version = (FRAMEWORK_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.manifest_path = self.target / install.MANIFEST_PATH

    def manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def write_manifest(self, data: dict) -> None:
        self.manifest_path.write_text(json.dumps(data) + "\n", encoding="utf-8")

    def older_version(self) -> str:
        major, minor, patch = map(int, self.version.split("."))
        self.assertGreater(patch, 0)
        return f"{major}.{minor}.{patch - 1}"

    def test_preview_apply_add_update_remove_and_preserve_project(self) -> None:
        data = self.manifest()
        data["framework_version"] = self.older_version()
        old_agent = b"# Previous generated instructions\n"
        (self.target / "AGENTS.md").write_bytes(old_agent)
        for item in data["files"]:
            if item["path"] == "AGENTS.md":
                item["sha256"] = hashlib.sha256(old_agent).hexdigest()
        added = ".agents/guides/commit-management.md"
        (self.target / added).unlink()
        data["files"] = [item for item in data["files"] if item["path"] != added]
        obsolete = ".agents/guides/obsolete.md"
        (self.target / obsolete).write_text("Old guide\n", encoding="utf-8")
        data["files"].append({
            "path": obsolete,
            "sha256": hashlib.sha256(b"Old guide\n").hexdigest(),
        })
        self.write_manifest(data)
        project_file = self.target / "projects/sample/worktrees/main/docs/source.md"
        project_file.parent.mkdir(parents=True)
        project_file.write_text("Project docs\n", encoding="utf-8")

        plan = update.plan_update(self.target, self.actions, self.version)
        states = {change.path.as_posix(): change.state for change in plan.changes}
        self.assertEqual("UPDATE", states["AGENTS.md"])
        self.assertEqual("CREATE", states[added])
        self.assertEqual("REMOVE", states[obsolete])
        self.assertEqual("# Previous generated instructions\n", (self.target / "AGENTS.md").read_text())
        self.assertFalse((self.target / added).exists())

        update.apply_update(self.target, plan)
        self.assertEqual(next(action.content for action in self.actions if action.relative_path == Path("AGENTS.md")),
                         (self.target / "AGENTS.md").read_bytes())
        self.assertTrue((self.target / added).is_file())
        self.assertFalse((self.target / obsolete).exists())
        self.assertEqual("Project docs\n", project_file.read_text())
        self.assertEqual(self.version, self.manifest()["framework_version"])
        self.assertIsNone(update.plan_update(self.target, self.actions, self.version).new_manifest)

    def test_cli_preview_apply_and_repeat_are_idempotent(self) -> None:
        data = self.manifest()
        data["framework_version"] = self.older_version()
        self.write_manifest(data)
        before = self.manifest_path.read_bytes()
        command = [sys.executable, str(INSTALLER_DIRECTORY / "update.py"), "--target", str(self.target)]
        preview = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(0, preview.returncode, preview.stderr)
        self.assertIn("Preview complete", preview.stdout)
        self.assertEqual(before, self.manifest_path.read_bytes())
        applied = subprocess.run([*command, "--apply"], capture_output=True, text=True, check=False)
        self.assertEqual(0, applied.returncode, applied.stderr)
        self.assertEqual(self.version, self.manifest()["framework_version"])
        after = self.manifest_path.read_bytes()
        repeated = subprocess.run([*command, "--apply"], capture_output=True, text=True, check=False)
        self.assertEqual(0, repeated.returncode, repeated.stderr)
        self.assertIn("already up to date", repeated.stdout)
        self.assertEqual(after, self.manifest_path.read_bytes())

    def test_local_edit_and_new_path_collision_stop_before_writes(self) -> None:
        data = self.manifest()
        data["framework_version"] = self.older_version()
        self.write_manifest(data)
        (self.target / "AGENTS.md").write_text("Local edit\n", encoding="utf-8")
        before = self.manifest_path.read_bytes()
        with self.assertRaisesRegex(update.UpdateError, "was modified"):
            update.plan_update(self.target, self.actions, self.version)
        self.assertEqual(before, self.manifest_path.read_bytes())
        self.assertFalse((self.target / update.JOURNAL).exists())

        (self.target / "AGENTS.md").write_bytes(next(
            action.content for action in self.actions if action.relative_path == Path("AGENTS.md")
        ))
        new = ".agents/guides/commit-management.md"
        data["files"] = [item for item in data["files"] if item["path"] != new]
        self.write_manifest(data)
        with self.assertRaisesRegex(update.UpdateError, "already exists"):
            update.plan_update(self.target, self.actions, self.version)

    def test_unsafe_manifest_path_is_rejected(self) -> None:
        data = self.manifest()
        data["files"][0]["path"] = "../outside"
        self.write_manifest(data)
        with self.assertRaisesRegex(update.UpdateError, "Unsafe manifest path"):
            update.plan_update(self.target, self.actions, self.version)
        self.assertFalse((self.target / update.JOURNAL).exists())

    def test_symlink_and_downgrade_are_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        data = self.manifest()
        data["framework_version"] = "99.0.0"
        self.write_manifest(data)
        with self.assertRaisesRegex(update.UpdateError, "downgrade"):
            update.plan_update(self.target, self.actions, self.version)
        data["framework_version"] = self.older_version()
        self.write_manifest(data)
        parent = self.target / ".agents/guides"
        outside = Path(self.temporary.name) / "outside"
        parent.rename(outside)
        parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(update.UpdateError, "symlink"):
            update.plan_update(self.target, self.actions, self.version)

    def test_legacy_project_layout_requires_migration_first(self) -> None:
        legacy = self.target / "projects/sample/docs"
        legacy.mkdir(parents=True)
        with self.assertRaisesRegex(update.UpdateError, "run installer/migrate.py first"):
            update.update(self.target)
        self.assertFalse((self.target / update.JOURNAL).exists())

    def test_interrupted_create_recovers_new_directories(self) -> None:
        new_path = Path(".agents/skills/new-skill/SKILL.md")
        actions = [*self.actions, install.InstallAction(new_path, b"# New skill\n")]
        plan = update.plan_update(self.target, actions, self.version)
        original = update.atomic_write

        def interrupt_after_create(path: Path, content: bytes, mode: int) -> None:
            original(path, content, mode)
            if path == self.target / new_path:
                raise KeyboardInterrupt

        with patch.object(update, "atomic_write", side_effect=interrupt_after_create):
            with self.assertRaises(KeyboardInterrupt):
                update.apply_update(self.target, plan)
        self.assertTrue((self.target / new_path).is_file())
        update.recover(self.target)
        self.assertFalse((self.target / new_path).exists())
        self.assertFalse((self.target / new_path.parent).exists())
        self.assertFalse((self.target / update.JOURNAL).exists())

    def test_write_failure_rolls_back_files_and_manifest(self) -> None:
        obsolete = ".agents/guides/obsolete.md"
        (self.target / obsolete).write_text("Old guide\n", encoding="utf-8")
        data = self.manifest()
        data["files"].append({
            "path": obsolete,
            "sha256": hashlib.sha256(b"Old guide\n").hexdigest(),
        })
        self.write_manifest(data)
        changed = []
        for action in self.actions:
            if action.relative_path in {Path("AGENTS.md"), Path("CLAUDE.md")}:
                changed.append(install.InstallAction(action.relative_path, b"Replacement\n", action.mode))
            else:
                changed.append(action)
        plan = update.plan_update(self.target, changed, self.version)
        before = {name: (self.target / name).read_bytes() for name in ("AGENTS.md", "CLAUDE.md")}
        manifest = self.manifest_path.read_bytes()
        original = update.atomic_write
        failed = False

        def fail_once(path: Path, content: bytes, mode: int) -> None:
            nonlocal failed
            if path == self.target / "CLAUDE.md" and not failed:
                failed = True
                raise OSError("simulated write failure")
            original(path, content, mode)

        with patch.object(update, "atomic_write", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "simulated write failure"):
                update.apply_update(self.target, plan)
        self.assertEqual(before, {name: (self.target / name).read_bytes() for name in before})
        self.assertEqual("Old guide\n", (self.target / obsolete).read_text())
        self.assertEqual(manifest, self.manifest_path.read_bytes())
        self.assertFalse((self.target / update.JOURNAL).exists())

    def test_interrupted_apply_recovers_before_retry(self) -> None:
        data = self.manifest()
        data["framework_version"] = self.older_version()
        old_agent = b"# Old instructions\n"
        (self.target / "AGENTS.md").write_bytes(old_agent)
        for item in data["files"]:
            if item["path"] == "AGENTS.md":
                item["sha256"] = hashlib.sha256(old_agent).hexdigest()
        self.write_manifest(data)
        plan = update.plan_update(self.target, self.actions, self.version)
        original = update.atomic_write

        def interrupt(path: Path, content: bytes, mode: int) -> None:
            if path == self.target / "AGENTS.md":
                raise KeyboardInterrupt
            original(path, content, mode)

        with patch.object(update, "atomic_write", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                update.apply_update(self.target, plan)
        self.assertTrue((self.target / update.JOURNAL).exists())
        with self.assertRaisesRegex(update.UpdateError, "Interrupted update"):
            update.update(self.target)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, update.update(self.target, apply=True))
        self.assertFalse((self.target / update.JOURNAL).exists())
        self.assertEqual(self.version, self.manifest()["framework_version"])


if __name__ == "__main__":
    unittest.main()
