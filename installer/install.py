#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_NAME = "ai-dev-framework"
MANIFEST_SCHEMA_VERSION = 1
MANIFEST_PATH = Path(".ai-dev-framework.json")
SKILL_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
READ_ONLY_ROLES = {"database-explorer", "explorer", "reviewer"}
ROLE_MARKERS = {
    "database-explorer": (
        "read-only connection or tool",
        "structured handoff payload",
        "never reveal credentials",
    ),
    "explorer": (
        "read-only exploration mode",
        "relevant documentation and guides",
        "structured handoff payload",
    ),
    "implementer": (
        "assigned task or correction pass",
        "ready-for-review",
        "handoff",
    ),
    "orchestrator": (
        "user communication",
        "plan-management skill",
        "plan-level",
    ),
    "reviewer": (
        "actionable finding",
        "acceptance-criteria coverage",
        "two complete payloads",
    ),
}
CLAUDE_DENIED_WRITE_TOOLS = {"Agent", "Edit", "Write", "NotebookEdit"}


class SourceValidationError(Exception):
    """Raised when framework source files cannot produce a valid installation."""


class InstallError(Exception):
    """Raised when a target cannot be installed safely."""


@dataclass(frozen=True)
class InstallAction:
    relative_path: Path
    content: bytes
    mode: int = 0o644

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass(frozen=True)
class PlannedAction:
    action: InstallAction
    state: str
    reason: str | None = None


def framework_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for path in directory.rglob("*"):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise SourceValidationError(f"Source symlinks are not installable: {path}")
        if path.is_file():
            files.append(path)
    return sorted(files)


def split_frontmatter(text: str, path: Path) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SourceValidationError(f"{path}: missing YAML frontmatter")

    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise SourceValidationError(f"{path}: unterminated YAML frontmatter") from error

    return lines[1:closing_index], "\n".join(lines[closing_index + 1 :]).strip()


