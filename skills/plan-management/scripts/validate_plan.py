#!/usr/bin/env python3
"""Validate an AI Dev Framework plan directory."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


PLAN_STATUSES = {"not-started", "in-progress", "blocked", "completed"}
TASK_STATUSES = PLAN_STATUSES | {
    "ready-for-review",
    "ready-for-integration",
    "needs-fix",
}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
COMMIT_PATTERN = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
TASK_ID_PATTERN = re.compile(r"^\d{3}-.+$")
PLACEHOLDER_PATTERN = re.compile(r"<[^>\n]+>")

PLAN_SECTIONS = {
    "Goal",
    "Context",
    "Scope",
    "Approach",
    "Integration",
    "Dependencies",
    "Related Files and Folders",
    "Relevant Documentation and Guides",
    "Open Questions",
    "Architecture Decisions",
    "Tasks",
    "Completion Criteria",
}
PLAN_PROGRESS_SECTIONS = {
    "Summary",
    "Integration",
    "Task Status",
    "Blockers",
    "Next Actions",
}
TASK_SECTIONS = {
    "Objective",
    "Requirements",
    "Related Files and Folders",
    "Relevant Documentation and Guides",
    "Acceptance Criteria",
    "Validation",
    "Review Checkpoints",
}
TASK_PROGRESS_SECTIONS = {
    "Summary",
    "Work Completed",
    "Decisions",
    "Changed Files",
    "Validation",
    "Blockers",
    "Review",
    "Next Action",
}

RELATED_PATH_HEADERS = ["Path", "State", "Expected Use", "Relevance", "Evidence"]
DOCUMENTATION_HEADERS = [
    "Path",
    "Source",
    "State",
    "Expected Use",
    "Relevance",
    "Evidence",
]
PLAN_TASK_HEADERS = ["ID", "Task", "Depends on"]
TASK_STATUS_HEADERS = ["Task", "Status", "Result or blocker"]
NEXT_ACTION_HEADERS = ["Task", "Action"]
ARCHITECTURE_HEADERS = ["Decision", "ADR Required", "Path", "Rationale"]
PATH_STATES = {"existing", "planned"}
EXPECTED_USES = {"inspect", "modify", "create"}
DOCUMENTATION_SOURCES = {"project-docs", "workspace-guide"}
NONE_VALUES = {"none", "none.", "n/a", "n/a."}


@dataclass
class MarkdownDocument:
    path: Path
    text: str
    frontmatter: dict[str, Any]
    body: str


@dataclass
class MarkdownTable:
    headers: list[str]
    rows: list[list[str]]


class PlanValidator:
    def __init__(self, plan_dir: Path) -> None:
        self.plan_dir = plan_dir
        self.errors: list[str] = []

    def error(self, path: Path, message: str) -> None:
        try:
            display_path = path.relative_to(self.plan_dir)
        except ValueError:
            display_path = path
        self.errors.append(f"{display_path}: {message}")

    def managed_project_root(self) -> Path | None:
        parent = self.plan_dir.parent
        if parent.name == "plans":
            return parent.parent
        if parent.name == "done" and parent.parent.name == "plans":
            return parent.parent.parent
        return None

    def read_document(self, path: Path) -> MarkdownDocument | None:
        if not path.is_file():
            self.error(path, "required file is missing")
            return None

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self.error(path, f"cannot read UTF-8 Markdown: {exc}")
            return None

        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            self.error(path, "YAML frontmatter must start on the first line")
            return MarkdownDocument(path, text, {}, text)

        closing_index = next(
            (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
            None,
        )
        if closing_index is None:
            self.error(path, "YAML frontmatter has no closing delimiter")
            return MarkdownDocument(path, text, {}, "")

        frontmatter: dict[str, Any] = {}
        for line_number, line in enumerate(lines[1:closing_index], start=2):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)", line)
            if not match:
                self.error(path, f"unsupported frontmatter syntax on line {line_number}")
                continue
            key, raw_value = match.groups()
            if key in frontmatter:
                self.error(path, f"duplicate frontmatter key: {key}")
                continue
            frontmatter[key] = self.parse_yaml_value(path, line_number, raw_value)

        for line_number, line in enumerate(lines, start=1):
            for placeholder in PLACEHOLDER_PATTERN.findall(line):
                self.error(path, f"unreplaced placeholder {placeholder!r} on line {line_number}")

        body = "\n".join(lines[closing_index + 1 :])
        return MarkdownDocument(path, text, frontmatter, body)

    def parse_yaml_value(self, path: Path, line_number: int, raw_value: str) -> Any:
        value = raw_value.strip()
        if value in {"null", "~"}:
            return None
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.startswith('"') and value.endswith('"'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                self.error(path, f"invalid quoted value on line {line_number}")
                return value
        if value.startswith("'") and value.endswith("'"):
            try:
                return ast.literal_eval(value)
            except (SyntaxError, ValueError):
                self.error(path, f"invalid quoted value on line {line_number}")
                return value
        if value.startswith("[") and value.endswith("]"):
            if value == "[]":
                return []
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    return parsed
            except (SyntaxError, ValueError):
                pass
            return [item.strip().strip('"\'') for item in value[1:-1].split(",")]
        return value

    def require_keys(
        self, document: MarkdownDocument, required_keys: set[str]
    ) -> None:
        for key in sorted(required_keys - document.frontmatter.keys()):
            self.error(document.path, f"missing frontmatter key: {key}")

    def require_sections(
        self, document: MarkdownDocument, required_sections: set[str]
    ) -> None:
        sections = self.section_map(document)
        for section in sorted(required_sections - sections.keys()):
            self.error(document.path, f"missing section: ## {section}")
        for section, bodies in sorted(sections.items()):
            if section in required_sections and len(bodies) > 1:
                self.error(document.path, f"duplicate section: ## {section}")

    def section_map(self, document: MarkdownDocument) -> dict[str, list[str]]:
        sections: dict[str, list[list[str]]] = {}
        current: list[str] | None = None
        fence: str | None = None

        for line in document.body.splitlines():
            stripped = line.lstrip()
            if fence is not None:
                if stripped.startswith(fence):
                    fence = None
                if current is not None:
                    current.append(line)
                continue
            if stripped.startswith("```"):
                fence = "```"
                if current is not None:
                    current.append(line)
                continue
            if stripped.startswith("~~~"):
                fence = "~~~"
                if current is not None:
                    current.append(line)
                continue

            heading = re.fullmatch(r"##\s+(.+?)\s*#*\s*", stripped)
            if heading:
                title = heading.group(1).strip()
                current = []
                sections.setdefault(title, []).append(current)
            elif current is not None:
                current.append(line)

        return {
            title: ["\n".join(lines) for lines in bodies]
            for title, bodies in sections.items()
        }

    def section_body(self, document: MarkdownDocument, section: str) -> str:
        bodies = self.section_map(document).get(section, [])
        return bodies[0] if bodies else ""

    @staticmethod
    def split_table_row(line: str) -> list[str]:
        value = line.strip()
        if value.startswith("|"):
            value = value[1:]
        if value.endswith("|"):
            value = value[:-1]

        cells: list[str] = []
        current: list[str] = []
        escaped = False
        in_code = False
        for character in value:
            if escaped:
                current.append(character)
                escaped = False
            elif character == "\\":
                current.append(character)
                escaped = True
            elif character == "`":
                current.append(character)
                in_code = not in_code
            elif character == "|" and not in_code:
                cells.append("".join(current).strip())
                current = []
            else:
                current.append(character)
        cells.append("".join(current).strip())
        return cells

    @staticmethod
    def plain_cell(value: str) -> str:
        value = value.strip()
        link = re.fullmatch(r"\[([^]]+)\]\([^)]+\)", value)
        if link:
            value = link.group(1)
        return value.replace("`", "").replace("\\|", "|").strip()

    def parse_table(
        self,
        document: MarkdownDocument,
        section: str,
        expected_headers: list[str],
    ) -> MarkdownTable | None:
        lines = self.section_body(document, section).splitlines()
        header_index = next(
            (index for index, line in enumerate(lines) if line.strip().startswith("|")),
            None,
        )
        if header_index is None:
            self.error(document.path, f"## {section} must contain a Markdown table")
            return None

        separator_index = next(
            (
                index
                for index in range(header_index + 1, len(lines))
                if lines[index].strip()
            ),
            None,
        )
        if separator_index is None:
            self.error(document.path, f"## {section} table is missing its separator row")
            return None

        headers = [self.plain_cell(cell) for cell in self.split_table_row(lines[header_index])]
        separator = self.split_table_row(lines[separator_index])
        if len(separator) != len(headers) or not all(
            re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in separator
        ):
            self.error(document.path, f"## {section} table has an invalid separator row")
            return None
        if headers != expected_headers:
            self.error(
                document.path,
                f"## {section} table headers must be: {' | '.join(expected_headers)}",
            )

        rows: list[list[str]] = []
        for line in lines[separator_index + 1 :]:
            if not line.strip():
                if rows:
                    break
                continue
            if not line.strip().startswith("|"):
                break
            cells = self.split_table_row(line)
            if len(cells) != len(expected_headers):
                self.error(
                    document.path,
                    f"## {section} table row must have {len(expected_headers)} cells",
                )
                continue
            rows.append(cells)

        return MarkdownTable(headers, rows)

    @staticmethod
    def meaningful_text(value: str) -> str:
        lines: list[str] = []
        for line in value.splitlines():
            stripped = re.sub(r"^\s*[-*]\s+", "", line).strip()
            if stripped:
                lines.append(stripped)
        return " ".join(lines).strip()

    @classmethod
    def has_meaningful_content(cls, value: str) -> bool:
        normalized = cls.meaningful_text(value).lower()
        return bool(normalized) and normalized not in NONE_VALUES

    def labeled_list_value(
        self,
        document: MarkdownDocument,
        section: str,
        label: str,
    ) -> str:
        match = re.search(
            rf"^\s*[-*]\s+{re.escape(label)}:\s*(.+?)\s*$",
            self.section_body(document, section),
            re.MULTILINE | re.IGNORECASE,
        )
        return self.plain_cell(match.group(1)) if match else ""

    def checklist_states(
        self, document: MarkdownDocument, section: str
    ) -> list[bool]:
        body = self.section_body(document, section)
        matches = re.findall(
            r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$",
            body,
            re.MULTILINE,
        )
        if not matches:
            self.error(document.path, f"## {section} must contain at least one checklist item")
            return []
        return [marker.lower() == "x" for marker, _ in matches]

    def validate_date(self, document: MarkdownDocument, key: str) -> None:
        value = document.frontmatter.get(key)
        if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
            self.error(document.path, f"{key} must use YYYY-MM-DD")

    def validate_timestamp(self, document: MarkdownDocument, key: str = "updated") -> None:
        value = document.frontmatter.get(key)
        if not isinstance(value, str) or not TIMESTAMP_PATTERN.fullmatch(value):
            self.error(document.path, f"{key} must use YYYY-MM-DDTHH:MM:SSZ")

    def validate_status(
        self, document: MarkdownDocument, allowed: set[str]
    ) -> None:
        status = document.frontmatter.get("status")
        if not isinstance(status, str) or status not in allowed:
            self.error(
                document.path,
                f"status must be one of: {', '.join(sorted(allowed))}",
            )

    def validate_worktree(
        self,
        document: MarkdownDocument,
        allow_null: bool,
        key: str = "worktree",
    ) -> None:
        value = document.frontmatter.get(key)
        if allow_null and value is None:
            return
        if not isinstance(value, str):
            self.error(
                document.path,
                f"{key} must be relative to the managed project and start with worktrees/",
            )
            return
        parts = value.split("/")
        if (
            "\\" in value
            or len(parts) < 2
            or parts[0] != "worktrees"
            or any(part in {"", ".", ".."} for part in parts)
            or PurePosixPath(value).is_absolute()
        ):
            self.error(
                document.path,
                f"{key} must be a normalized path below worktrees/",
            )

    def validate_artifact_path(
        self,
        document: MarkdownDocument,
        key: str,
        root: str,
    ) -> None:
        value = document.frontmatter.get(key)
        if value is None:
            return
        if not isinstance(value, str):
            self.error(document.path, f"{key} must be a string path or null")
            return
        parts = value.split("/")
        if (
            "\\" in value
            or len(parts) < 2
            or parts[0] != root
            or any(part in {"", ".", ".."} for part in parts)
            or PurePosixPath(value).is_absolute()
            or not value.endswith(".md")
        ):
            self.error(
                document.path,
                f"{key} must be a normalized Markdown path below {root}/",
            )

    def validate_commit(self, document: MarkdownDocument, key: str) -> None:
        value = document.frontmatter.get(key)
        if value is not None and (
            not isinstance(value, str) or not COMMIT_PATTERN.fullmatch(value)
        ):
            self.error(document.path, f"{key} must be a full Git commit SHA or null")

    def read_review(
        self,
        progress: MarkdownDocument,
    ) -> MarkdownDocument | None:
        value = progress.frontmatter.get("latest_review")
        if not isinstance(value, str):
            return None

        project_root = self.managed_project_root()
        if project_root is None:
            return None

        parts = value.split("/")
        if (
            "\\" in value
            or len(parts) < 2
            or parts[0] != "reviews"
            or any(part in {"", ".", ".."} for part in parts)
            or PurePosixPath(value).is_absolute()
            or not value.endswith(".md")
        ):
            return None

        return self.read_document(project_root.joinpath(*parts))

    def validate_review_result(
        self,
        progress: MarkdownDocument,
        expected_status: str,
    ) -> MarkdownDocument | None:
        review = self.read_review(progress)
        if review is None:
            return None

        actual_status = review.frontmatter.get("status")
        if actual_status != expected_status:
            self.error(
                progress.path,
                f"latest_review must have status {expected_status!r}, got {actual_status!r}",
            )
        return review

    def plan_integration_review_is_current(
        self,
        plan_id: str,
        progress: MarkdownDocument,
        *,
        report_errors: bool,
    ) -> bool:
        review = self.read_review(progress)
        if review is None:
            if report_errors:
                self.error(
                    progress.path,
                    "a completed plan must record a clean integration latest_review",
                )
            return False

        expected = {
            "plan": plan_id,
            "task": None,
            "review_kind": "plan-integration",
            "status": "clean",
            "worktree": progress.frontmatter.get("integration_worktree"),
            "branch": progress.frontmatter.get("integration_branch"),
            "head_commit": progress.frontmatter.get("integration_head_commit"),
            "uncommitted_changes": progress.frontmatter.get(
                "integration_uncommitted_changes"
            ),
        }
        matches = True
        for key, expected_value in expected.items():
            actual_value = review.frontmatter.get(key)
            if actual_value != expected_value:
                matches = False
                if report_errors:
                    self.error(
                        progress.path,
                        f"integration latest_review {key} must be {expected_value!r}, "
                        f"got {actual_value!r}",
                    )
        return matches

    def validate_task_final_review(
        self,
        definition: MarkdownDocument,
        progress: MarkdownDocument,
        expected_status: str,
    ) -> None:
        review = self.validate_review_result(progress, expected_status)
        if review is None:
            return

        expected = {
            "plan": definition.frontmatter.get("plan"),
            "task": definition.frontmatter.get("id"),
            "review_kind": "task-final",
            "worktree": progress.frontmatter.get("worktree"),
            "branch": progress.frontmatter.get("branch"),
            "head_commit": progress.frontmatter.get("head_commit"),
            "uncommitted_changes": progress.frontmatter.get("uncommitted_changes"),
        }
        for key, expected_value in expected.items():
            actual_value = review.frontmatter.get(key)
            if actual_value != expected_value:
                self.error(
                    progress.path,
                    f"latest_review {key} must be {expected_value!r}, got {actual_value!r}",
                )

    def validate_plan_definition(
        self, document: MarkdownDocument, plan_id: str
    ) -> None:
        required = {
            "id",
            "title",
            "created",
            "updated",
            "worktree",
            "branch",
            "baseline_commit",
            "planned_integration_worktree",
            "planned_integration_branch",
            "delivery_branch",
            "approved_at",
        }
        self.require_keys(document, required)
        self.require_sections(document, PLAN_SECTIONS)
        self.validate_date(document, "created")
        self.validate_timestamp(document)
        self.validate_timestamp(document, "approved_at")
        self.validate_worktree(document, allow_null=False)
        self.validate_worktree(
            document,
            allow_null=False,
            key="planned_integration_worktree",
        )
        self.validate_commit(document, "baseline_commit")
        if document.frontmatter.get("id") != plan_id:
            self.error(document.path, f"id must match plan folder name {plan_id!r}")
        if not isinstance(document.frontmatter.get("title"), str) or not document.frontmatter.get(
            "title"
        ):
            self.error(document.path, "title must be a non-empty string")
        if not isinstance(document.frontmatter.get("branch"), str) or not document.frontmatter.get(
            "branch"
        ):
            self.error(document.path, "branch must be a non-empty string")
        for key in ("planned_integration_branch", "delivery_branch"):
            if not isinstance(document.frontmatter.get(key), str) or not document.frontmatter.get(
                key
            ):
                self.error(document.path, f"{key} must be a non-empty string")

    def validate_plan_progress(
        self, document: MarkdownDocument, plan_id: str
    ) -> None:
        self.require_keys(
            document,
            {
                "plan",
                "status",
                "updated",
                "current_tasks",
                "integration_worktree",
                "integration_branch",
                "integration_head_commit",
                "integration_uncommitted_changes",
                "latest_handoff",
                "latest_review",
            },
        )
        self.require_sections(document, PLAN_PROGRESS_SECTIONS)
        self.validate_status(document, PLAN_STATUSES)
        self.validate_timestamp(document)
        self.validate_worktree(document, allow_null=True, key="integration_worktree")
        self.validate_commit(document, "integration_head_commit")
        self.validate_artifact_path(document, "latest_handoff", "plans")
        self.validate_artifact_path(document, "latest_review", "reviews")
        if document.frontmatter.get("plan") != plan_id:
            self.error(document.path, f"plan must match plan folder name {plan_id!r}")
        if not isinstance(document.frontmatter.get("current_tasks"), list):
            self.error(document.path, "current_tasks must be a YAML flow list")

        integration_values = {
            "integration_worktree": document.frontmatter.get("integration_worktree"),
            "integration_branch": document.frontmatter.get("integration_branch"),
            "integration_head_commit": document.frontmatter.get("integration_head_commit"),
            "integration_uncommitted_changes": document.frontmatter.get(
                "integration_uncommitted_changes"
            ),
        }
        if any(value is not None for value in integration_values.values()):
            if integration_values["integration_worktree"] is None:
                self.error(document.path, "an integration checkout must record its worktree")
            if not isinstance(integration_values["integration_branch"], str) or not integration_values[
                "integration_branch"
            ]:
                self.error(document.path, "an integration checkout must record its branch")
            if integration_values["integration_head_commit"] is None:
                self.error(document.path, "an integration checkout must record its head commit")
            if not isinstance(integration_values["integration_uncommitted_changes"], bool):
                self.error(
                    document.path,
                    "an integration checkout must record uncommitted changes as true or false",
                )

    def validate_task_definition(
        self, document: MarkdownDocument, plan_id: str, task_id: str
    ) -> None:
        required = {
            "id",
            "plan",
            "title",
            "created",
            "updated",
            "depends_on",
            "planned_worktree",
            "planned_branch",
            "review_required",
        }
        self.require_keys(document, required)
        self.require_sections(document, TASK_SECTIONS)
        self.validate_date(document, "created")
        self.validate_timestamp(document)
        self.validate_worktree(document, allow_null=False, key="planned_worktree")
        if document.frontmatter.get("id") != task_id:
            self.error(document.path, f"id must match task folder name {task_id!r}")
        if document.frontmatter.get("plan") != plan_id:
            self.error(document.path, f"plan must match plan ID {plan_id!r}")
        if not isinstance(document.frontmatter.get("title"), str) or not document.frontmatter.get(
            "title"
        ):
            self.error(document.path, "title must be a non-empty string")
        if not isinstance(document.frontmatter.get("depends_on"), list):
            self.error(document.path, "depends_on must be a YAML flow list")
        if (
            not isinstance(document.frontmatter.get("planned_branch"), str)
            or not document.frontmatter.get("planned_branch")
        ):
            self.error(document.path, "planned_branch must be a non-empty string")
        if document.frontmatter.get("review_required") is not True:
            self.error(document.path, "review_required must be true")

    def validate_task_progress(
        self, document: MarkdownDocument, task_id: str
    ) -> None:
        required = {
            "task",
            "status",
            "updated",
            "worktree",
            "branch",
            "head_commit",
            "integrated_commit",
            "uncommitted_changes",
            "latest_handoff",
            "latest_review",
        }
        self.require_keys(document, required)
        self.require_sections(document, TASK_PROGRESS_SECTIONS)
        self.validate_status(document, TASK_STATUSES)
        self.validate_timestamp(document)
        self.validate_worktree(document, allow_null=True)
        self.validate_commit(document, "head_commit")
        self.validate_commit(document, "integrated_commit")
        self.validate_artifact_path(document, "latest_handoff", "plans")
        self.validate_artifact_path(document, "latest_review", "reviews")
        if document.frontmatter.get("task") != task_id:
            self.error(document.path, f"task must match task folder name {task_id!r}")

        status = document.frontmatter.get("status")
        worktree = document.frontmatter.get("worktree")
        branch = document.frontmatter.get("branch")
        head_commit = document.frontmatter.get("head_commit")
        uncommitted = document.frontmatter.get("uncommitted_changes")
        if status != "not-started":
            if worktree is None:
                self.error(document.path, "started tasks must record a worktree")
            if not isinstance(branch, str) or not branch:
                self.error(document.path, "started tasks must record a branch")
            if head_commit is None:
                self.error(document.path, "started tasks must record a head_commit")
            if not isinstance(uncommitted, bool):
                self.error(
                    document.path,
                    "started tasks must record uncommitted_changes as true or false",
                )
        elif branch is not None and (not isinstance(branch, str) or not branch):
            self.error(document.path, "branch must be a non-empty string or null")
        if uncommitted is not None and not isinstance(uncommitted, bool):
            self.error(document.path, "uncommitted_changes must be true, false, or null")
        integrated_commit = document.frontmatter.get("integrated_commit")
        if status == "completed" and integrated_commit is None:
            self.error(document.path, "a completed task must record its integrated_commit")
        elif status != "completed" and integrated_commit is not None:
            self.error(document.path, "an incomplete task must set integrated_commit to null")

    def validate_related_paths(
        self, document: MarkdownDocument
    ) -> dict[str, tuple[str, set[str]]]:
        table = self.parse_table(
            document,
            "Related Files and Folders",
            RELATED_PATH_HEADERS,
        )
        if table is None:
            return {}

        paths: dict[str, tuple[str, set[str]]] = {}
        for row in table.rows:
            path = self.plain_cell(row[0]).rstrip("/")
            state = self.plain_cell(row[1])
            expected_uses = {
                value.strip()
                for value in self.plain_cell(row[2]).split(",")
                if value.strip()
            }
            relevance = self.plain_cell(row[3])
            evidence = self.plain_cell(row[4])

            raw_parts = path.split("/")
            if (
                not path
                or "\\" in path
                or PurePosixPath(path).is_absolute()
                or any(part in {"", ".", ".."} for part in raw_parts)
            ):
                self.error(
                    document.path,
                    f"related path must be a normalized repository-relative path: {path!r}",
                )
            if path in paths:
                self.error(document.path, f"duplicate related path {path!r}")
            if state not in PATH_STATES:
                self.error(
                    document.path,
                    f"related path {path!r} has invalid State {state!r}",
                )
            if not expected_uses or not expected_uses <= EXPECTED_USES:
                self.error(
                    document.path,
                    f"related path {path!r} has invalid Expected Use {self.plain_cell(row[2])!r}",
                )
            if not relevance or relevance.lower() in NONE_VALUES:
                self.error(document.path, f"related path {path!r} needs concrete relevance")
            if not evidence or evidence.lower() in NONE_VALUES:
                self.error(document.path, f"related path {path!r} needs concrete evidence")
            paths[path] = (state, expected_uses)
        return paths

    def validate_documentation_references(
        self, document: MarkdownDocument
    ) -> dict[tuple[str, str], tuple[str, set[str]]]:
        table = self.parse_table(
            document,
            "Relevant Documentation and Guides",
            DOCUMENTATION_HEADERS,
        )
        if table is None:
            return {}

        references: dict[tuple[str, str], tuple[str, set[str]]] = {}
        for row in table.rows:
            path = self.plain_cell(row[0]).rstrip("/")
            source = self.plain_cell(row[1])
            state = self.plain_cell(row[2])
            expected_uses = {
                value.strip()
                for value in self.plain_cell(row[3]).split(",")
                if value.strip()
            }
            relevance = self.plain_cell(row[4])
            evidence = self.plain_cell(row[5])
            key = (source, path)

            raw_parts = path.split("/")
            normalized = (
                bool(path)
                and "\\" not in path
                and not PurePosixPath(path).is_absolute()
                and all(part not in {"", ".", ".."} for part in raw_parts)
            )
            if not normalized:
                self.error(
                    document.path,
                    f"documentation path must be normalized and relative: {path!r}",
                )
            if key in references:
                self.error(
                    document.path,
                    f"duplicate documentation reference {source!r} {path!r}",
                )
            if source not in DOCUMENTATION_SOURCES:
                self.error(
                    document.path,
                    f"documentation reference {path!r} has invalid Source {source!r}",
                )
            if state not in PATH_STATES:
                self.error(
                    document.path,
                    f"documentation reference {path!r} has invalid State {state!r}",
                )
            if not expected_uses or not expected_uses <= EXPECTED_USES:
                self.error(
                    document.path,
                    f"documentation reference {path!r} has invalid Expected Use "
                    f"{self.plain_cell(row[3])!r}",
                )

            if source == "project-docs":
                if normalized and (len(raw_parts) < 2 or raw_parts[0] != "docs"):
                    self.error(
                        document.path,
                        f"project-docs path must be below docs/: {path!r}",
                    )
                if (
                    document.path.name == "PLAN.md"
                    and state == "planned"
                    and "create" not in expected_uses
                ):
                    self.error(
                        document.path,
                        f"planned project-docs reference must include create: {path!r}",
                    )
                if state == "existing" and "create" in expected_uses:
                    self.error(
                        document.path,
                        f"existing project-docs reference cannot use create: {path!r}",
                    )
            elif source == "workspace-guide":
                if normalized and (
                    len(raw_parts) < 3 or raw_parts[:2] != [".agents", "guides"]
                ):
                    self.error(
                        document.path,
                        f"workspace-guide path must be below .agents/guides/: {path!r}",
                    )
                if state != "existing":
                    self.error(
                        document.path,
                        f"workspace-guide reference must be existing: {path!r}",
                    )
                if expected_uses != {"inspect"}:
                    self.error(
                        document.path,
                        f"workspace-guide reference must be inspect-only: {path!r}",
                    )

            if not relevance or relevance.lower() in NONE_VALUES:
                self.error(
                    document.path,
                    f"documentation reference {path!r} needs concrete relevance",
                )
            if not evidence or evidence.lower() in NONE_VALUES:
                self.error(
                    document.path,
                    f"documentation reference {path!r} needs concrete evidence",
                )
            references[key] = (state, expected_uses)
        return references

    @staticmethod
    def dependency_cell(value: str) -> list[str]:
        normalized = value.replace("`", "").strip()
        if normalized.lower() in NONE_VALUES:
            return []
        return [item.strip() for item in normalized.split(",") if item.strip()]

    def validate_architecture_decisions(self, plan: MarkdownDocument) -> None:
        table = self.parse_table(
            plan,
            "Architecture Decisions",
            ARCHITECTURE_HEADERS,
        )
        if table is None:
            return
        if not table.rows:
            self.error(plan.path, "Architecture Decisions must record a decision or no-ADR rationale")
            return

        for row in table.rows:
            decision = self.plain_cell(row[0])
            required = self.plain_cell(row[1]).lower()
            path = self.plain_cell(row[2])
            rationale = self.plain_cell(row[3])
            if not decision or decision.lower() in NONE_VALUES:
                self.error(plan.path, "Architecture Decisions row needs a decision")
            if required not in {"yes", "no"}:
                self.error(plan.path, "ADR Required must be yes or no")
            if not rationale or rationale.lower() in NONE_VALUES:
                self.error(plan.path, "Architecture Decisions row needs a rationale")

            if required == "yes":
                parts = path.split("/")
                normalized = (
                    "\\" not in path
                    and len(parts) >= 3
                    and parts[:2] == ["docs", "adrs"]
                    and all(part not in {"", ".", ".."} for part in parts)
                    and not PurePosixPath(path).is_absolute()
                    and path.endswith(".md")
                )
                if not normalized:
                    self.error(
                        plan.path,
                        "an ADR-required decision needs a Markdown path below docs/adrs/",
                    )
            elif required == "no" and path.lower() not in NONE_VALUES:
                self.error(plan.path, "a no-ADR decision must use None for Path")

    def validate_planned_assignments(
        self,
        plan: MarkdownDocument,
        definitions: dict[str, MarkdownDocument],
    ) -> None:
        for field in ("planned_worktree", "planned_branch"):
            assignments: dict[str, list[str]] = {}
            for task_id, document in definitions.items():
                value = document.frontmatter.get(field)
                if isinstance(value, str) and value:
                    assignments.setdefault(value, []).append(task_id)
            for value, task_ids in assignments.items():
                if len(task_ids) > 1:
                    self.error(
                        definitions[task_ids[0]].path,
                        f"tasks {', '.join(sorted(task_ids))} share {field} {value!r}",
                    )

        for plan_field, task_field in (
            ("planned_integration_worktree", "planned_worktree"),
            ("planned_integration_branch", "planned_branch"),
        ):
            plan_value = plan.frontmatter.get(plan_field)
            conflicts = [
                task_id
                for task_id, document in definitions.items()
                if document.frontmatter.get(task_field) == plan_value
            ]
            if conflicts:
                self.error(
                    plan.path,
                    f"{plan_field} {plan_value!r} is shared with tasks "
                    f"{', '.join(sorted(conflicts))}",
                )

    def validate_plan_tasks_table(
        self,
        plan: MarkdownDocument,
        definitions: dict[str, MarkdownDocument],
        task_ids: set[str],
    ) -> None:
        table = self.parse_table(plan, "Tasks", PLAN_TASK_HEADERS)
        if table is None:
            return

        recorded: dict[str, list[str]] = {}
        for row in table.rows:
            task_id = self.plain_cell(row[0])
            if task_id in recorded:
                self.error(plan.path, f"duplicate Tasks row for {task_id!r}")
            recorded_dependencies = self.dependency_cell(row[2])
            if len(recorded_dependencies) != len(set(recorded_dependencies)):
                self.error(plan.path, f"Tasks row for {task_id!r} repeats a dependency")
            recorded[task_id] = recorded_dependencies

            link = re.fullmatch(r"\[([^]]+)\]\(([^)]+)\)", row[1].strip())
            expected_target = f"tasks/{task_id}/TASK.md"
            if link is None or link.group(2) != expected_target:
                self.error(
                    plan.path,
                    f"Tasks row for {task_id!r} must link to {expected_target!r}",
                )

        for task_id in sorted(task_ids - recorded.keys()):
            self.error(plan.path, f"Tasks table is missing {task_id!r}")
        for task_id in sorted(recorded.keys() - task_ids):
            self.error(plan.path, f"Tasks table contains unknown task {task_id!r}")
        for task_id in sorted(recorded.keys() & definitions.keys()):
            defined = definitions[task_id].frontmatter.get("depends_on")
            defined_ids = (
                [dependency for dependency in defined if isinstance(dependency, str)]
                if isinstance(defined, list)
                else []
            )
            if isinstance(defined, list) and set(recorded[task_id]) != set(defined_ids):
                self.error(
                    plan.path,
                    f"Tasks row for {task_id!r} has dependencies {recorded[task_id]!r}, "
                    f"but TASK.md has {defined!r}",
                )

    def task_status_table(self, document: MarkdownDocument) -> dict[str, str]:
        table = self.parse_table(document, "Task Status", TASK_STATUS_HEADERS)
        if table is None:
            return {}

        statuses: dict[str, str] = {}
        for row in table.rows:
            task_id = self.plain_cell(row[0])
            status = self.plain_cell(row[1])
            result = self.plain_cell(row[2])
            if task_id in statuses:
                self.error(document.path, f"duplicate Task Status row for {task_id!r}")
            if not result or result.lower() in NONE_VALUES:
                self.error(
                    document.path,
                    f"Task Status row for {task_id!r} needs a result or blocker summary",
                )
            statuses[task_id] = status
        return statuses

    def validate_dependencies(
        self,
        definitions: dict[str, MarkdownDocument],
        task_ids: set[str],
    ) -> None:
        graph: dict[str, list[str]] = {}
        for task_id, document in definitions.items():
            dependencies = document.frontmatter.get("depends_on")
            if not isinstance(dependencies, list):
                graph[task_id] = []
                continue
            normalized: list[str] = []
            for dependency in dependencies:
                if not isinstance(dependency, str):
                    self.error(document.path, "every depends_on value must be a task ID")
                    continue
                if dependency in normalized:
                    self.error(document.path, f"duplicate dependency task ID {dependency!r}")
                normalized.append(dependency)
                if dependency == task_id:
                    self.error(document.path, "a task cannot depend on itself")
                elif dependency not in task_ids:
                    self.error(document.path, f"unknown dependency task ID {dependency!r}")
            graph[task_id] = normalized

        state: dict[str, int] = {}

        def visit(task_id: str, trail: list[str]) -> None:
            current_state = state.get(task_id, 0)
            if current_state == 1:
                cycle_start = trail.index(task_id) if task_id in trail else 0
                cycle = trail[cycle_start:] + [task_id]
                self.error(
                    definitions[task_id].path,
                    f"cyclic dependency: {' -> '.join(cycle)}",
                )
                return
            if current_state == 2:
                return
            state[task_id] = 1
            for dependency in graph.get(task_id, []):
                if dependency in graph:
                    visit(dependency, trail + [task_id])
            state[task_id] = 2

        for task_id in sorted(task_ids):
            visit(task_id, [])

    def validate_status_consistency(
        self,
        plan: MarkdownDocument,
        plan_progress: MarkdownDocument,
        definitions: dict[str, MarkdownDocument],
        task_progress: dict[str, MarkdownDocument],
    ) -> None:
        actual_statuses = {
            task_id: document.frontmatter.get("status")
            for task_id, document in task_progress.items()
        }
        summary_statuses = self.task_status_table(plan_progress)

        for task_id in sorted(actual_statuses.keys() - summary_statuses.keys()):
            self.error(plan_progress.path, f"Task Status table is missing {task_id!r}")
        for task_id in sorted(summary_statuses.keys() - actual_statuses.keys()):
            self.error(plan_progress.path, f"Task Status table contains unknown task {task_id!r}")
        for task_id in sorted(actual_statuses.keys() & summary_statuses.keys()):
            summary_status = summary_statuses[task_id]
            if summary_status not in TASK_STATUSES:
                self.error(
                    plan_progress.path,
                    f"Task Status row for {task_id!r} has invalid status {summary_status!r}",
                )
            elif summary_status != actual_statuses[task_id]:
                self.error(
                    plan_progress.path,
                    f"Task Status row for {task_id!r} is {summary_status!r}, "
                    f"but task progress is {actual_statuses[task_id]!r}",
                )

        current_tasks = plan_progress.frontmatter.get("current_tasks")
        if isinstance(current_tasks, list):
            non_string = [item for item in current_tasks if not isinstance(item, str)]
            if non_string:
                self.error(plan_progress.path, "current_tasks values must be task IDs")
            string_values = [item for item in current_tasks if isinstance(item, str)]
            if len(string_values) != len(set(string_values)):
                self.error(plan_progress.path, "current_tasks must not contain duplicates")
            recorded = set(string_values)
            unknown = recorded - actual_statuses.keys()
            for task_id in sorted(unknown):
                self.error(plan_progress.path, f"current_tasks contains unknown task {task_id!r}")
            active = {
                task_id
                for task_id, status in actual_statuses.items()
                if status == "in-progress"
            }
            if recorded != active:
                self.error(
                    plan_progress.path,
                    "current_tasks must exactly match tasks with status in-progress",
                )

        plan_status = plan_progress.frontmatter.get("status")
        statuses = list(actual_statuses.values())
        for planned_key, actual_key in (
            ("planned_integration_worktree", "integration_worktree"),
            ("planned_integration_branch", "integration_branch"),
        ):
            planned_value = plan.frontmatter.get(planned_key)
            actual_value = plan_progress.frontmatter.get(actual_key)
            if actual_value is not None and actual_value != planned_value:
                self.error(
                    plan_progress.path,
                    f"{actual_key} must match {planned_key} {planned_value!r}",
                )

        integration_assignment_recorded = (
            isinstance(plan_progress.frontmatter.get("integration_worktree"), str)
            and isinstance(plan_progress.frontmatter.get("integration_branch"), str)
            and isinstance(plan_progress.frontmatter.get("integration_head_commit"), str)
            and isinstance(
                plan_progress.frontmatter.get("integration_uncommitted_changes"),
                bool,
            )
        )
        if (
            any(status != "not-started" for status in statuses)
            and not integration_assignment_recorded
        ):
            self.error(
                plan_progress.path,
                "started task work requires a recorded plan integration checkout",
            )

        dependencies: dict[str, list[str]] = {}
        for task_id, definition in definitions.items():
            values = definition.frontmatter.get("depends_on")
            dependencies[task_id] = (
                [value for value in values if isinstance(value, str)]
                if isinstance(values, list)
                else []
            )

        for task_id, status in actual_statuses.items():
            if status == "not-started":
                continue
            incomplete = [
                dependency
                for dependency in dependencies.get(task_id, [])
                if actual_statuses.get(dependency) != "completed"
            ]
            if incomplete:
                self.error(
                    task_progress[task_id].path,
                    f"{status} task has incomplete dependencies: {', '.join(incomplete)}",
                )

        actionable = {
            task_id
            for task_id, status in actual_statuses.items()
            if status == "not-started"
            and all(
                actual_statuses.get(dependency) == "completed"
                for dependency in dependencies.get(task_id, [])
            )
        }
        active = {
            task_id
            for task_id, status in actual_statuses.items()
            if status == "in-progress"
        }
        review_and_integration_work = {
            task_id
            for task_id, status in actual_statuses.items()
            if status in {"ready-for-review", "ready-for-integration", "needs-fix"}
        }
        all_tasks_completed = bool(statuses) and all(
            status == "completed" for status in statuses
        )
        criteria = self.checklist_states(plan, "Completion Criteria")
        criteria_completed = bool(criteria) and all(criteria)
        integration_validation = self.labeled_list_value(
            plan_progress,
            "Integration",
            "Validation",
        ).lower()
        integration_validation_recorded = bool(integration_validation) and (
            integration_validation not in NONE_VALUES | {"not run", "not run."}
        )
        integration_review_current = self.plan_integration_review_is_current(
            plan.frontmatter.get("id", ""),
            plan_progress,
            report_errors=False,
        )
        integration_state_complete = (
            integration_assignment_recorded
            and plan_progress.frontmatter.get("integration_uncommitted_changes") is False
        )
        completed_integration_commits = {
            document.frontmatter.get("integrated_commit")
            for task_id, document in task_progress.items()
            if actual_statuses.get(task_id) == "completed"
            and isinstance(document.frontmatter.get("integrated_commit"), str)
        }
        if (
            completed_integration_commits
            and plan_progress.frontmatter.get("integration_head_commit")
            not in completed_integration_commits
        ):
            self.error(
                plan_progress.path,
                "integration_head_commit must match a completed task integration",
            )
        completion_ready = (
            all_tasks_completed
            and criteria_completed
            and integration_state_complete
            and integration_validation_recorded
            and integration_review_current
        )
        plan_has_blockers = self.has_meaningful_content(
            self.section_body(plan_progress, "Blockers")
        )

        if completion_ready:
            expected_status = "completed"
        elif all_tasks_completed:
            expected_status = "in-progress"
        elif statuses and all(status == "not-started" for status in statuses):
            expected_status = "not-started"
        elif active or actionable or review_and_integration_work:
            expected_status = "in-progress"
        else:
            expected_status = "blocked"

        if plan_status != expected_status:
            if all_tasks_completed and not criteria_completed:
                message = (
                    "all tasks are completed but unchecked plan completion criteria "
                    "require status in-progress"
                )
            elif all_tasks_completed and not integration_state_complete:
                message = (
                    "all tasks and plan completion criteria are complete but the plan "
                    "integration state is not complete"
                )
            elif all_tasks_completed and not integration_validation_recorded:
                message = (
                    "all tasks and plan completion criteria are complete but combined "
                    "integration validation is not recorded"
                )
            elif all_tasks_completed and not integration_review_current:
                message = (
                    "all tasks and plan completion criteria are complete but a clean "
                    "review of the current integration head is still required"
                )
            else:
                message = f"plan status must be {expected_status!r} for the current task state"
            self.error(plan_progress.path, message)

        if plan_status == "completed":
            if not integration_validation_recorded:
                self.error(
                    plan_progress.path,
                    "a completed plan must record combined integration validation",
                )
            self.plan_integration_review_is_current(
                plan.frontmatter.get("id", ""),
                plan_progress,
                report_errors=True,
            )

        if plan_status == "blocked" and not plan_has_blockers:
            self.error(plan_progress.path, "a blocked plan must record an unresolved blocker")
        if plan_status == "completed" and plan_has_blockers:
            self.error(plan_progress.path, "a completed plan cannot have unresolved blockers")

        blocked_tasks = {
            task_id
            for task_id, status in actual_statuses.items()
            if status == "blocked"
        }
        if blocked_tasks and not plan_has_blockers:
            self.error(
                plan_progress.path,
                "plan Blockers must summarize blockers from blocked tasks",
            )

        expected_actions = set(
            active | actionable | review_and_integration_work | blocked_tasks
        )
        if all_tasks_completed and not completion_ready:
            expected_actions = {"plan"}
        if plan_status == "completed":
            expected_actions = set()
        self.validate_next_actions(
            plan_progress,
            actual_statuses.keys(),
            expected_actions,
        )
        self.validate_parallel_assignments(plan_progress, task_progress)

    def validate_next_actions(
        self,
        plan_progress: MarkdownDocument,
        task_ids: Iterable[str],
        expected_actions: set[str],
    ) -> None:
        table = self.parse_table(plan_progress, "Next Actions", NEXT_ACTION_HEADERS)
        if table is None:
            return

        known = set(task_ids)
        recorded: set[str] = set()
        for row in table.rows:
            task_id = self.plain_cell(row[0])
            action = self.plain_cell(row[1])
            if task_id in recorded:
                self.error(plan_progress.path, f"duplicate Next Actions row for {task_id!r}")
            recorded.add(task_id)
            if task_id != "plan" and task_id not in known:
                self.error(
                    plan_progress.path,
                    f"Next Actions contains unknown task {task_id!r}",
                )
            if not action or action.lower() in NONE_VALUES:
                self.error(
                    plan_progress.path,
                    f"Next Actions row for {task_id!r} needs an exact action",
                )

        if recorded != expected_actions:
            self.error(
                plan_progress.path,
                f"Next Actions must exactly list available actions: {sorted(expected_actions)!r}",
            )

    def validate_parallel_assignments(
        self,
        plan_progress: MarkdownDocument,
        task_progress: dict[str, MarkdownDocument],
    ) -> None:
        active = {
            task_id: document
            for task_id, document in task_progress.items()
            if document.frontmatter.get("status") == "in-progress"
        }
        for field in ("worktree", "branch"):
            assignments: dict[str, list[str]] = {}
            for task_id, document in active.items():
                value = document.frontmatter.get(field)
                if isinstance(value, str):
                    assignments.setdefault(value, []).append(task_id)
            for value, task_ids in assignments.items():
                if len(task_ids) > 1:
                    self.error(
                        plan_progress.path,
                        f"parallel tasks {', '.join(sorted(task_ids))} share {field} {value!r}",
                    )

        for integration_field, task_field in (
            ("integration_worktree", "worktree"),
            ("integration_branch", "branch"),
        ):
            integration_value = plan_progress.frontmatter.get(integration_field)
            conflicts = [
                task_id
                for task_id, document in active.items()
                if document.frontmatter.get(task_field) == integration_value
            ]
            if integration_value is not None and conflicts:
                self.error(
                    plan_progress.path,
                    f"{integration_field} {integration_value!r} is shared with active tasks "
                    f"{', '.join(sorted(conflicts))}",
                )

    def validate_task_completion(
        self,
        definition: MarkdownDocument,
        progress: MarkdownDocument,
    ) -> None:
        status = progress.frontmatter.get("status")
        criteria = self.checklist_states(definition, "Acceptance Criteria")
        blockers = self.has_meaningful_content(self.section_body(progress, "Blockers"))
        next_action = self.has_meaningful_content(
            self.section_body(progress, "Next Action")
        )
        validation = self.meaningful_text(self.section_body(progress, "Validation"))
        validation_recorded = bool(validation) and validation.lower() not in (
            NONE_VALUES | {"not run", "not run."}
        )
        latest_handoff = progress.frontmatter.get("latest_handoff")
        latest_review = progress.frontmatter.get("latest_review")

        if status == "blocked" and not blockers:
            self.error(progress.path, "a blocked task must record an unresolved blocker")
        if status == "ready-for-review":
            if not validation_recorded:
                self.error(
                    progress.path,
                    "a ready-for-review task must record implementation validation",
                )
            if not isinstance(latest_handoff, str):
                self.error(
                    progress.path,
                    "a ready-for-review task must record latest_handoff",
                )
        if status == "ready-for-integration":
            if criteria and not all(criteria):
                self.error(
                    progress.path,
                    "a ready-for-integration task requires every acceptance criterion checked",
                )
            if blockers:
                self.error(
                    progress.path,
                    "a ready-for-integration task cannot have unresolved blockers",
                )
            if not validation_recorded:
                self.error(
                    progress.path,
                    "a ready-for-integration task must record implementation validation",
                )
            if not isinstance(latest_handoff, str):
                self.error(
                    progress.path,
                    "a ready-for-integration task must record latest_handoff",
                )
            if not isinstance(latest_review, str):
                self.error(
                    progress.path,
                    "a ready-for-integration task must record the clean latest_review",
                )
            else:
                self.validate_task_final_review(definition, progress, "clean")
        if status == "needs-fix":
            if not isinstance(latest_handoff, str):
                self.error(progress.path, "a needs-fix task must record latest_handoff")
            if not isinstance(latest_review, str):
                self.error(progress.path, "a needs-fix task must record latest_review")
            else:
                self.validate_task_final_review(
                    definition,
                    progress,
                    "actionable-findings",
                )
        if status == "completed":
            if criteria and not all(criteria):
                self.error(
                    progress.path,
                    "a completed task requires every acceptance criterion checked",
                )
            if blockers:
                self.error(progress.path, "a completed task cannot have unresolved blockers")
            if next_action:
                self.error(progress.path, "a completed task must set Next Action to None.")
            if not validation_recorded:
                self.error(
                    progress.path,
                    "a completed task must record validation or an accepted exception",
                )
            if not isinstance(latest_review, str):
                self.error(
                    progress.path,
                    "a completed task must record the clean latest_review",
                )
            else:
                self.validate_task_final_review(definition, progress, "clean")
        elif not next_action:
            self.error(progress.path, "an incomplete task must record one exact next action")

    def run(self) -> list[str]:
        if not self.plan_dir.is_dir():
            self.error(self.plan_dir, "plan path is not a directory")
            return self.errors

        readmes = list(self.plan_dir.rglob("README.md"))
        for readme in readmes:
            self.error(readme, "README.md files are not part of the plan structure")

        plan_id = self.plan_dir.name
        handoffs_dir = self.plan_dir / "handoffs"
        if not handoffs_dir.is_dir():
            self.error(handoffs_dir, "required directory is missing")
        plan = self.read_document(self.plan_dir / "PLAN.md")
        plan_progress = self.read_document(self.plan_dir / "PROGRESS.md")
        plan_related: dict[str, tuple[str, set[str]]] = {}
        plan_documentation: dict[tuple[str, str], tuple[str, set[str]]] = {}
        if plan is not None:
            self.validate_plan_definition(plan, plan_id)
            self.validate_architecture_decisions(plan)
            plan_related = self.validate_related_paths(plan)
            plan_documentation = self.validate_documentation_references(plan)
        if plan_progress is not None:
            self.validate_plan_progress(plan_progress, plan_id)

        tasks_dir = self.plan_dir / "tasks"
        if not tasks_dir.is_dir():
            self.error(tasks_dir, "required directory is missing")
            return self.errors

        task_dirs = sorted(path for path in tasks_dir.iterdir() if path.is_dir())
        if not task_dirs:
            self.error(tasks_dir, "a plan must contain at least one task directory")

        definitions: dict[str, MarkdownDocument] = {}
        progress_documents: dict[str, MarkdownDocument] = {}
        task_related: dict[str, dict[str, tuple[str, set[str]]]] = {}
        task_documentation: dict[
            str,
            dict[tuple[str, str], tuple[str, set[str]]],
        ] = {}
        for task_dir in task_dirs:
            task_id = task_dir.name
            if not TASK_ID_PATTERN.fullmatch(task_id):
                self.error(
                    task_dir,
                    "task folder must start with a three-digit sequence and hyphen",
                )
            task_handoffs = task_dir / "handoffs"
            if not task_handoffs.is_dir():
                self.error(task_handoffs, "required directory is missing")
            definition = self.read_document(task_dir / "TASK.md")
            progress = self.read_document(task_dir / "PROGRESS.md")
            if definition is not None:
                definitions[task_id] = definition
                self.validate_task_definition(definition, plan_id, task_id)
                task_related[task_id] = self.validate_related_paths(definition)
                task_documentation[task_id] = self.validate_documentation_references(
                    definition
                )
            if progress is not None:
                progress_documents[task_id] = progress
                self.validate_task_progress(progress, task_id)
            if definition is not None and progress is not None:
                self.validate_task_completion(definition, progress)

        task_ids = {task_dir.name for task_dir in task_dirs}
        if plan is not None:
            self.validate_plan_tasks_table(plan, definitions, task_ids)
            for task_id, related in task_related.items():
                for path in sorted(related.keys() - plan_related.keys()):
                    self.error(
                        definitions[task_id].path,
                        f"related path {path!r} is missing from the plan related-path table",
                    )
                for path in sorted(related.keys() & plan_related.keys()):
                    task_state, task_uses = related[path]
                    plan_state, plan_uses = plan_related[path]
                    if task_state != plan_state:
                        self.error(
                            definitions[task_id].path,
                            f"related path {path!r} has State {task_state!r}, "
                            f"but the plan uses {plan_state!r}",
                        )
                    if not task_uses <= plan_uses:
                        self.error(
                            definitions[task_id].path,
                            f"related path {path!r} uses {sorted(task_uses)!r}, "
                            f"which is not a subset of plan uses {sorted(plan_uses)!r}",
                        )
            for task_id, references in task_documentation.items():
                for key in sorted(references.keys() - plan_documentation.keys()):
                    source, path = key
                    self.error(
                        definitions[task_id].path,
                        f"documentation reference {source!r} {path!r} is missing "
                        "from the plan table",
                    )
                for key in sorted(references.keys() & plan_documentation.keys()):
                    source, path = key
                    task_state, task_uses = references[key]
                    plan_state, plan_uses = plan_documentation[key]
                    if task_state != plan_state:
                        self.error(
                            definitions[task_id].path,
                            f"documentation reference {source!r} {path!r} has State "
                            f"{task_state!r}, but the plan uses {plan_state!r}",
                        )
                    if not task_uses <= plan_uses:
                        self.error(
                            definitions[task_id].path,
                            f"documentation reference {source!r} {path!r} uses "
                            f"{sorted(task_uses)!r}, which is not a subset of plan "
                            f"uses {sorted(plan_uses)!r}",
                        )
        self.validate_dependencies(definitions, task_ids)
        if plan is not None:
            self.validate_planned_assignments(plan, definitions)
        if plan is not None and plan_progress is not None:
            self.validate_status_consistency(
                plan,
                plan_progress,
                definitions,
                progress_documents,
            )

        return self.errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the structure and synchronized state of one plan directory."
    )
    parser.add_argument("plan", type=Path, help="Path to an active or completed plan folder")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan_dir = args.plan.expanduser().resolve()
    errors = PlanValidator(plan_dir).run()
    if errors:
        print(f"Plan validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Plan validation passed: {plan_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
