#!/usr/bin/env python3
"""Summarize numeric usage in Claude Code JSONL transcripts without retaining text.

This is an offline, best-effort diagnostic. Transcript schemas can change.
Session timestamp span includes idle/user time and is not agent execution time.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


TOKEN_KEYS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)
CONTEXT_THRESHOLD = 200_000


def token_counts(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    counts = {}
    for key in TOKEN_KEYS:
        token = value.get(key, 0)
        if type(token) is not int or token < 0:
            return None
        counts[key] = token
    return counts


def timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def file_usage(path: Path) -> tuple[list[dict[str, Any]], int | None]:
    messages: dict[str, dict[str, Any]] = {}
    first: datetime | None = None
    last: datetime | None = None
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue  # A truncated tail must not erase earlier observations.
            if not isinstance(event, dict) or event.get("type") != "assistant":
                continue
            message = event.get("message")
            if not isinstance(message, dict):
                continue
            usage = token_counts(message.get("usage"))
            if usage is None:
                continue
            moment = timestamp(event.get("timestamp"))
            if moment is not None:
                first = min(first, moment) if first else moment
                last = max(last, moment) if last else moment
            model = message.get("model")
            if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", model):
                model = "unknown"
            identifier = message.get("id") or event.get("uuid") or f"line-{number}"
            if not isinstance(identifier, str):
                identifier = f"line-{number}"
            candidate = {"model": model, **usage}
            existing = messages.get(identifier)
            if existing is None or sum(candidate[key] for key in TOKEN_KEYS) >= sum(
                existing[key] for key in TOKEN_KEYS
            ):
                messages[identifier] = candidate
    span = int((last - first).total_seconds() * 1000) if first and last else None
    return list(messages.values()), span


def empty_group() -> dict[str, int]:
    return {
        "files": 0,
        "requests": 0,
        "requests_above_200k_context": 0,
        "context_input_tokens": 0,
        "context_input_tokens_above_200k": 0,
        **{key: 0 for key in TOKEN_KEYS},
    }


def add_request(group: dict[str, int], usage: dict[str, Any]) -> None:
    group["requests"] += 1
    for key in TOKEN_KEYS:
        group[key] += usage[key]
    context = sum(usage[key] for key in TOKEN_KEYS[:3])
    group["context_input_tokens"] += context
    if context > CONTEXT_THRESHOLD:
        group["requests_above_200k_context"] += 1
        group["context_input_tokens_above_200k"] += context


def summarize(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        raise ValueError(f"Transcript directory does not exist: {directory}")
    overall = empty_group()
    groups: dict[str, dict[str, int]] = {}
    session_spans: list[int] = []
    for path in sorted(directory.rglob("*.jsonl")):
        if path.is_symlink() or not path.is_file():
            continue
        kind = "subagent" if "subagents" in path.relative_to(directory).parts else "main"
        requests, span = file_usage(path)
        overall["files"] += 1
        if span is not None:
            session_spans.append(span)
        seen_groups: set[str] = set()
        for request in requests:
            key = f"{kind}:{request['model']}"
            group = groups.setdefault(key, empty_group())
            add_request(group, request)
            add_request(overall, request)
            seen_groups.add(key)
        for key in seen_groups:
            groups[key]["files"] += 1
    return {
        "schema_version": 1,
        "overall": overall,
        "usage_status": "observed" if overall["requests"] else "unavailable",
        "groups": dict(sorted(groups.items())),
        "session_spans_with_timestamps": len(session_spans),
        "max_session_span_ms": max(session_spans) if session_spans else None,
        "limitations": (
            "Timestamp span includes idle/user time; role, phase, fork status, "
            "and actual agent elapsed time are unavailable from this summary. "
            "Input token classes are kept separate; do not equate total input "
            "with cost."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcripts", type=Path, help="Directory of Claude Code JSONL transcripts")
    args = parser.parse_args()
    try:
        print(json.dumps(summarize(args.transcripts), indent=2, sort_keys=True))
    except (OSError, ValueError) as error:
        print(f"Claude usage: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
