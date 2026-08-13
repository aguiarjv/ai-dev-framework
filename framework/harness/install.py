#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import framework_root, pack_path, parse_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Install AI Dev Framework assets into a target project.")
    parser.add_argument("--target", required=True, help="Target project directory.")
    parser.add_argument("--pack", default="core", help="Pack name from framework/packs.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without changing files.")
    parser.add_argument("--force", action="store_true", help="Overwrite differing target files.")
    args = parser.parse_args()

    root = framework_root()
    target = Path(args.target).expanduser().resolve()
    pack = parse_pack(pack_path(args.pack))
    actions = build_actions(root, pack)

    collisions = []
    for relative_target, content in actions:
        destination = target / relative_target
        if destination.exists() and destination.read_bytes() != content and not args.force:
            collisions.append(relative_target)

    if collisions:
        print("Refusing to overwrite differing files without --force:")
        for item in collisions:
            print(f"  {item}")
        return 2

    installed_files: list[str] = []
    for relative_target, content in actions:
        destination = target / relative_target
        installed_files.append(write_item(relative_target, content, destination, args.dry_run))
    installed_files.extend(ensure_project_state(target, args.dry_run))

    manifest = {
        "framework": "ai-dev-framework",
        "pack": pack["name"],
        "version": pack["version"],
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "files": sorted(installed_files),
    }
    manifest_path = target / ".ai-dev-framework.json"
    if args.dry_run:
        print(f"DRY RUN write {manifest_path}")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {manifest_path}")

    return 0


def build_actions(root: Path, pack: dict) -> list[tuple[Path, bytes]]:
    actions: list[tuple[Path, bytes]] = []

    guide_path = root / ".ai" / "guides" / f"{pack['guide']}.md"
    guide_text = guide_path.read_text(encoding="utf-8")
    actions.append((Path(".ai") / "guides" / guide_path.name, guide_text.encode("utf-8")))
    actions.append((Path("AGENTS.md"), render_codex_guide(pack["guide"], guide_text).encode("utf-8")))

    for guide in pack.get("guides", []):
        supplemental = root / ".ai" / "guides" / f"{guide}.md"
        actions.append((Path(".ai") / "guides" / supplemental.name, supplemental.read_bytes()))

    adapters = set(pack.get("adapters", []))
    if "claude" in adapters:
        actions.append((Path("CLAUDE.md"), render_claude_guide(pack["guide"]).encode("utf-8")))

    for agent_name in pack["agents"]:
        source = root / ".ai" / "agents" / f"{agent_name}.md"
        text = source.read_text(encoding="utf-8")
        meta, body = parse_agent_source(text)
        actions.append((Path(".ai") / "agents" / source.name, text.encode("utf-8")))
        if "codex" in adapters:
            actions.append((Path(".codex") / "agents" / f"{agent_name}.toml", render_codex_agent(meta, body).encode("utf-8")))
        if "claude" in adapters:
            actions.append((Path(".claude") / "agents" / f"{agent_name}.md", render_claude_agent(meta, body).encode("utf-8")))

    for template in pack.get("templates", []):
        source = template_path(root, template)
        actions.append((Path(".ai") / "templates" / source.name, source.read_bytes()))

    for harness in pack.get("harnesses", []):
        if harness == "registry":
            source = root / ".ai" / "harnesses" / "registry.md"
            actions.append((Path(".ai") / "harnesses" / "registry.md", source.read_bytes()))
            continue
        source = root / ".ai" / "harnesses" / harness
        for file_path in sorted(path for path in source.rglob("*") if path.is_file()):
            relative = file_path.relative_to(root / ".ai")
            actions.append((Path(".ai") / relative, file_path.read_bytes()))

    harness_scripts = root / ".ai" / "harnesses" / "scripts"
    for file_path in sorted(path for path in harness_scripts.rglob("*") if path.is_file()):
        relative = file_path.relative_to(root / ".ai")
        action = (Path(".ai") / relative, file_path.read_bytes())
        if action not in actions:
            actions.append(action)

    for skill in pack["skills"]:
        source = root / ".ai" / "skills" / skill
        for file_path in sorted(path for path in source.rglob("*") if path.is_file()):
            relative = file_path.relative_to(root / ".ai")
            content = file_path.read_bytes()
            actions.append((Path(".ai") / relative, content))
            if "codex" in adapters:
                skill_relative = file_path.relative_to(source)
                if skill_relative == Path("SKILL.md"):
                    content = render_codex_skill(skill, content.decode("utf-8")).encode("utf-8")
                actions.append((Path(".agents") / "skills" / skill / skill_relative, content))

    return actions


def template_path(root: Path, template: str) -> Path:
    for suffix in [".md", ".sh"]:
        source = root / ".ai" / "templates" / f"{template}{suffix}"
        if source.exists():
            return source
    raise FileNotFoundError(f"Template not found: {template}")


