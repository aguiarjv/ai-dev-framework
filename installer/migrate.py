#!/usr/bin/env python3
"""Upgrade an installed workspace and rename managed-project metadata folders."""

from __future__ import annotations

import argparse
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
import update as framework_update


FOLDERS = ("docs", "plans", "scripts", "reviews", "reports")
JOURNAL = ".ai-dev-framework-migration"
OLD_PATH = re.compile(r"(?<![\w-])(?:docs|plans|scripts|reviews|reports)/")
OLD_LITERAL = re.compile(r"['\"](?:docs|plans|scripts|reviews|reports)['\"]")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".toml", ".yaml", ".yml", ".txt"}
OLD_APPROVAL_RULE = (
    "- An approved plan authorizes only its recorded task-to-plan integrations. Do\n"
    "  not deliver the plan branch, otherwise merge or rebase, push, remove a\n"
)
NEW_IMPLEMENTATION_RULE = (
    "- A later explicit request to implement the created plan authorizes task work,\n"
    "  recorded worktrees, and task-to-plan integrations. Do not deliver the plan\n"
    "  branch, otherwise merge or rebase, push, remove a\n"
)


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
        return text.replace(OLD_APPROVAL_RULE, NEW_IMPLEMENTATION_RULE)
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
    result = before + marker + revised + (separator + after if separator else "")
    return result.replace(OLD_APPROVAL_RULE, NEW_IMPLEMENTATION_RULE)


def plan_artifact(text: str, plan_id: str, *, archived: bool = False) -> str:
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
        elif re.search(r"\|\s*`?project-docs`?\s*\|", line) or (
            section == "Architecture Decisions" and line.startswith("|")
            and re.search(r"(?<![\w-])docs/adrs/[^\s|`]+", line)
        ):
            line = re.sub(r"(?<![\w-])docs/", "workspace-docs/", line)
        for folder in ("plans", "reviews"):
            destination = (
                f"workspace-plans/done/{plan_id}/"
                if folder == "plans" and archived
                else f"workspace-{folder}/{plan_id}/"
            )
            line = re.sub(
                rf"(?<![\w-]){folder}/{re.escape(plan_id)}/",
                destination, line,
            )
        if archived and not (
            re.search(r"\bold\b", line, re.IGNORECASE)
            and re.search(r"\babsent\b", line, re.IGNORECASE)
        ):
            line = re.sub(
                rf"(?<![\w-])workspace-plans/{re.escape(plan_id)}/",
                f"workspace-plans/done/{plan_id}/", line,
            )
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
                revised = plan_artifact(
                    original.decode("utf-8"), plan_id,
                    archived=relative.parts[0] == "done",
                ).encode("utf-8")
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
                    text = plan_artifact(
                        text, plan_id, archived=relative.parts[0] == "done",
                    )
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
                    if name == "AGENTS.md" and "approved plan authorizes" in line.lower():
                        warnings.append(f"REVIEW {path}:{number}: old implementation authorization rule")
    return moves, changes, warnings


def backup_and_apply(target: Path, moves: list[tuple[Path, Path]], changes: list[FileChange], manifest: bytes | None) -> None:
    journal_dir = target / JOURNAL
    journal_dir.mkdir(mode=0o700)
    manifest_path = target / install.MANIFEST_PATH
    all_changes = [*changes]
    if manifest is not None:
        all_changes.append(FileChange(manifest_path, manifest_path, manifest))
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
    update_journal = target / framework_update.JOURNAL
    if update_journal.exists() or update_journal.is_symlink():
        raise MigrationError("An interrupted framework update must be recovered first")
    if (target / JOURNAL).exists():
        if not apply:
            raise MigrationError(f"Interrupted migration found; run with --apply to recover: {target / JOURNAL}")
        recover(target)
        print("Recovered an interrupted migration; checking the workspace again.")
    actions = install.build_actions()
    version = (install.framework_root() / "VERSION").read_text(encoding="utf-8").strip()
    try:
        update_plan = framework_update.plan_update(target, actions, version)
        _, old_inventory, old_manifest = framework_update.load_manifest(target)
    except framework_update.UpdateError as error:
        raise MigrationError(str(error)) from error
    same_inventory = set(old_inventory) == {action.relative_path.as_posix() for action in actions}
    installed: list[FileChange] = []
    if same_inventory:
        for change in update_plan.changes:
            if change.state == "UPDATE":
                assert change.content is not None
                installed.append(FileChange(target / change.path, target / change.path, change.content))
    moves, project_files, warnings = project_changes(target)
    manifest = update_plan.new_manifest if same_inventory else None
    if not moves and not installed and not project_files and update_plan.new_manifest is None:
        for warning in warnings:
            print(warning)
        print("Workspace is already migrated.")
        return 0
    if not same_inventory and not moves and not project_files:
        for warning in warnings:
            print(warning)
        print("Workspace layout is already migrated; run installer/update.py next.")
        return 0
    for old, new in moves:
        print(f"MOVE {old.relative_to(target)} -> {new.relative_to(target)}")
    for change in [*installed, *project_files]:
        print(f"UPDATE {change.destination.relative_to(target)}")
    if manifest is not None and old_manifest != manifest:
        print(f"UPDATE {install.MANIFEST_PATH}")
    if not same_inventory:
        print("Framework files will remain at their installed version; run installer/update.py after migration.")
    for warning in warnings:
        print(warning)
    if not apply:
        print("Preview complete; use --apply to migrate.")
        return 0
    backup_and_apply(target, moves, [*installed, *project_files], manifest)
    print("Migration complete." if same_inventory else "Migration complete; run installer/update.py next.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Apply the previewed migration")
    args = parser.parse_args()
    try:
        return migrate(args.target, args.apply)
    except (MigrationError, framework_update.UpdateError, OSError, UnicodeError, json.JSONDecodeError, install.InstallError) as error:
        print(f"Migration stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
