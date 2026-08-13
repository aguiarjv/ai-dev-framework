#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

from common import framework_root, pack_path, parse_pack
from install import build_actions, parse_agent_source

SKILL_NAME = re.compile(r"^[a-z0-9-]+$")
GENERATED_MARKER = "Generated from .ai/"
AGENT_TOOLS = {"read", "write", "web", "orchestrate"}
AGENT_PERMISSION_MODES = {"read-only", "project-write"}


def main() -> int:
    root = framework_root()
    errors: list[str] = []

    for pack_file in sorted((root / "framework" / "packs").glob("*.yaml")):
        try:
            pack = parse_pack(pack_file)
        except Exception as exc:
            errors.append(f"{pack_file}: {exc}")
            continue
        validate_pack(root, pack_file, pack, errors)

    for skill_dir in sorted((root / ".ai" / "skills").iterdir()):
        if skill_dir.is_dir():
            validate_skill(skill_dir, errors)

    for agent_file in sorted((root / ".ai" / "agents").glob("*.md")):
        validate_agent_source(agent_file, errors)

    for script in [root / "framework" / "harness" / "install.sh", root / "framework" / "harness" / "validate.sh"]:
        if not script.exists():
            errors.append(f"Missing script: {script}")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Validation passed.")
    return 0


def validate_pack(root: Path, pack_file: Path, pack: dict, errors: list[str]) -> None:
    for key in ["name", "version", "guide", "adapters", "agents", "skills"]:
        if key not in pack:
            errors.append(f"{pack_file}: missing {key}")

    guide = pack.get("guide")
    if not guide or not (root / ".ai" / "guides" / f"{guide}.md").exists():
        errors.append(f"{pack_file}: missing guide {guide}")

    for guide_name in pack.get("guides", []):
        if not SKILL_NAME.match(str(guide_name)):
            errors.append(f"{pack_file}: invalid guide name {guide_name}")
        if not (root / ".ai" / "guides" / f"{guide_name}.md").exists():
            errors.append(f"{pack_file}: missing guide {guide_name}")

    for adapter in pack.get("adapters", []):
        if adapter not in {"codex", "claude"}:
            errors.append(f"{pack_file}: unknown adapter {adapter}")

    for agent in pack.get("agents", []):
        if not SKILL_NAME.match(str(agent)):
            errors.append(f"{pack_file}: invalid agent name {agent}")
        if not (root / ".ai" / "agents" / f"{agent}.md").exists():
            errors.append(f"{pack_file}: missing agent {agent}")

    for template in pack.get("templates", []):
        if not SKILL_NAME.match(str(template)):
            errors.append(f"{pack_file}: invalid template name {template}")
        if not any((root / ".ai" / "templates" / f"{template}{suffix}").exists() for suffix in [".md", ".sh"]):
            errors.append(f"{pack_file}: missing template {template}")

    for harness in pack.get("harnesses", []):
        if not SKILL_NAME.match(str(harness)):
            errors.append(f"{pack_file}: invalid harness name {harness}")
        if harness == "registry":
            if not (root / ".ai" / "harnesses" / "registry.md").exists():
                errors.append(f"{pack_file}: missing harness registry")
        elif not (root / ".ai" / "harnesses" / str(harness)).exists():
            errors.append(f"{pack_file}: missing harness {harness}")

    if not (root / ".ai" / "harnesses" / "scripts").exists():
        errors.append("missing .ai/harnesses/scripts")

    for skill in pack.get("skills", []):
        if not SKILL_NAME.match(str(skill)):
            errors.append(f"{pack_file}: invalid skill name {skill}")
        if not (root / ".ai" / "skills" / str(skill) / "SKILL.md").exists():
            errors.append(f"{pack_file}: missing skill {skill}")

    if not any(str(error).startswith(str(pack_file)) for error in errors):
        validate_rendered_pack(root, pack_file, pack, errors)


