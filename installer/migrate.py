#!/usr/bin/env python3
"""Upgrade an installed workspace and rename managed-project metadata folders."""

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
from pathlib import Path

import install


FOLDERS = ("docs", "plans", "scripts", "reviews", "reports")
JOURNAL = ".ai-dev-framework-migration"
OLD_PATH = re.compile(r"(?<![\w-])(?:docs|plans|scripts|reviews|reports)/")
OLD_LITERAL = re.compile(r"['\"](?:docs|plans|scripts|reviews|reports)['\"]")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".toml", ".yaml", ".yml", ".txt"}


class MigrationError(ValueError):
    pass


@dataclass(frozen=True)
class FileChange:
    source: Path
    destination: Path
    content: bytes


def safe_relative(value: str) -> Path:
    path = Path(value)
    if (not value or path.is_absolute() or "\\" in value or
            any(part in {"", ".", ".."} for part in value.split("/"))):
        raise MigrationError(f"Unsafe manifest path: {value!r}")
    return path


def regular_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise MigrationError(f"Expected a regular file: {path}")
    return path.read_bytes()


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".migration-", dir=path.parent)
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


def rename_paths(text: str) -> str:
    return OLD_PATH.sub(lambda match: "workspace-" + match.group(), text)


def project_instructions(text: str) -> str:
    marker = "## Project Paths\n"
    if marker not in text:
        return text
    before, section = text.split(marker, 1)
    body, separator, after = section.partition("\n## ")
    labels = (
        "- Project documentation:", "- Architecture decisions:",
        "- Active and completed plans:", "- Project workspace scripts:",
        "- Review artifacts:", "- Optional reports:",
    )
    revised = "".join(
        rename_paths(line) if line.startswith(labels) else line
        for line in body.splitlines(keepends=True)
    )
    return before + marker + revised + (separator + after if separator else "")


def plan_artifact(text: str, plan_id: str) -> str:
    lines = []
    section = ""
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            section = line[3:].strip()
        if "| `repo-file` |" in line:
            lines.append(line)
            continue
        if re.match(r"^(latest_handoff|latest_review):\s", line):
            line = re.sub(r'(?<=")(?:(?:plans)|(?:reviews))/',
                          lambda match: "workspace-" + match.group(), line, count=1)
        elif "| `project-docs` |" in line or (
            section == "Architecture Decisions" and line.startswith("|")
            and re.search(r"`docs/adrs/[^`]+`", line)
        ):
            line = re.sub(r"(?<![\w-])docs/", "workspace-docs/", line)
        for folder in ("plans", "reviews"):
            line = re.sub(rf"(?<![\w-]){folder}/{re.escape(plan_id)}/",
                          f"workspace-{folder}/{plan_id}/", line)
        lines.append(line)
    return "".join(lines)


def inspect_tree(root: Path) -> None:
    for current, directories, filenames in os.walk(root, followlinks=False):
        for name in directories + filenames:
            path = Path(current) / name
            if path.is_symlink():
                raise MigrationError(f"Metadata contains a symlink: {path}")


