#!/usr/bin/env python3
"""Record minimal Codex lifecycle metrics from project-local hooks.

Only numeric usage from a recognized local transcript record is read. Codex
does not promise a stable transcript format, so unrecognized usage stays unknown.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METRICS_RELATIVE = Path(".agents/metrics/codex-native.jsonl")
MAX_TRANSCRIPT_TAIL = 8 * 1024 * 1024
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
START_EVENTS = {"UserPromptSubmit": "root", "SubagentStart": "subagent"}
STOP_EVENTS = {"Stop": "root", "SubagentStop": "subagent"}


def workspace_root(script_path: Path) -> Path:
    for parent in script_path.resolve().parents:
        if (parent / ".ai-dev-framework.json").is_file():
            return parent
    raise ValueError("No installed AI Dev Framework workspace contains this hook")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def run_id(event: dict[str, Any], kind: str) -> str | None:
    session = event.get("session_id")
    turn = event.get("turn_id")
    agent = event.get("agent_id") if kind == "subagent" else "root"
    if not all(isinstance(value, str) and value for value in (session, turn, agent)):
        return None
    digest = hashlib.sha256(f"{session}\0{turn}\0{agent}".encode()).hexdigest()
    return digest[:24]


def location(root: Path, cwd_value: Any) -> dict[str, str | None]:
    result = {"project": None, "plan": None, "task": None}
    if not isinstance(cwd_value, str):
        return result
    try:
        parts = Path(cwd_value).resolve().relative_to(root.resolve()).parts
    except ValueError:
        return result
    if len(parts) < 2 or parts[0] != "projects":
        return result
    result["project"] = parts[1]
    if len(parts) >= 4 and parts[2] == "worktrees":
        plan_directory = root / "projects" / parts[1] / "plans" / parts[3]
        if (plan_directory / "PLAN.md").is_file():
            result["plan"] = parts[3]
            if len(parts) >= 5 and parts[4] != "plan-integration":
                if (plan_directory / "tasks" / parts[4] / "TASK.md").is_file():
                    result["task"] = parts[4]
    return result


def token_usage(value: Any) -> dict[str, int | None] | None:
    if not isinstance(value, dict):
        return None
    required = ("input_tokens", "output_tokens")
    if any(type(value.get(key)) is not int or value[key] < 0 for key in required):
        return None
    result: dict[str, int | None] = {}
    for key in TOKEN_FIELDS:
        item = value.get(key)
        result[key] = item if type(item) is int and item >= 0 else None
    cached = result["cached_input_tokens"]
    if cached is not None and cached > result["input_tokens"]:
        result["cached_input_tokens"] = None
    return result


def transcript_usage(path_value: Any, kind: str, turn_id: str) -> dict[str, int | None] | None:
    if not isinstance(path_value, str):
        return None
    path = Path(path_value)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        return None
    latest = None
    with path.open("rb") as stream:
        size = stream.seek(0, os.SEEK_END)
        offset = max(0, size - MAX_TRANSCRIPT_TAIL)
        stream.seek(offset)
        if offset:
            stream.readline()  # Discard a possibly partial first line.
        for raw_line in stream:
            if b'"token_usage_record"' not in raw_line:
                continue
            try:
                event = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(event, dict) or event.get("type") != "token_usage_record":
                continue
            payload = event.get("payload")
            if not isinstance(payload, dict):
                continue
            if kind == "root" and payload.get("turn_id") != turn_id:
                continue
            field = "thread_token_usage" if kind == "subagent" else "turn_token_usage"
            candidate = token_usage(payload.get(field))
            if candidate is not None:
                latest = candidate
    return latest


def append_record(root: Path, record: dict[str, Any]) -> None:
    destination = root / METRICS_RELATIVE
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    line = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, line)
    finally:
        os.close(descriptor)


def record_hook(root: Path, event: dict[str, Any], timestamp: str | None = None) -> bool:
    name = event.get("hook_event_name")
    kind = START_EVENTS.get(name) or STOP_EVENTS.get(name)
    if kind is None:
        return False
    identifier = run_id(event, kind)
    if identifier is None:
        return False
    phase = "start" if name in START_EVENTS else "stop"
    record: dict[str, Any] = {
        "schema_version": 1,
        "run_id": identifier,
        "event": phase,
        "kind": kind,
        "role": event.get("agent_type") if kind == "subagent" else "orchestrator",
        "model": event.get("model") if isinstance(event.get("model"), str) else None,
        "recorded_at": timestamp or utc_now(),
        **location(root, event.get("cwd")),
    }
    if phase == "stop":
        transcript = event.get("agent_transcript_path") if kind == "subagent" else event.get("transcript_path")
        usage = transcript_usage(transcript, kind, event["turn_id"])
        record["usage_status"] = "observed" if usage is not None else "unavailable"
        record["usage_source"] = "codex-local-token-usage-record" if usage is not None else None
        record["usage"] = usage
    append_record(root, record)
    return True


def summarize(root: Path) -> dict[str, Any]:
    path = root / METRICS_RELATIVE
    if not path.is_file():
        raise ValueError(f"No native metrics recorded at {path}")
    runs: dict[str, dict[str, Any]] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid metrics line {number}: {error}") from error
        if not isinstance(record, dict) or record.get("schema_version") != 1:
            raise ValueError(f"Invalid metrics record at line {number}")
        item = runs.setdefault(record["run_id"], {})
        item[record["event"]] = record
    groups: dict[str, dict[str, int]] = {}
    for item in runs.values():
        stop = item.get("stop")
        start = item.get("start")
        record = stop or start
        role = record["role"] or "unknown"
        group = groups.setdefault(role, {
            "runs": 0, "completed": 0, "elapsed_ms": 0,
            "missing_start": 0, "missing_usage": 0,
            "known_input_tokens": 0, "known_cached_input_tokens": 0,
            "known_output_tokens": 0,
        })
        group["runs"] += 1
        if stop is None:
            continue
        group["completed"] += 1
        if start is None:
            group["missing_start"] += 1
        else:
            try:
                began = datetime.fromisoformat(start["recorded_at"].replace("Z", "+00:00"))
                ended = datetime.fromisoformat(stop["recorded_at"].replace("Z", "+00:00"))
                group["elapsed_ms"] += max(0, int((ended - began).total_seconds() * 1000))
            except (KeyError, TypeError, ValueError):
                group["missing_start"] += 1
        usage = stop.get("usage")
        if stop.get("usage_status") != "observed" or not isinstance(usage, dict):
            group["missing_usage"] += 1
            continue
        for key in ("input_tokens", "cached_input_tokens", "output_tokens"):
            if usage.get(key) is not None:
                group[f"known_{key}"] += usage[key]
    return {"runs": len(runs), "roles": groups}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    try:
        root = args.workspace_root or workspace_root(Path(__file__))
        if args.summarize:
            print(json.dumps(summarize(root), indent=2, sort_keys=True))
            return 0
        event = json.load(sys.stdin)
        record_hook(root, event)
        if event.get("hook_event_name") in STOP_EVENTS:
            print("{}")  # Stop hooks require JSON output.
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Native metrics hook: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
