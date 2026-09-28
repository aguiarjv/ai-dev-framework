#!/usr/bin/env python3
"""Preview or apply an update to an installed AI Dev Framework workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import install


JOURNAL = ".ai-dev-framework-update"
MANAGED_FILES = {
    "AGENTS.md", "CLAUDE.md", "projects/README.md",
    ".codex/hooks.json", ".claude/settings.json",
}
MANAGED_PREFIXES = (
    ".codex/agents/", ".claude/agents/", ".claude/skills/",
    ".agents/guides/", ".agents/skills/",
)
LEGACY_FOLDERS = ("docs", "plans", "scripts", "reviews", "reports")


class UpdateError(ValueError):
    pass


@dataclass(frozen=True)
class FileChange:
    path: Path
    state: str
    content: bytes | None
    mode: int | None
    old_digest: str | None


@dataclass(frozen=True)
class UpdatePlan:
    changes: tuple[FileChange, ...]
    old_manifest: bytes
    new_manifest: bytes | None
    old_version: str
    new_version: str


def safe_relative(value: str) -> Path:
    if (not value or value.startswith("/") or "\\" in value or "\x00" in value
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise UpdateError(f"Unsafe manifest path: {value!r}")
    if value not in MANAGED_FILES and not value.startswith(MANAGED_PREFIXES):
        raise UpdateError(f"Path is outside the managed file set: {value}")
    return Path(value)


def regular_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise UpdateError(f"Expected a regular file: {path}")
    return path.read_bytes()


def check_parents(target: Path, relative: Path) -> None:
    cursor = target
    for part in relative.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise UpdateError(f"Parent is a symlink: {cursor}")
        if cursor.exists() and not cursor.is_dir():
            raise UpdateError(f"Parent is not a directory: {cursor}")


def require_current_layout(target: Path) -> None:
    projects = target / "projects"
    if projects.is_symlink() or not projects.is_dir():
        raise UpdateError(f"Expected a regular projects directory: {projects}")
    for project in projects.iterdir():
        if project.name == "README.md":
            continue
        if project.is_symlink():
            raise UpdateError(f"Unexpected projects entry: {project}")
        if not project.is_dir():
            continue
        for name in LEGACY_FOLDERS:
            old = project / name
            if old.exists() or old.is_symlink():
                raise UpdateError(f"Legacy workspace folder found: {old}; run installer/migrate.py first")


def load_manifest(target: Path) -> tuple[dict[str, object], dict[str, str], bytes]:
    path = target / install.MANIFEST_PATH
    content = regular_bytes(path)
    try:
        data = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpdateError(f"Invalid framework manifest: {error}") from error
    fields = {
        "framework", "schema_version", "framework_version", "installed_at",
        "source_revision", "source_dirty", "files",
    }
    if not isinstance(data, dict) or set(data) != fields:
        raise UpdateError("Unsupported framework manifest fields")
    if (data["framework"] != install.FRAMEWORK_NAME
            or type(data["schema_version"]) is not int
            or data["schema_version"] != install.MANIFEST_SCHEMA_VERSION):
        raise UpdateError("Unsupported framework manifest")
    version = data["framework_version"]
    if not isinstance(version, str) or re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        raise UpdateError("Invalid installed framework version")
    timestamp = data["installed_at"]
    try:
        if not isinstance(timestamp, str) or datetime.fromisoformat(timestamp).tzinfo is None:
            raise ValueError
    except ValueError as error:
        raise UpdateError("Invalid framework installation time") from error
    revision = data["source_revision"]
    if revision is not None and (
        not isinstance(revision, str)
        or re.fullmatch(r"[0-9a-fA-F]{40,64}", revision) is None
    ):
        raise UpdateError("Invalid framework source revision")
    if data["source_dirty"] is not None and not isinstance(data["source_dirty"], bool):
        raise UpdateError("Invalid framework source dirty state")
    inventory = data["files"]
    if not isinstance(inventory, list):
        raise UpdateError("Invalid framework file inventory")
    old: dict[str, str] = {}
    for item in inventory:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise UpdateError("Invalid framework file inventory")
        name, digest = item["path"], item["sha256"]
        if not isinstance(name, str) or not isinstance(digest, str):
            raise UpdateError("Invalid framework file inventory")
        safe_relative(name)
        if name in old or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise UpdateError("Duplicate path or invalid checksum in manifest")
        old[name] = digest
    return data, old, content


def plan_update(
    target: Path,
    actions: list[install.InstallAction],
    version: str,
    root: Path | None = None,
) -> UpdatePlan:
    if target.is_symlink() or not target.is_dir():
        raise UpdateError(f"Target must be a regular directory: {target}")
    data, old, old_manifest = load_manifest(target)
    old_version = data["framework_version"]
    if tuple(map(int, version.split("."))) < tuple(map(int, old_version.split("."))):
        raise UpdateError(f"Refusing to downgrade framework {old_version} to {version}")
    expected = {action.relative_path.as_posix(): action for action in actions}
    for name in expected:
        safe_relative(name)
    changes: list[FileChange] = []
    for name in sorted(set(old) | set(expected)):
        relative = safe_relative(name)
        check_parents(target, relative)
        path = target / relative
        action = expected.get(name)
        if name in old:
            original = regular_bytes(path)
            digest = hashlib.sha256(original).hexdigest()
            if digest != old[name]:
                raise UpdateError(f"Installed framework file was modified: {path}")
            if action is None:
                changes.append(FileChange(relative, "REMOVE", None, None, digest))
            elif original != action.content:
                changes.append(FileChange(relative, "UPDATE", action.content, action.mode, digest))
            else:
                changes.append(FileChange(relative, "UNCHANGED", None, None, digest))
        else:
            if path.exists() or path.is_symlink():
                raise UpdateError(f"New framework path already exists: {path}")
            assert action is not None
            changes.append(FileChange(relative, "CREATE", action.content, action.mode, None))
    needs_manifest = (old_version != version or
                      any(change.state != "UNCHANGED" for change in changes))
    manifest = (
        install.manifest_content(root or install.framework_root(), actions, version)
        if needs_manifest else None
    )
    return UpdatePlan(tuple(changes), old_manifest, manifest, old_version, version)


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".update-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def missing_directories(target: Path, changes: tuple[FileChange, ...]) -> list[Path]:
    missing: set[Path] = set()
    for change in changes:
        if change.state != "CREATE":
            continue
        parent = change.path.parent
        while parent != Path(".") and not (target / parent).exists():
            missing.add(parent)
            parent = parent.parent
    return sorted(missing, key=lambda path: (len(path.parts), path.as_posix()))


def apply_update(target: Path, plan: UpdatePlan) -> None:
    if plan.new_manifest is None:
        return
    journal_dir = target / JOURNAL
    journal_dir.mkdir(mode=0o700)
    entries = []
    directories = missing_directories(target, plan.changes)
    try:
        for index, change in enumerate(plan.changes):
            if change.state == "UNCHANGED":
                continue
            backup = None
            old_mode = None
            if change.old_digest is not None:
                path = target / change.path
                original = regular_bytes(path)
                if hashlib.sha256(original).hexdigest() != change.old_digest:
                    raise UpdateError(f"Installed framework file changed during update: {path}")
                backup = str(index)
                old_mode = stat.S_IMODE(path.stat().st_mode)
                atomic_write(journal_dir / backup, original, 0o600)
            entries.append({
                "path": change.path.as_posix(), "state": change.state,
                "backup": backup, "old_mode": old_mode,
                "old_digest": change.old_digest,
                "new_digest": hashlib.sha256(change.content).hexdigest() if change.content is not None else None,
            })
        if regular_bytes(target / install.MANIFEST_PATH) != plan.old_manifest:
            raise UpdateError("Framework manifest changed during update")
        atomic_write(journal_dir / "manifest", plan.old_manifest, 0o600)
        manifest_mode = stat.S_IMODE((target / install.MANIFEST_PATH).stat().st_mode)
        journal = {
            "files": entries,
            "directories": [path.as_posix() for path in directories],
            "manifest_mode": manifest_mode,
            "new_manifest_digest": hashlib.sha256(plan.new_manifest).hexdigest(),
        }
        atomic_write(journal_dir / "journal.json", json.dumps(journal).encode("utf-8"), 0o600)
    except BaseException:
        shutil.rmtree(journal_dir)
        raise
    try:
        for relative in directories:
            (target / relative).mkdir()
        for change in plan.changes:
            if change.state == "UNCHANGED":
                continue
            check_parents(target, change.path)
            path = target / change.path
            if change.state == "CREATE":
                if path.exists() or path.is_symlink():
                    raise UpdateError(f"New framework path appeared during update: {path}")
                assert change.content is not None and change.mode is not None
                atomic_write(path, change.content, change.mode)
            else:
                original = regular_bytes(path)
                if hashlib.sha256(original).hexdigest() != change.old_digest:
                    raise UpdateError(f"Installed framework file changed during update: {path}")
                if change.state == "REMOVE":
                    path.unlink()
                else:
                    assert change.content is not None and change.mode is not None
                    atomic_write(path, change.content, change.mode)
        for change in plan.changes:
            check_parents(target, change.path)
            path = target / change.path
            if change.state in {"CREATE", "UPDATE"}:
                assert change.content is not None
                if regular_bytes(path) != change.content:
                    raise UpdateError(f"Framework file changed during update: {path}")
            elif change.state == "UNCHANGED":
                if hashlib.sha256(regular_bytes(path)).hexdigest() != change.old_digest:
                    raise UpdateError(f"Installed framework file changed during update: {path}")
            elif change.state == "REMOVE" and (path.exists() or path.is_symlink()):
                raise UpdateError(f"Removed framework file reappeared during update: {path}")
        if regular_bytes(target / install.MANIFEST_PATH) != plan.old_manifest:
            raise UpdateError("Framework manifest changed during update")
        atomic_write(target / install.MANIFEST_PATH, plan.new_manifest, manifest_mode)
    except Exception:
        recover(target)
        raise
    shutil.rmtree(journal_dir)


def recover(target: Path) -> None:
    journal_dir = target / JOURNAL
    journal_path = journal_dir / "journal.json"
    if not journal_path.exists():
        shutil.rmtree(journal_dir)
        return
    journal = json.loads(regular_bytes(journal_path))
    if (not isinstance(journal, dict) or not isinstance(journal.get("files"), list)
            or not isinstance(journal.get("directories"), list)):
        raise UpdateError("Invalid update journal")
    def valid_digest(value: object) -> bool:
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    if (not valid_digest(journal.get("new_manifest_digest"))
            or type(journal.get("manifest_mode")) is not int
            or not 0 <= journal["manifest_mode"] <= 0o777):
        raise UpdateError("Invalid update journal manifest record")
    for entry in journal["files"]:
        if not isinstance(entry, dict) or entry.get("state") not in {"CREATE", "UPDATE", "REMOVE"}:
            raise UpdateError("Invalid update journal entry")
        if not isinstance(entry.get("path"), str):
            raise UpdateError("Invalid update journal path")
        safe_relative(entry["path"])
        if entry["state"] == "CREATE":
            if (entry.get("backup") is not None or entry.get("old_mode") is not None
                    or entry.get("old_digest") is not None or not valid_digest(entry.get("new_digest"))):
                raise UpdateError("Invalid update journal create record")
        else:
            if (not isinstance(entry.get("backup"), str) or not entry["backup"].isdigit()
                    or type(entry.get("old_mode")) is not int
                    or not 0 <= entry["old_mode"] <= 0o777
                    or not valid_digest(entry.get("old_digest"))):
                raise UpdateError("Invalid update journal backup")
            if entry["state"] == "UPDATE" and not valid_digest(entry.get("new_digest")):
                raise UpdateError("Invalid update journal update record")
            if entry["state"] == "REMOVE" and entry.get("new_digest") is not None:
                raise UpdateError("Invalid update journal removal record")
    for name in journal["directories"]:
        if (not isinstance(name, str) or not name or name.startswith("/") or "\\" in name
                or any(part in {"", ".", ".."} for part in name.split("/"))
                or not any(entry["state"] == "CREATE" and entry["path"].startswith(name + "/")
                           for entry in journal["files"])):
            raise UpdateError("Invalid update journal directory")
    manifest_path = target / install.MANIFEST_PATH
    old_manifest = regular_bytes(journal_dir / "manifest")
    current_manifest = regular_bytes(manifest_path)
    if (current_manifest != old_manifest and
            hashlib.sha256(current_manifest).hexdigest() != journal["new_manifest_digest"]):
        raise UpdateError("Framework manifest changed since interrupted update")
    for entry in reversed(journal["files"]):
        relative = safe_relative(entry["path"])
        check_parents(target, relative)
        path = target / relative
        if entry["state"] == "CREATE":
            if path.exists() or path.is_symlink():
                if hashlib.sha256(regular_bytes(path)).hexdigest() != entry["new_digest"]:
                    raise UpdateError(f"Created framework file changed since interruption: {path}")
                path.unlink()
        else:
            if path.exists() or path.is_symlink():
                digest = hashlib.sha256(regular_bytes(path)).hexdigest()
                if digest not in {entry["old_digest"], entry["new_digest"]}:
                    raise UpdateError(f"Framework file changed since interruption: {path}")
            original = regular_bytes(journal_dir / entry["backup"])
            atomic_write(path, original, entry["old_mode"])
    atomic_write(manifest_path, old_manifest, journal["manifest_mode"])
    for name in reversed(journal["directories"]):
        directory = target / Path(name)
        if directory.exists():
            directory.rmdir()
    shutil.rmtree(journal_dir)


def update(target: Path, *, apply: bool = False, root: Path | None = None) -> int:
    if target.is_symlink() or not target.is_dir():
        raise UpdateError(f"Target must be a regular directory: {target}")
    if (target / ".ai-dev-framework-migration").exists():
        raise UpdateError("An interrupted workspace migration must be recovered first")
    journal = target / JOURNAL
    if journal.is_symlink():
        raise UpdateError(f"Update journal is a symlink: {journal}")
    if journal.exists():
        if not apply:
            raise UpdateError(f"Interrupted update found; run with --apply to recover: {journal}")
        recover(target)
        print("Recovered an interrupted update; checking the workspace again.")
    require_current_layout(target)
    root = root or install.framework_root()
    actions = install.build_actions(root)
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    plan = plan_update(target, actions, version, root)
    if plan.new_manifest is None:
        print("Workspace is already up to date.")
        return 0
    for change in plan.changes:
        if change.state != "UNCHANGED":
            print(f"{change.state} {change.path.as_posix()}")
    print(f"UPDATE {install.MANIFEST_PATH.as_posix()} ({plan.old_version} -> {plan.new_version})")
    if not apply:
        print("Preview complete; use --apply to update.")
        return 0
    apply_update(target, plan)
    print(f"Updated AI Dev Framework to {version} in {target}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Apply the previewed update")
    args = parser.parse_args(argv)
    target = Path(os.path.abspath(args.target.expanduser()))
    try:
        return update(target, apply=args.apply)
    except (UpdateError, install.SourceValidationError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Update stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