def project_changes(target: Path) -> tuple[list[tuple[Path, Path]], list[FileChange], list[str]]:
    projects = target / "projects"
    if projects.is_symlink() or not projects.is_dir():
        raise MigrationError(f"Expected a regular projects directory: {projects}")
    moves: list[tuple[Path, Path]] = []
    changes: list[FileChange] = []
    warnings: list[str] = []
    for project in sorted(projects.iterdir()):
        if project.name == "README.md":
            continue
        if project.is_symlink():
            raise MigrationError(f"Unexpected projects entry: {project}")
        if not project.is_dir():
            continue
        for folder in FOLDERS:
            old = project / folder
            new = project / f"workspace-{folder}"
            if old.is_symlink() or new.is_symlink():
                raise MigrationError(f"Metadata folder is a symlink: {old if old.is_symlink() else new}")
            if old.exists():
                if not old.is_dir() or new.exists():
                    raise MigrationError(f"Folder collision or invalid folder: {old} -> {new}")
                inspect_tree(old)
                moves.append((old, new))
            elif new.exists():
                if not new.is_dir():
                    raise MigrationError(f"Metadata path is not a directory: {new}")
                inspect_tree(new)
        instructions = project / "AGENTS.md"
        if instructions.exists():
            original = regular_bytes(instructions)
            revised = project_instructions(original.decode("utf-8")).encode("utf-8")
            if revised != original:
                changes.append(FileChange(instructions, instructions, revised))
        for folder in ("plans", "workspace-plans"):
            plan_root = project / folder
            if not plan_root.is_dir():
                continue
            for source in sorted(plan_root.rglob("*.md")):
                original = regular_bytes(source)
                relative = source.relative_to(plan_root)
                plan_id = relative.parts[1] if relative.parts[0] == "done" and len(relative.parts) > 1 else relative.parts[0]
                revised = plan_artifact(original.decode("utf-8"), plan_id).encode("utf-8")
                destination = project / "workspace-plans" / relative
                if revised != original:
                    changes.append(FileChange(source, destination, revised))
        for folder in (*FOLDERS, *(f"workspace-{name}" for name in FOLDERS)):
            metadata = project / folder
            if not metadata.is_dir():
                continue
            for source in sorted(
                path for path in metadata.rglob("*")
                if path.is_file() and path.suffix in TEXT_SUFFIXES
            ):
                if source.is_symlink():
                    raise MigrationError(f"Metadata contains a symlink: {source}")
                text = source.read_text(encoding="utf-8", errors="replace")
                if folder in ("plans", "workspace-plans") and source.suffix == ".md":
                    relative = source.relative_to(metadata)
                    plan_id = relative.parts[1] if relative.parts[0] == "done" and len(relative.parts) > 1 else relative.parts[0]
                    text = plan_artifact(text, plan_id)
                display = project / f"workspace-{folder}" / source.relative_to(metadata) if folder in FOLDERS else source
                for number, line in enumerate(text.splitlines(), 1):
                    if OLD_PATH.search(line) or (
                        folder in ("scripts", "workspace-scripts") and OLD_LITERAL.search(line)
                    ):
                        warnings.append(f"REVIEW {display}:{number}: possible old path")
        for name in ("AGENTS.md", "README.md"):
            path = project / name
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if name == "AGENTS.md":
                    text = project_instructions(text)
                for number, line in enumerate(text.splitlines(), 1):
                    if OLD_PATH.search(line):
                        warnings.append(f"REVIEW {path}:{number}: possible old path")
    return moves, changes, warnings


def installed_changes(target: Path, actions: list[install.InstallAction]) -> list[FileChange]:
    manifest_path = target / install.MANIFEST_PATH
    data = json.loads(regular_bytes(manifest_path))
    if (not isinstance(data, dict) or data.get("framework") != install.FRAMEWORK_NAME or
            data.get("schema_version") != install.MANIFEST_SCHEMA_VERSION or
            not isinstance(data.get("files"), list)):
        raise MigrationError("Unsupported installed framework manifest")
    expected = {action.relative_path.as_posix(): action for action in actions}
    old: dict[str, str] = {}
    for item in data["files"]:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise MigrationError("Invalid installed file inventory")
        name, digest = item["path"], item["sha256"]
        if not isinstance(name, str) or not isinstance(digest, str):
            raise MigrationError("Invalid installed file inventory")
        safe_relative(name)
        if name in old or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise MigrationError("Duplicate path or invalid checksum in manifest")
        old[name] = digest
    if set(old) != set(expected):
        raise MigrationError("Installed file inventory differs from this migration's supported layout")
    changes = []
    for name, action in expected.items():
        relative = safe_relative(name)
        parent = target
        for part in relative.parts[:-1]:
            parent = parent / part
            if parent.is_symlink():
                raise MigrationError(f"Installed framework parent is a symlink: {parent}")
        path = target / relative
        original = regular_bytes(path)
        if hashlib.sha256(original).hexdigest() != old[name]:
            raise MigrationError(f"Installed framework file was modified: {path}")
        if original != action.content:
            changes.append(FileChange(path, path, action.content))
    return changes