def parse_frontmatter(text: str, path: Path) -> tuple[dict[str, Any], str]:
    frontmatter_lines, body = split_frontmatter(text, path)
    values: dict[str, Any] = {}
    list_key: str | None = None

    for raw_line in frontmatter_lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line[:1].isspace():
            if stripped.startswith("- ") and list_key is not None:
                list_value = values.setdefault(list_key, [])
                if not isinstance(list_value, list):
                    raise SourceValidationError(f"{path}: invalid list for {list_key}")
                list_value.append(unquote(stripped[2:].strip()))
            continue
        if ":" not in raw_line:
            raise SourceValidationError(f"{path}: invalid frontmatter line: {raw_line}")
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        list_key = key if not raw_value else None
        values[key] = unquote(raw_value) if raw_value else []

    return values, body


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_codex_agents(root: Path) -> dict[str, tuple[dict[str, Any], str, Path]]:
    directory = root / "agents" / "codex"
    if not directory.is_dir():
        raise SourceValidationError(f"Missing Codex agent directory: {directory}")

    agents: dict[str, tuple[dict[str, Any], str, Path]] = {}
    for path in sorted(directory.glob("*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise SourceValidationError(f"{path}: invalid TOML: {error}") from error
        for field in ("name", "description", "developer_instructions"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise SourceValidationError(f"{path}: missing required field {field}")
        name = data["name"]
        if path.stem != name:
            raise SourceValidationError(f"{path}: filename must match agent name {name}")
        if name in agents:
            raise SourceValidationError(f"Duplicate Codex agent name: {name}")
        agents[name] = (data, data["developer_instructions"].strip(), path)
    return agents


def load_claude_agents(root: Path) -> dict[str, tuple[dict[str, Any], str, Path]]:
    directory = root / "agents" / "claude"
    if not directory.is_dir():
        raise SourceValidationError(f"Missing Claude agent directory: {directory}")

    agents: dict[str, tuple[dict[str, Any], str, Path]] = {}
    for path in sorted(directory.glob("*.md")):
        try:
            metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
        except OSError as error:
            raise SourceValidationError(f"{path}: cannot read agent: {error}") from error
        for field in ("name", "description"):
            if not isinstance(metadata.get(field), str) or not metadata[field].strip():
                raise SourceValidationError(f"{path}: missing required field {field}")
        if not body:
            raise SourceValidationError(f"{path}: agent prompt is empty")
        name = metadata["name"]
        if path.stem != name:
            raise SourceValidationError(f"{path}: filename must match agent name {name}")
        if name in agents:
            raise SourceValidationError(f"Duplicate Claude agent name: {name}")
        agents[name] = (metadata, body, path)
    return agents


def validate_agents(root: Path) -> None:
    codex_agents = load_codex_agents(root)
    claude_agents = load_claude_agents(root)
    if set(codex_agents) != set(claude_agents):
        raise SourceValidationError(
            "Codex and Claude agent sets differ: "
            f"Codex={sorted(codex_agents)}, Claude={sorted(claude_agents)}"
        )
    if set(codex_agents) != set(ROLE_MARKERS):
        raise SourceValidationError(
            f"Agent set does not match the framework contract: {sorted(codex_agents)}"
        )

    for name in sorted(codex_agents):
        codex_metadata, codex_body, codex_path = codex_agents[name]
        claude_metadata, claude_body, claude_path = claude_agents[name]

        if codex_metadata["description"] != claude_metadata["description"]:
            raise SourceValidationError(
                f"{name}: Codex and Claude descriptions must match exactly"
            )

        expected_codex_mode = (
            "read-only"
            if name in READ_ONLY_ROLES
            else "workspace-write" if name == "implementer" else None
        )
        if codex_metadata.get("sandbox_mode") != expected_codex_mode:
            raise SourceValidationError(
                f"{codex_path}: sandbox_mode must be {expected_codex_mode!r}"
            )

        expected_claude_mode = (
            "plan"
            if name in READ_ONLY_ROLES
            else "acceptEdits" if name == "implementer" else None
        )
        if claude_metadata.get("permissionMode") != expected_claude_mode:
            raise SourceValidationError(
                f"{claude_path}: permissionMode must be {expected_claude_mode!r}"
            )

        denied_tools = set(claude_metadata.get("disallowedTools", []))
        expected_denied = (
            CLAUDE_DENIED_WRITE_TOOLS
            if name in READ_ONLY_ROLES
            else {"Agent"} if name == "implementer" else set()
        )
        if denied_tools != expected_denied:
            raise SourceValidationError(
                f"{claude_path}: disallowedTools must be {sorted(expected_denied)}"
            )

        for marker in ROLE_MARKERS[name]:
            if marker not in codex_body.lower():
                raise SourceValidationError(
                    f"{codex_path}: missing behavioral contract marker {marker!r}"
                )
            if marker not in claude_body.lower():
                raise SourceValidationError(
                    f"{claude_path}: missing behavioral contract marker {marker!r}"
                )


def validate_skills(root: Path) -> None:
    skills_directory = root / "skills"
    if not skills_directory.is_dir():
        raise SourceValidationError(f"Missing skills directory: {skills_directory}")

    skill_directories = sorted(
        path for path in skills_directory.iterdir() if path.is_dir()
    )
    if not skill_directories:
        raise SourceValidationError("No skills found")

    guide_root = (root / "guides").resolve()
    for directory in skill_directories:
        skill_path = directory / "SKILL.md"
        if not skill_path.is_file():
            raise SourceValidationError(f"{directory}: missing SKILL.md")
        metadata, _ = parse_frontmatter(skill_path.read_text(encoding="utf-8"), skill_path)
        unknown_fields = set(metadata) - SKILL_FRONTMATTER_FIELDS
        if unknown_fields:
            raise SourceValidationError(
                f"{skill_path}: non-portable frontmatter fields: {sorted(unknown_fields)}"
            )
        for field in ("name", "description"):
            if not isinstance(metadata.get(field), str) or not metadata[field].strip():
                raise SourceValidationError(f"{skill_path}: missing required field {field}")
        if metadata["name"] != directory.name:
            raise SourceValidationError(
                f"{skill_path}: skill name must match directory {directory.name}"
            )

        text = skill_path.read_text(encoding="utf-8")
        for match in re.finditer(r"\]\((\.\./\.\./guides/[^)#]+)", text):
            linked_path = (skill_path.parent / match.group(1)).resolve()
            try:
                linked_path.relative_to(guide_root)
            except ValueError as error:
                raise SourceValidationError(
                    f"{skill_path}: linked guide escapes the guides directory: {match.group(1)}"
                ) from error
            if not linked_path.is_file():
                raise SourceValidationError(
                    f"{skill_path}: linked guide does not exist: {match.group(1)}"
                )


def validate_sources(root: Path) -> None:
    version_path = root / "VERSION"
    if not version_path.is_file() or not version_path.read_text(encoding="utf-8").strip():
        raise SourceValidationError(f"Missing framework version: {version_path}")
    version = version_path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SourceValidationError(f"{version_path}: version must use MAJOR.MINOR.PATCH")
    validate_agents(root)
    validate_skills(root)
    for template_name in ("AGENTS.md", "CLAUDE.md", "projects-README.md"):
        template_path = root / "installer" / "templates" / template_name
        if not template_path.is_file():
            raise SourceValidationError(f"Missing installer template: {template_path}")


def file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def render_skill(text: str, source_path: str, *, for_claude: bool) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise SourceValidationError(f"{source_path}: missing YAML frontmatter")
    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise SourceValidationError(f"{source_path}: unterminated YAML frontmatter") from error

    prefix = "".join(lines[: closing_index + 1]).rstrip("\r\n") + "\n"
    body = "".join(lines[closing_index + 1 :]).lstrip("\r\n")
    if for_claude:
        body = body.replace("../../guides/", "../../../.agents/guides/")
    marker = f"<!-- Generated from {source_path}. Edit the framework source and reinstall. -->"
    return f"{prefix}\n{marker}\n\n{body}"


def build_actions(root: Path | None = None) -> list[InstallAction]:
    root = root or framework_root()
    validate_sources(root)
    actions: dict[Path, InstallAction] = {}

    def add(relative_path: Path, content: bytes, mode: int = 0o644) -> None:
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise SourceValidationError(f"Unsafe target path: {relative_path}")
        if relative_path in actions:
            raise SourceValidationError(f"Duplicate target path: {relative_path}")
        actions[relative_path] = InstallAction(relative_path, content, mode)

    template_directory = root / "installer" / "templates"
    add(Path("AGENTS.md"), (template_directory / "AGENTS.md").read_bytes())
    add(Path("CLAUDE.md"), (template_directory / "CLAUDE.md").read_bytes())
    add(
        Path("projects") / "README.md",
        (template_directory / "projects-README.md").read_bytes(),
    )

    for source in source_files(root / "agents" / "codex"):
        relative = source.relative_to(root / "agents" / "codex")
        add(Path(".codex") / "agents" / relative, source.read_bytes(), file_mode(source))
    for source in source_files(root / "agents" / "claude"):
        relative = source.relative_to(root / "agents" / "claude")
        add(Path(".claude") / "agents" / relative, source.read_bytes(), file_mode(source))
    for source in source_files(root / "guides"):
        relative = source.relative_to(root / "guides")
        add(Path(".agents") / "guides" / relative, source.read_bytes(), file_mode(source))

    skill_root = root / "skills"
    for skill_directory in sorted(path for path in skill_root.iterdir() if path.is_dir()):
        for source in source_files(skill_directory):
            skill_relative = source.relative_to(skill_directory)
            content = source.read_bytes()
            if skill_relative == Path("SKILL.md"):
                source_name = source.relative_to(root).as_posix()
                text = content.decode("utf-8")
                codex_content = render_skill(text, source_name, for_claude=False).encode("utf-8")
                claude_content = render_skill(text, source_name, for_claude=True).encode("utf-8")
            else:
                codex_content = content
                claude_content = content
            add(
                Path(".agents") / "skills" / skill_directory.name / skill_relative,
                codex_content,
                file_mode(source),
            )
            add(
                Path(".claude") / "skills" / skill_directory.name / skill_relative,
                claude_content,
                file_mode(source),
            )

    return [actions[path] for path in sorted(actions, key=lambda item: item.as_posix())]


def expected_manifest_files(actions: list[InstallAction]) -> list[dict[str, str]]:
    return [
        {"path": action.relative_path.as_posix(), "sha256": action.digest}
        for action in actions
    ]


def inspect_destination(target: Path, action: InstallAction) -> PlannedAction:
    cursor = target
    for part in action.relative_path.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            return PlannedAction(action, "conflict", f"parent is a symlink: {cursor}")
        if cursor.exists() and not cursor.is_dir():
            return PlannedAction(action, "conflict", f"parent is not a directory: {cursor}")

    destination = target / action.relative_path
    if destination.is_symlink():
        return PlannedAction(action, "conflict", "destination is a symlink")
    if not destination.exists():
        return PlannedAction(action, "create")
    if not destination.is_file():
        return PlannedAction(action, "conflict", "destination is not a regular file")
    try:
        existing_content = destination.read_bytes()
    except OSError as error:
        return PlannedAction(action, "conflict", f"cannot read destination: {error}")
    if existing_content == action.content:
        return PlannedAction(action, "same")
    return PlannedAction(action, "conflict", "destination content differs")


def validate_existing_manifest(
    path: Path,
    actions: list[InstallAction],
    version: str,
) -> str | None:
    if path.is_symlink():
        return "manifest is a symlink"
    if not path.exists():
        return None
    if not path.is_file():
        return "manifest is not a regular file"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return f"manifest is invalid: {error}"
    if not isinstance(data, dict):
        return "manifest must be a JSON object"
    expected_keys = {
        "framework",
        "schema_version",
        "framework_version",
        "installed_at",
        "source_revision",
        "source_dirty",
        "files",
    }
    if set(data) != expected_keys:
        return "manifest fields differ"
    if data.get("framework") != FRAMEWORK_NAME:
        return "manifest belongs to a different framework"
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        return "manifest schema version differs"
    if data.get("framework_version") != version:
        return "manifest framework version differs"
    if not isinstance(data.get("installed_at"), str) or not data["installed_at"]:
        return "manifest installation time is missing"
    try:
        installed_at = datetime.fromisoformat(data["installed_at"])
    except ValueError:
        return "manifest installation time is invalid"
    if installed_at.tzinfo is None:
        return "manifest installation time must include a timezone"
    revision = data.get("source_revision")
    if revision is not None and (
        not isinstance(revision, str) or re.fullmatch(r"[0-9a-fA-F]{40,64}", revision) is None
    ):
        return "manifest source revision is invalid"
    if data.get("source_dirty") is not None and not isinstance(data["source_dirty"], bool):
        return "manifest source dirty state is invalid"
    if data.get("files") != expected_manifest_files(actions):
        return "manifest file inventory differs"
    return "valid"


def plan_install(
    target: Path,
    actions: list[InstallAction],
    version: str,
) -> tuple[list[PlannedAction], str]:
    if target.is_symlink():
        raise InstallError(f"Target is a symlink: {target}")
    if target.exists() and not target.is_dir():
        raise InstallError(f"Target is not a directory: {target}")

    planned = [inspect_destination(target, action) for action in actions]
    manifest_path = target / MANIFEST_PATH
    manifest_state = validate_existing_manifest(manifest_path, actions, version)
    if manifest_state == "valid" and any(item.state != "same" for item in planned):
        manifest_state = "manifest inventory exists but installed files are missing or changed"
    return planned, manifest_state or "create"


def git_metadata(root: Path) -> tuple[str | None, bool | None]:
    try:
        revision = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status_output = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None, None
    return revision or None, bool(status_output.strip())


def manifest_content(root: Path, actions: list[InstallAction], version: str) -> bytes:
    revision, dirty = git_metadata(root)
    data = {
        "framework": FRAMEWORK_NAME,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "framework_version": version,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "source_revision": revision,
        "source_dirty": dirty,
        "files": expected_manifest_files(actions),
    }
    return (json.dumps(data, indent=2) + "\n").encode("utf-8")


def write_exclusive(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor: int | None = None
    created = False
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        created = True
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(path, mode)
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        raise


def install(target: Path, *, dry_run: bool = False, root: Path | None = None) -> int:
    root = root or framework_root()
    actions = build_actions(root)
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    planned, manifest_state = plan_install(target, actions, version)

    conflicts = [item for item in planned if item.state == "conflict"]
    if manifest_state not in {"create", "valid"}:
        conflicts.append(
            PlannedAction(
                InstallAction(MANIFEST_PATH, b""),
                "conflict",
                manifest_state,
            )
        )

    for item in planned:
        label = {
            "create": "CREATE",
            "same": "UNCHANGED",
            "conflict": "CONFLICT",
        }[item.state]
        suffix = f": {item.reason}" if item.reason else ""
        print(f"{label} {item.action.relative_path.as_posix()}{suffix}")
    if manifest_state == "create":
        print(f"CREATE {MANIFEST_PATH.as_posix()}")
    elif manifest_state == "valid":
        print(f"UNCHANGED {MANIFEST_PATH.as_posix()}")
    else:
        print(f"CONFLICT {MANIFEST_PATH.as_posix()}: {manifest_state}")

    if conflicts:
        print("Installation aborted; no files were written.", file=sys.stderr)
        return 2
    if dry_run:
        print("Dry run complete; no files were written.")
        return 0

    target.mkdir(parents=True, exist_ok=True)
    for item in planned:
        if item.state == "create":
            try:
                write_exclusive(
                    target / item.action.relative_path,
                    item.action.content,
                    item.action.mode,
                )
            except OSError as error:
                raise InstallError(
                    f"Could not write {item.action.relative_path}: {error}"
                ) from error

    if manifest_state == "create":
        try:
            write_exclusive(
                target / MANIFEST_PATH,
                manifest_content(root, actions, version),
                0o644,
            )
        except OSError as error:
            raise InstallError(f"Could not write {MANIFEST_PATH}: {error}") from error

    if all(item.state == "same" for item in planned) and manifest_state == "valid":
        print("Installation is already up to date.")
    else:
        print(f"Installed AI Dev Framework {version} into {target}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install AI Dev Framework for Codex and Claude Code."
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target meta-repository directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the installation without writing files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(os.path.abspath(Path(args.target).expanduser()))
    try:
        return install(target, dry_run=args.dry_run)
    except SourceValidationError as error:
        print(f"Invalid framework source: {error}", file=sys.stderr)
        return 1
    except InstallError as error:
        print(f"Installation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