def ensure_project_state(target: Path, dry_run: bool) -> list[str]:
    paths = [
        Path("docs") / "tasks" / ".gitkeep",
        Path("docs") / "adr" / ".gitkeep",
        Path(".local") / "tasks" / ".gitkeep",
        Path("harness") / ".gitkeep",
    ]
    installed = []
    for relative_path in paths:
        destination = target / relative_path
        if dry_run:
            print(f"DRY RUN ensure {destination}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_text("", encoding="utf-8")
            print(f"Ensured {relative_path}")
        installed.append(relative_path.as_posix())

    installed.append(ensure_gitignore(target, dry_run))
    return installed


def ensure_gitignore(target: Path, dry_run: bool) -> str:
    relative_path = Path(".gitignore")
    destination = target / relative_path
    line = ".local/"
    block = f"\n# AI Dev Framework local state\n{line}\n"

    if dry_run:
        print(f"DRY RUN ensure {destination} contains {line}")
        return relative_path.as_posix()

    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_text(f"{line}\n", encoding="utf-8")
        print(f"Wrote {relative_path}")
        return relative_path.as_posix()

    text = destination.read_text(encoding="utf-8")
    if line not in {existing.strip() for existing in text.splitlines()}:
        separator = "" if text.endswith("\n") else "\n"
        destination.write_text(f"{text}{separator}{block.lstrip()}", encoding="utf-8")
        print(f"Updated {relative_path}")
    else:
        print(f"Ensured {relative_path}")
    return relative_path.as_posix()


def parse_agent_source(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("Agent source is missing frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Agent source frontmatter is unterminated")
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("\"'")
    return meta, text[end + 5 :].strip() + "\n"


def render_codex_guide(source_name: str, guide_text: str) -> str:
    return f"<!-- Generated from .ai/guides/{source_name}.md. Edit the .ai source, then reinstall. -->\n\n{guide_text}"


def render_claude_guide(source_name: str) -> str:
    return f"<!-- Generated from .ai/guides/{source_name}.md. Edit the .ai source, then reinstall. -->\n\n# Project AI Guidance\n\nGenerated adapter. Source of truth:\n\n@.ai/guides/{source_name}.md\n"


def render_codex_agent(meta: dict[str, str], body: str) -> str:
    return "\n".join(
        [
            f"# Generated from .ai/agents/{meta['name']}.md. Edit the .ai source, then reinstall.",
            f"name = {toml_quote(meta['name'])}",
            f"description = {toml_quote(meta['description'])}",
            f"developer_instructions = {toml_multiline(body)}",
            "",
        ]
    )


def render_claude_agent(meta: dict[str, str], body: str) -> str:
    lines = [
        "---",
        f"name: {meta['name']}",
        f"description: {meta['description']}",
    ]
    tools = claude_tools(meta.get("tools", ""))
    if tools:
        lines.append(f"tools: {tools}")
    permission_mode = claude_permission_mode(meta.get("permission_mode", ""))
    if permission_mode:
        lines.append(f"permissionMode: {permission_mode}")
    if meta.get("model") and meta["model"] != "inherit":
        lines.append(f"model: {meta['model']}")
    lines.extend(
        [
            "---",
            "",
            f"<!-- Generated from .ai/agents/{meta['name']}.md. Edit the .ai source, then reinstall. -->",
            "",
            body.rstrip(),
            "",
        ]
    )
    return "\n".join(lines)


def render_codex_skill(skill: str, text: str) -> str:
    marker = f"<!-- Generated from .ai/skills/{skill}/SKILL.md. Edit the .ai source, then reinstall. -->"
    if not text.startswith("---\n"):
        return f"{marker}\n\n{text}"
    end = text.find("\n---\n", 4)
    if end == -1:
        return f"{marker}\n\n{text}"
    frontmatter_end = end + len("\n---\n")
    return f"{text[:frontmatter_end]}\n{marker}\n\n{text[frontmatter_end:].lstrip()}"


def claude_tools(value: str) -> str:
    if value == "orchestrate":
        return "Agent, Read, Grep, Glob"
    if value == "read":
        return "Read, Grep, Glob"
    if value == "write":
        return "Read, Grep, Glob, Bash, Edit, Write"
    if value == "web":
        return "Read, Grep, Glob, Bash"
    return ""


def claude_permission_mode(value: str) -> str:
    if value == "read-only":
        return "default"
    if value == "project-write":
        return "acceptEdits"
    return ""


def toml_quote(value: str) -> str:
    return json.dumps(value)


def toml_multiline(value: str) -> str:
    escaped = value.replace('"""', '\\"\\"\\"')
    return f'"""\n{escaped}"""'


def write_item(relative_destination: Path, content: bytes, destination: Path, dry_run: bool) -> str:
    if dry_run:
        print(f"DRY RUN write {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        print(f"Wrote {relative_destination}")
    return relative_destination.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