def backup_and_apply(target: Path, moves: list[tuple[Path, Path]], changes: list[FileChange], manifest: bytes) -> None:
    journal_dir = target / JOURNAL
    journal_dir.mkdir(mode=0o700)
    manifest_path = target / install.MANIFEST_PATH
    all_changes = [*changes, FileChange(manifest_path, manifest_path, manifest)]
    records = []
    try:
        for index, change in enumerate(all_changes):
            original = regular_bytes(change.source)
            backup = journal_dir / str(index)
            atomic_write(backup, original, 0o600)
            records.append({
                "source": str(change.source.relative_to(target)),
                "destination": str(change.destination.relative_to(target)),
                "backup": str(index),
                "mode": stat.S_IMODE(change.source.stat().st_mode),
            })
        journal = {"moves": [[str(a.relative_to(target)), str(b.relative_to(target))] for a, b in moves],
                   "files": records}
        atomic_write(journal_dir / "journal.json", json.dumps(journal, indent=2).encode("utf-8"), 0o600)
    except BaseException:
        shutil.rmtree(journal_dir)
        raise
    try:
        for old, new in moves:
            old.rename(new)
        for change, record in zip(all_changes, records):
            atomic_write(change.destination, change.content, record["mode"])
    except Exception:
        recover(target)
        raise
    shutil.rmtree(journal_dir)


def recover(target: Path) -> None:
    journal_dir = target / JOURNAL
    if not (journal_dir / "journal.json").exists():
        shutil.rmtree(journal_dir)
        return
    journal = json.loads(regular_bytes(journal_dir / "journal.json"))
    moves = [(target / safe_relative(a), target / safe_relative(b)) for a, b in journal["moves"]]
    for record in journal["files"]:
        source = target / safe_relative(record["source"])
        destination = target / safe_relative(record["destination"])
        path = destination if destination.exists() else source
        if path.exists():
            atomic_write(path, regular_bytes(journal_dir / safe_relative(record["backup"])), record["mode"])
    for old, new in reversed(moves):
        if new.exists() and not old.exists():
            new.rename(old)
    shutil.rmtree(journal_dir)


def migrate(target: Path, apply: bool) -> int:
    if target.is_symlink() or not target.is_dir():
        raise MigrationError(f"Target must be a regular directory: {target}")
    if (target / JOURNAL).is_symlink():
        raise MigrationError(f"Migration journal is a symlink: {target / JOURNAL}")
    if (target / JOURNAL).exists():
        if not apply:
            raise MigrationError(f"Interrupted migration found; run with --apply to recover: {target / JOURNAL}")
        recover(target)
        print("Recovered an interrupted migration; checking the workspace again.")
    actions = install.build_actions()
    installed = installed_changes(target, actions)
    moves, project_files, warnings = project_changes(target)
    version = (install.framework_root() / "VERSION").read_text(encoding="utf-8").strip()
    manifest = install.manifest_content(install.framework_root(), actions, version)
    old_manifest = regular_bytes(target / install.MANIFEST_PATH)
    manifest_current = (
        install.validate_existing_manifest(target / install.MANIFEST_PATH, actions, version)
        == "valid"
    )
    if not moves and not installed and not project_files and manifest_current:
        for warning in warnings:
            print(warning)
        print("Workspace is already migrated.")
        return 0
    for old, new in moves:
        print(f"MOVE {old.relative_to(target)} -> {new.relative_to(target)}")
    for change in [*installed, *project_files]:
        print(f"UPDATE {change.destination.relative_to(target)}")
    if old_manifest != manifest:
        print(f"UPDATE {install.MANIFEST_PATH}")
    for warning in warnings:
        print(warning)
    if not apply:
        print("Preview complete; use --apply to migrate.")
        return 0
    backup_and_apply(target, moves, [*installed, *project_files], manifest)
    print("Migration complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Apply the previewed migration")
    args = parser.parse_args()
    try:
        return migrate(args.target, args.apply)
    except (MigrationError, OSError, UnicodeError, json.JSONDecodeError, install.InstallError) as error:
        print(f"Migration stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
