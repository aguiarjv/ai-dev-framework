#!/usr/bin/env python3
"""Apply one validated plan-state transition without hand-editing three files."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from validate_plan import PlanValidator, TASK_ID_PATTERN


class TransitionError(ValueError):
    pass


def project_root(plan_dir: Path) -> Path:
    if plan_dir.parent.name != "workspace-plans":
        raise TransitionError("Transition requires an active workspace-plans/<plan-id> directory")
    return plan_dir.parent.parent


def required_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise TransitionError(f"Required regular file is missing: {path}")
    return path.read_text(encoding="utf-8")


def artifact(project: Path, value: str, prefix: tuple[str, ...]) -> Path:
    parts = Path(value).parts
    if (Path(value).is_absolute() or "\\" in value or
            len(parts) <= len(prefix) or parts[:len(prefix)] != prefix or
            any(part in {"", ".", ".."} for part in parts) or
            not value.endswith(".md")):
        raise TransitionError(f"Artifact must be a normalized Markdown path below {'/'.join(prefix)}/")
    path = project.joinpath(*parts)
    required_file(path)
    return path


def frontmatter_value(text: str, key: str) -> object:
    head, separator, _ = text.partition("\n---\n")
    if not separator or not head.startswith("---\n"):
        raise TransitionError("Missing supported YAML frontmatter")
    match = re.findall(rf"(?m)^{re.escape(key)}: (.*)$", head)
    if len(match) != 1:
        raise TransitionError(f"Expected one frontmatter key: {key}")
    raw = match[0].strip()
    return json.loads(raw) if raw.startswith('"') else raw


def set_frontmatter(text: str, key: str, value: str) -> str:
    head, separator, tail = text.partition("\n---\n")
    if not separator or not head.startswith("---\n"):
        raise TransitionError("Missing supported YAML frontmatter")
    updated, count = re.subn(
        rf"(?m)^{re.escape(key)}: .*$", f"{key}: {value}", head
    )
    if count != 1:
        raise TransitionError(f"Expected one frontmatter key: {key}")
    return updated + separator + tail


def section(text: str, heading: str) -> tuple[str, str, str]:
    marker = f"## {heading}\n"
    if text.count(marker) != 1:
        raise TransitionError(f"Expected one section: {heading}")
    before, rest = text.split(marker, 1)
    match = re.search(r"(?m)^## ", rest)
    if match:
        return before + marker, rest[:match.start()], rest[match.start():]
    return before + marker, rest, ""


def replace_section(text: str, heading: str, body: str) -> str:
    before, _, after = section(text, heading)
    return before + "\n" + body.rstrip() + "\n\n" + after.lstrip("\n")


def replace_row(text: str, heading: str, task_id: str, columns: list[str]) -> str:
    before, body, after = section(text, heading)
    lines = body.splitlines(keepends=True)
    indexes = [i for i, line in enumerate(lines) if line.startswith(f"| `{task_id}` |")]
    if len(indexes) != 1:
        raise TransitionError(f"Expected one {heading} row for {task_id}")
    lines[indexes[0]] = "| " + " | ".join(columns) + " |\n"
    return before + "".join(lines) + after


def check_criteria(text: str, accept_all: bool) -> str:
    before, body, after = section(text, "Acceptance Criteria")
    unchecked = len(re.findall(r"(?m)^\s*[-*]\s+\[ \]\s+", body))
    if unchecked and not accept_all:
        raise TransitionError("Acceptance criteria remain unchecked; pass --accept-all only after verifying them")
    if accept_all:
        body = re.sub(r"(?m)^(\s*[-*]\s+)\[ \](\s+)", r"\1[x]\2", body)
    return before + body + after


def set_review_section(text: str, review_path: str) -> str:
    before, body, after = section(text, "Review")
    for label, replacement in (
        ("Latest review", review_path),
        ("Result", "Clean final review; awaiting integration."),
    ):
        body, count = re.subn(
            rf"(?m)^- {label}: .*$", f"- {label}: {replacement}", body
        )
        if count != 1:
            raise TransitionError(f"Expected one Review field: {label}")
    return before + body + after


def validate(plan_dir: Path) -> None:
    errors = PlanValidator(plan_dir).run()
    if errors:
        raise TransitionError("Plan validation failed:\n" + "\n".join(errors))


def atomic_write(path: Path, content: str) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".plan-state-", dir=path.parent)
    try:
        os.fchmod(descriptor, path.stat().st_mode & 0o777)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def transition_ready_for_integration(
    plan_dir: Path, task_id: str, review: str, handoff: str,
    *, accept_all: bool, dry_run: bool = False,
) -> bool:
    plan_dir = plan_dir.resolve()
    if not TASK_ID_PATTERN.fullmatch(task_id) or "/" in task_id:
        raise TransitionError("Invalid task ID")
    project = project_root(plan_dir)
    task_dir = plan_dir / "tasks" / task_id
    task_definition = task_dir / "TASK.md"
    task_progress = task_dir / "PROGRESS.md"
    plan_progress = plan_dir / "PROGRESS.md"
    originals = {
        task_definition: required_file(task_definition),
        task_progress: required_file(task_progress),
        plan_progress: required_file(plan_progress),
    }
    artifact(project, review, ("workspace-reviews", plan_dir.name))
    artifact(project, handoff, ("workspace-plans", plan_dir.name, "tasks", task_id, "handoffs"))
    status = frontmatter_value(originals[task_progress], "status")
    if status == "ready-for-integration":
        if (frontmatter_value(originals[task_progress], "latest_review") == review and
                frontmatter_value(originals[task_progress], "latest_handoff") == handoff):
            validate(plan_dir)
            return False
        raise TransitionError("Task is already ready for integration with different artifacts")
    if status != "ready-for-review":
        raise TransitionError("Task must be ready-for-review")
    if frontmatter_value(originals[plan_progress], "status") != "in-progress":
        raise TransitionError("Plan must be in-progress")
    validate(plan_dir)
    if any(path.is_symlink() for path in plan_dir.rglob("*")):
        raise TransitionError("Plan contains a symlink; staged validation cannot safely follow it")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    definition = check_criteria(originals[task_definition], accept_all)
    progress = originals[task_progress]
    for key, value in (
        ("status", "ready-for-integration"),
        ("updated", json.dumps(now)),
        ("latest_review", json.dumps(review)),
        ("latest_handoff", json.dumps(handoff)),
    ):
        progress = set_frontmatter(progress, key, value)
    progress = set_review_section(progress, review)
    next_action = "Integrate the exact cleanly reviewed task head into the plan integration branch."
    progress = replace_section(progress, "Next Action", next_action)

    plan = set_frontmatter(originals[plan_progress], "updated", json.dumps(now))
    plan = replace_row(plan, "Task Status", task_id, [
        f"`{task_id}`", "`ready-for-integration`", "Clean final review; awaiting integration.",
    ])
    plan = replace_row(plan, "Next Actions", task_id, [f"`{task_id}`", next_action])
    updates = {
        task_definition: definition,
        task_progress: progress,
        plan_progress: plan,
    }

    with tempfile.TemporaryDirectory(prefix="plan-state-") as temporary:
        staged_project = Path(temporary) / "project"
        staged_plan = staged_project / "workspace-plans" / plan_dir.name
        staged_plan.parent.mkdir(parents=True)
        shutil.copytree(plan_dir, staged_plan, symlinks=True)
        staged_review = staged_project / review
        staged_review.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / review, staged_review)
        for path, content in updates.items():
            (staged_plan / path.relative_to(plan_dir)).write_text(content, encoding="utf-8")
        validate(staged_plan)

    if dry_run:
        return True
    for path, original in originals.items():
        if required_file(path) != original:
            raise TransitionError(f"File changed during transition staging: {path}")
    changed: list[Path] = []
    try:
        for path, content in updates.items():
            if content != originals[path]:
                atomic_write(path, content)
                changed.append(path)
        validate(plan_dir)
    except (OSError, TransitionError):
        for path in reversed(changed):
            atomic_write(path, originals[path])
        raise
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    transition = commands.add_parser("transition", help="Apply a validated state transition")
    transition.add_argument("task_id")
    transition.add_argument("status", choices=["ready-for-integration"])
    transition.add_argument("--review", required=True,
                            help="Managed-project-relative clean final review")
    transition.add_argument("--handoff", required=True,
                            help="Managed-project-relative reviewer handoff")
    transition.add_argument("--accept-all", action="store_true",
                        help="Affirm every unchecked acceptance criterion is satisfied")
    transition.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        changed = transition_ready_for_integration(
            args.plan, args.task_id, args.review, args.handoff,
            accept_all=args.accept_all, dry_run=args.dry_run,
        )
    except (OSError, TransitionError) as error:
        print(f"Plan state: {error}", file=sys.stderr)
        return 2
    print("VALIDATED " + ("no change" if not changed else "ready-for-integration" +
                           (" (dry run)" if args.dry_run else "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
