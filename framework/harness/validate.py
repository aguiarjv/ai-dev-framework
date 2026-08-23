#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

from common import framework_root, pack_path, parse_pack
from contracts import SCHEMA_DIR, validate_contract
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

    validate_workflow_schemas(errors)
    validate_capability_registry(root, errors)

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
        if not any((root / ".ai" / "templates" / f"{template}{suffix}").exists() for suffix in [".md", ".sh", ".json"]):
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
    if "framework/skills/" in text:
        errors.append(f"{skill_md}: references the stale framework/skills path")

    for reference in re.findall(r"references/([A-Za-z0-9._-]+)", text):
        if not (skill_dir / "references" / reference).exists():
            errors.append(f"{skill_md}: missing referenced file references/{reference}")


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

    seen: set[Path] = set()
    for relative_path, content in actions:
        if relative_path in seen:
            errors.append(f"{pack_file}: duplicate rendered destination {relative_path}")
        seen.add(relative_path)
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
    if "Portable agent contract:" not in data.get("developer_instructions", ""):
        errors.append(f"{relative_path}: missing portable agent contract metadata")


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


def validate_workflow_schemas(errors: list[str]) -> None:
    expected = {
        "task-contract.schema.json",
        "handoff.schema.json",
        "agent-result.schema.json",
        "review-finding.schema.json",
        "workflow-state.schema.json",
    }
    for name in expected:
        path = SCHEMA_DIR / name
        if not path.exists():
            errors.append(f"Missing workflow schema: {path}")
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        if not isinstance(schema, dict) or schema.get("type") != "object":
            errors.append(f"{path}: workflow schemas must define an object")

    sample = {
        "schema_version": "1",
        "task_id": "schema-smoke-test",
        "title": "Schema smoke test",
        "status": "draft",
        "task_type": "test",
        "objective": "Validate the workflow contract validator.",
        "scope": {"in": ["contract validation"], "out": []},
        "acceptance_criteria": [
            {"id": "AC-1", "statement": "The schema validates.", "verification": ["unit test"]}
        ],
        "subtasks": [
            {
                "id": "T-1",
                "title": "Run schema validation",
                "task_type": "test",
                "owner": "harness",
                "status": "pending",
                "depends_on": [],
                "paths": [],
                "acceptance_criteria": ["AC-1"],
                "verification": ["unit test"],
                "parallelizable": False,
                "done_when": "The validator accepts this document.",
            }
        ],
        "risk": {"level": "low", "areas": []},
        "review_policy": {"required": True, "max_remediation_cycles": 2, "slices": []},
    }
    for error in validate_contract(sample, "task-contract.schema.json"):
        errors.append(f"Workflow schema smoke test: {error}")

    state = {
        "schema_version": "1",
        "task_id": "schema-smoke-test",
        "phase": "intake",
        "status": "pending",
        "active_subtask": None,
        "review_cycles": 0,
        "blockers": [],
        "history": [
            {
                "phase": "intake",
                "status": "pending",
                "at": "2026-01-01T00:00:00Z",
                "actor": "harness",
                "evidence": ["schema smoke test"],
            }
        ],
    }
    for error in validate_contract(state, "workflow-state.schema.json"):
        errors.append(f"Workflow state smoke test: {error}")


def validate_capability_registry(root: Path, errors: list[str]) -> None:
    path = root / ".ai" / "agent-capabilities.md"
    if not path.exists():
        errors.append(f"Missing capability registry: {path}")
        return
    text = path.read_text(encoding="utf-8")
    for agent in sorted(path.stem for path in (root / ".ai" / "agents").glob("*.md")):
        if f"`{agent}`" not in text:
            errors.append(f"{path}: missing agent {agent}")
    for skill in sorted(path.parent.joinpath("skills").iterdir()):
        if skill.is_dir() and (skill / "SKILL.md").exists() and f"`{skill.name}`" not in text:
            errors.append(f"{path}: missing skill {skill.name}")


if __name__ == "__main__":
    raise SystemExit(main())
