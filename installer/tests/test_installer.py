from __future__ import annotations

import hashlib
import json
import os
import posixpath
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


INSTALLER_DIRECTORY = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = INSTALLER_DIRECTORY.parent
sys.path.insert(0, str(INSTALLER_DIRECTORY))

import install  # noqa: E402


class SourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.actions = install.build_actions(FRAMEWORK_ROOT)
        cls.actions_by_path = {
            action.relative_path.as_posix(): action for action in cls.actions
        }

    def test_native_agents_and_portable_skills_validate(self) -> None:
        install.validate_sources(FRAMEWORK_ROOT)

    def test_build_contains_both_platforms_and_shared_instructions(self) -> None:
        paths = set(self.actions_by_path)
        for role in install.ROLE_MARKERS:
            self.assertIn(f".codex/agents/{role}.toml", paths)
            self.assertIn(f".claude/agents/{role}.md", paths)
        self.assertIn("AGENTS.md", paths)
        self.assertIn("CLAUDE.md", paths)
        self.assertEqual(b"@AGENTS.md\n", self.actions_by_path["CLAUDE.md"].content)
        self.assertIn("projects/README.md", paths)

    def test_skill_supporting_files_are_identical_generated_copies(self) -> None:
        codex_path = ".agents/skills/plan-management/scripts/validate_plan.py"
        claude_path = ".claude/skills/plan-management/scripts/validate_plan.py"
        self.assertEqual(
            self.actions_by_path[codex_path].content,
            self.actions_by_path[claude_path].content,
        )

    def test_commit_management_is_installed_and_required(self) -> None:
        self.assertIn(".agents/guides/commit-management.md", self.actions_by_path)
        self.assertIn(
            ".agents/skills/commit-management/SKILL.md", self.actions_by_path
        )
        self.assertIn(
            ".claude/skills/commit-management/SKILL.md", self.actions_by_path
        )
        workspace_instructions = self.actions_by_path["AGENTS.md"].content.decode(
            "utf-8"
        )
        self.assertIn("commit-management", workspace_instructions)

    def test_claude_skill_guide_links_resolve_to_installed_guides(self) -> None:
        action_paths = set(self.actions_by_path)
        checked_links = 0
        for path, action in self.actions_by_path.items():
            if not path.startswith(".claude/skills/") or not path.endswith("/SKILL.md"):
                continue
            text = action.content.decode("utf-8")
            self.assertIn("<!-- Generated from skills/", text)
            for token in text.split("(")[1:]:
                link = token.split(")", 1)[0]
                if not link.startswith("../../../.agents/guides/"):
                    continue
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), link))
                self.assertIn(resolved, action_paths)
                checked_links += 1
        self.assertGreater(checked_links, 0)

    def test_git_metadata_is_optional_outside_a_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual((None, None), install.git_metadata(Path(directory)))


