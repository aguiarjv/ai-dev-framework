#!/usr/bin/env python3
"""Validation for the structured artifacts exchanged by workflow agents."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
WORKFLOW_PHASES = [
    "intake",
    "exploration",
    "specification",
    "approval",
    "planning",
    "implementation",
    "verification",
    "review",
    "remediation",
    "done",
]


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate_document(document: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None and not matches_type(document, expected_type):
        return [f"{path}: expected {expected_type}, got {type(document).__name__}"]

    if "enum" in schema and document not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}, got {document!r}")

    if isinstance(document, str):
        if len(document) < schema.get("minLength", 0):
            errors.append(f"{path}: must contain at least {schema['minLength']} characters")
        pattern = schema.get("pattern")
        if pattern and not re.match(pattern, document):
            errors.append(f"{path}: does not match {pattern!r}")

    if isinstance(document, (int, float)) and not isinstance(document, bool):
        if "minimum" in schema and document < schema["minimum"]:
            errors.append(f"{path}: must be >= {schema['minimum']}")
        if "maximum" in schema and document > schema["maximum"]:
            errors.append(f"{path}: must be <= {schema['maximum']}")

    if isinstance(document, list):
        if len(document) < schema.get("minItems", 0):
            errors.append(f"{path}: must contain at least {schema['minItems']} items")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(document):
                errors.extend(validate_document(item, item_schema, f"{path}[{index}]"))

    if isinstance(document, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in document:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in document:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key!r}")
        for key, value in document.items():
            if key in properties:
                errors.extend(validate_document(value, properties[key], f"{path}.{key}"))

    return errors


def matches_type(value: Any, expected: str | list[str]) -> bool:
    expected_values = [expected] if isinstance(expected, str) else expected
    return any(
        {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }.get(item, False)
        for item in expected_values
    )


def validate_contract(document: dict[str, Any], schema_name: str) -> list[str]:
    errors = validate_document(document, load_schema(schema_name))
    if schema_name == "task-contract.schema.json" and not errors:
        errors.extend(validate_task_graph(document))
    return errors


def validate_task_graph(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    criteria = {item["id"] for item in document["acceptance_criteria"]}
    subtasks = document["subtasks"]
    subtask_ids = [item["id"] for item in subtasks]
    if len(subtask_ids) != len(set(subtask_ids)):
        errors.append("$.subtasks: task IDs must be unique")

    known_tasks = set(subtask_ids)
    covered_criteria = {
        criterion
        for subtask in subtasks
        for criterion in subtask["acceptance_criteria"]
    }
    for criterion in sorted(criteria - covered_criteria):
        errors.append(f"$.acceptance_criteria: criterion {criterion!r} is not assigned to a subtask")
    for subtask in subtasks:
        for dependency in subtask["depends_on"]:
            if dependency not in known_tasks:
                errors.append(f"$.subtasks[{subtask['id']}].depends_on: unknown task {dependency!r}")
        for criterion in subtask["acceptance_criteria"]:
            if criterion not in criteria:
                errors.append(f"$.subtasks[{subtask['id']}].acceptance_criteria: unknown criterion {criterion!r}")

    graph = {item["id"]: set(item["depends_on"]) for item in subtasks}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            errors.append(f"$.subtasks: dependency cycle includes {task_id!r}")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in graph[task_id]:
            if dependency in graph:
                visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id)
    return errors


def validate_contract_file(path: Path, schema_name: str) -> list[str]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: could not read JSON: {exc}"]
    return [f"{path}: {error}" for error in validate_contract(document, schema_name)]


def validate_state_transition(previous_phase: str, next_phase: str) -> list[str]:
    """Check the workflow transitions that the orchestrator is allowed to make."""
    if next_phase == "blocked":
        return []
    if previous_phase == "blocked":
        return ["blocked workflows require an explicit resume decision before continuing"]
    if previous_phase == "review" and next_phase == "remediation":
        return []
    if previous_phase == "remediation" and next_phase == "review":
        return []
    if previous_phase == next_phase:
        return []
    try:
        previous_index = WORKFLOW_PHASES.index(previous_phase)
        next_index = WORKFLOW_PHASES.index(next_phase)
    except ValueError:
        return [f"unknown workflow phase transition: {previous_phase!r} -> {next_phase!r}"]
    if next_index != previous_index + 1:
        return [f"invalid workflow phase transition: {previous_phase!r} -> {next_phase!r}"]
    return []