def validate_skill(skill_dir: Path, errors: list[str]) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"{skill_dir}: missing SKILL.md")
        return

    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{skill_md}: missing YAML frontmatter")
        return

    end = text.find("\n---\n", 4)
    if end == -1:
        errors.append(f"{skill_md}: unterminated YAML frontmatter")
        return

    frontmatter = text[4:end].splitlines()
    values = {}
    for line in frontmatter:
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("\"'")

    expected_name = skill_dir.name
    if values.get("name") != expected_name:
        errors.append(f"{skill_md}: name must be {expected_name}")
    if not values.get("description") or "TODO" in values.get("description", ""):
        errors.append(f"{skill_md}: description is missing or still TODO")
    if "[TODO" in text:
        errors.append(f"{skill_md}: contains TODO template text")


def validate_agent_source(agent_file: Path, errors: list[str]) -> None:
    try:
        data, body = parse_agent_source(agent_file.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{agent_file}: invalid agent source: {exc}")
        return

    for key in ["name", "description"]:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{agent_file}: missing frontmatter field {key}")

    if data.get("name") != agent_file.stem:
        errors.append(f"{agent_file}: name must match file stem")
    if data.get("tools") and data["tools"] not in AGENT_TOOLS:
        errors.append(f"{agent_file}: unknown tools value {data['tools']}")
    if data.get("permission_mode") and data["permission_mode"] not in AGENT_PERMISSION_MODES:
        errors.append(f"{agent_file}: unknown permission_mode value {data['permission_mode']}")
    if not body.strip():
        errors.append(f"{agent_file}: missing prompt body")


def validate_rendered_pack(root: Path, pack_file: Path, pack: dict, errors: list[str]) -> None:
    try:
        actions = build_actions(root, pack)
    except Exception as exc:
        errors.append(f"{pack_file}: render failed: {exc}")
        return

    for relative_path, content in actions:
        if relative_path.suffix == ".toml" and ".codex/agents" in relative_path.as_posix():
            validate_agent_toml(relative_path, content, errors)
        if relative_path.suffix == ".md" and ".claude/agents" in relative_path.as_posix():
            validate_claude_agent(relative_path, content, errors)
        if relative_path in {Path("AGENTS.md"), Path("CLAUDE.md")}:
            validate_generated_marker(relative_path, content, errors)
        if relative_path.as_posix().startswith(".agents/skills/") and relative_path.name == "SKILL.md":
            validate_generated_marker(relative_path, content, errors)


def validate_agent_toml(relative_path: Path, content: bytes, errors: list[str]) -> None:
    validate_generated_marker(relative_path, content, errors)
    try:
        data = tomllib.loads(content.decode("utf-8"))
    except Exception as exc:
        errors.append(f"{relative_path}: invalid TOML: {exc}")
        return

    for key in ["name", "description", "developer_instructions"]:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{relative_path}: missing string field {key}")

    if data.get("name") != relative_path.stem:
        errors.append(f"{relative_path}: name must match file stem")


def validate_claude_agent(relative_path: Path, content: bytes, errors: list[str]) -> None:
    text = content.decode("utf-8")
    validate_generated_marker(relative_path, content, errors)
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        errors.append(f"{relative_path}: missing YAML frontmatter")
        return
    if f"name: {relative_path.stem}" not in text:
        errors.append(f"{relative_path}: name must match file stem")
    if relative_path.stem == "orchestrator" and "tools: Agent, Read, Grep, Glob" not in text:
        errors.append(f"{relative_path}: orchestrator must include Agent tool")


def validate_generated_marker(relative_path: Path, content: bytes, errors: list[str]) -> None:
    text = content.decode("utf-8", errors="replace")
    first_lines = "\n".join(text.splitlines()[:10])
    if GENERATED_MARKER not in first_lines:
        errors.append(f"{relative_path}: missing generated source marker")


if __name__ == "__main__":
    raise SystemExit(main())