class InstallerCliTests(unittest.TestCase):
    def run_installer(
        self,
        target: Path,
        *extra: str,
        cwd: Path | None = None,
        wrapper: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        command = (
            ["bash", str(INSTALLER_DIRECTORY / "install.sh")]
            if wrapper
            else [sys.executable, str(INSTALLER_DIRECTORY / "install.py")]
        )
        return subprocess.run(
            [*command, "--target", str(target), *extra],
            cwd=cwd or FRAMEWORK_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_dry_run_does_not_create_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "missing target"
            result = self.run_installer(target, "--dry-run", wrapper=True, cwd=Path(directory))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("CREATE .codex/agents/orchestrator.toml", result.stdout)
            self.assertIn("CREATE .claude/agents/orchestrator.md", result.stdout)
            self.assertFalse(target.exists())

    def test_real_install_manifest_and_idempotent_reinstall(self) -> None:
        actions = install.build_actions(FRAMEWORK_ROOT)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "workspace with spaces"
            first = self.run_installer(target)
            self.assertEqual(0, first.returncode, first.stderr)

            for action in actions:
                destination = target / action.relative_path
                self.assertTrue(destination.is_file(), action.relative_path)
                self.assertEqual(action.content, destination.read_bytes())

            manifest_path = target / install.MANIFEST_PATH
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("ai-dev-framework", manifest["framework"])
            self.assertEqual("0.1.0", manifest["framework_version"])
            self.assertEqual(1, manifest["schema_version"])
            self.assertNotIn(install.MANIFEST_PATH.as_posix(), {
                item["path"] for item in manifest["files"]
            })
            expected_hashes = {
                action.relative_path.as_posix(): hashlib.sha256(action.content).hexdigest()
                for action in actions
            }
            self.assertEqual(
                expected_hashes,
                {item["path"]: item["sha256"] for item in manifest["files"]},
            )

            tracked_paths = [target / action.relative_path for action in actions]
            tracked_paths.append(manifest_path)
            before_bytes = {path: path.read_bytes() for path in tracked_paths}
            before_mtimes = {path: path.stat().st_mtime_ns for path in tracked_paths}

            second = self.run_installer(target)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertIn("Installation is already up to date.", second.stdout)
            self.assertEqual(before_bytes, {path: path.read_bytes() for path in tracked_paths})
            self.assertEqual(
                before_mtimes,
                {path: path.stat().st_mtime_ns for path in tracked_paths},
            )

    def test_matching_partial_target_is_completed(self) -> None:
        actions = install.build_actions(FRAMEWORK_ROOT)
        agents_action = next(
            action for action in actions if action.relative_path == Path("AGENTS.md")
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "workspace"
            target.mkdir()
            (target / "AGENTS.md").write_bytes(agents_action.content)
            result = self.run_installer(target)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("UNCHANGED AGENTS.md", result.stdout)
            self.assertTrue((target / ".claude" / "agents" / "reviewer.md").is_file())

    def test_differing_file_aborts_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "workspace"
            target.mkdir()
            conflicting = target / "AGENTS.md"
            conflicting.write_text("user content\n", encoding="utf-8")

            result = self.run_installer(target)
            self.assertEqual(2, result.returncode)
            self.assertIn("CONFLICT AGENTS.md", result.stdout)
            self.assertIn("no files were written", result.stderr)
            self.assertEqual("user content\n", conflicting.read_text(encoding="utf-8"))
            self.assertFalse((target / "CLAUDE.md").exists())
            self.assertFalse((target / ".codex").exists())

    def test_invalid_existing_manifest_is_a_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "workspace"
            first = self.run_installer(target)
            self.assertEqual(0, first.returncode, first.stderr)
            manifest_path = target / install.MANIFEST_PATH
            manifest_path.write_text("not json\n", encoding="utf-8")

            result = self.run_installer(target)
            self.assertEqual(2, result.returncode)
            self.assertIn("CONFLICT .ai-dev-framework.json", result.stdout)
            self.assertEqual("not json\n", manifest_path.read_text(encoding="utf-8"))

    def test_target_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "not-a-directory"
            target.write_text("content\n", encoding="utf-8")
            result = self.run_installer(target)
            self.assertEqual(2, result.returncode)
            self.assertIn("Target is not a directory", result.stderr)

    def test_symlinked_target_is_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_target = root / "real-workspace"
            real_target.mkdir()
            target = root / "workspace"
            target.symlink_to(real_target, target_is_directory=True)

            result = self.run_installer(target)
            self.assertEqual(2, result.returncode)
            self.assertIn("Target is a symlink", result.stderr)
            self.assertEqual([], list(real_target.iterdir()))

    def test_symlinked_destination_is_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "workspace"
            target.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (target / ".codex").symlink_to(outside, target_is_directory=True)
            result = self.run_installer(target)
            self.assertEqual(2, result.returncode)
            self.assertIn("parent is a symlink", result.stdout)
            self.assertEqual([], list(outside.iterdir()))


if __name__ == "__main__":
    unittest.main()
