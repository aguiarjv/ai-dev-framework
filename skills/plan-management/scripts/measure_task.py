#!/usr/bin/env python3
"""Record elapsed time and reported Codex JSONL usage for a plan or task phase."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METRICS_NAME = "METRICS.jsonl"
PHASES = (
    "planning",
    "exploration",
    "implementation",
    "validation",
    "review",
    "integration",
    "correction",
)
ROLES = ("orchestrator", "explorer", "database-explorer", "implementer", "reviewer")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def token_count(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


class CodexUsage:
    """Read usage from one Codex CLI turn without storing its event stream."""

    def __init__(self) -> None:
        self.completed_turns: list[dict[str, Any]] = []
        self.invalid_lines = 0

    def observe(self, line: str) -> None:
        if not line.strip():
            return
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            self.invalid_lines += 1
            return
        if not isinstance(event, dict):
            self.invalid_lines += 1
            return
        if event.get("type") == "turn.completed":
            self.completed_turns.append(event)

    def result(self) -> tuple[str, dict[str, int | None]]:
        empty = {"input_tokens": None, "cached_input_tokens": None, "output_tokens": None}
        if not self.completed_turns:
            return "unavailable", empty
        if len(self.completed_turns) != 1 or self.invalid_lines:
            return "ambiguous", empty

        usage = self.completed_turns[0].get("usage")
        if not isinstance(usage, dict):
            return "unavailable", empty
        input_tokens = token_count(usage.get("input_tokens"))
        output_tokens = token_count(usage.get("output_tokens"))
        if input_tokens is None or output_tokens is None:
            return "unavailable", empty

        cached = token_count(usage.get("cached_input_tokens"))
        if cached is None:
            details = usage.get("input_tokens_details")
            if isinstance(details, dict):
                cached = token_count(details.get("cached_tokens"))
        if cached is not None and cached > input_tokens:
            cached = None
        return "reported", {
            "input_tokens": input_tokens,
            "cached_input_tokens": cached,
            "output_tokens": output_tokens,
        }


def target_kind(target_dir: Path) -> str:
    if not (target_dir / "PROGRESS.md").is_file():
        raise ValueError(f"Not a plan or task directory: {target_dir}")
    if (target_dir / "TASK.md").is_file():
        return "task"
    if (target_dir / "PLAN.md").is_file():
        return "plan"
    raise ValueError(f"Not a plan or task directory: {target_dir}")


def append_record(target_dir: Path, record: dict[str, Any]) -> None:
    with (target_dir / METRICS_NAME).open("a", encoding="utf-8") as metrics:
        metrics.write(json.dumps(record, separators=(",", ":")) + "\n")


def run_phase(args: argparse.Namespace) -> int:
    target_dir = args.target_dir.resolve()
    kind = target_kind(target_dir)
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        raise ValueError("A command that emits Codex JSONL is required after --")

    collector = CodexUsage()
    started_at = utc_timestamp()
    started_ns = time.monotonic_ns()
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, errors="replace")
    except OSError as error:
        raise ValueError(f"Could not start command: {error}") from error

    try:
        assert process.stdout is not None
        for line in process.stdout:
            collector.observe(line)
            sys.stdout.write(line)
            sys.stdout.flush()
        exit_code = process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        exit_code = 130
    finally:
        if process.stdout is not None:
            process.stdout.close()

    elapsed_ms = (time.monotonic_ns() - started_ns) // 1_000_000
    usage_status, usage = collector.result()
    record = {
        "schema_version": 1,
        "run_id": str(uuid.uuid4()),
        "target_kind": kind,
        "target_id": target_dir.name,
        "phase": args.phase,
        "role": args.role,
        "source": "codex-jsonl",
        "started_at": started_at,
        "ended_at": utc_timestamp(),
        "elapsed_ms": elapsed_ms,
        "exit_code": exit_code,
        "completed_turns": len(collector.completed_turns),
        "invalid_lines": collector.invalid_lines,
        "usage_status": usage_status,
        "usage": usage,
    }
    append_record(target_dir, record)
    print(f"Recorded {args.phase} metrics in {target_dir / METRICS_NAME}", file=sys.stderr)
    return exit_code


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    phases: dict[str, dict[str, int]] = {}
    for record in records:
        phase = record["phase"]
        summary = phases.setdefault(
            phase,
            {
                "runs": 0,
                "elapsed_ms": 0,
                "reported_usage_runs": 0,
                "missing_usage_runs": 0,
                "known_input_tokens": 0,
                "known_cached_input_tokens": 0,
                "known_output_tokens": 0,
                "missing_cached_input_runs": 0,
            },
        )
        summary["runs"] += 1
        summary["elapsed_ms"] += record["elapsed_ms"]
        usage = record["usage"]
        if record["usage_status"] == "reported":
            summary["reported_usage_runs"] += 1
            summary["known_input_tokens"] += usage["input_tokens"]
            summary["known_output_tokens"] += usage["output_tokens"]
            if usage["cached_input_tokens"] is None:
                summary["missing_cached_input_runs"] += 1
            else:
                summary["known_cached_input_tokens"] += usage["cached_input_tokens"]
        else:
            summary["missing_usage_runs"] += 1
    return {"runs": len(records), "phases": phases}


def summarize(args: argparse.Namespace) -> int:
    target_dir = args.target_dir.resolve()
    target_kind(target_dir)
    path = target_dir / METRICS_NAME
    if not path.is_file():
        raise ValueError(f"No metrics recorded: {path}")
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            record = json.loads(line)
            if not isinstance(record, dict) or record.get("schema_version") != 1:
                raise ValueError("unsupported metrics record")
            records.append(record)
        except (json.JSONDecodeError, ValueError) as error:
            raise ValueError(f"Invalid metrics at {path}:{number}: {error}") from error
    result = summarize_records(records)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    print(f"{target_dir.name}: {result['runs']} recorded runs")
    print("Phase            Runs  Agent time  Input*  Cached*  Output*  Missing usage")
    for phase, values in sorted(result["phases"].items()):
        print(
            f"{phase:<16} {values['runs']:>4}  {values['elapsed_ms'] / 1000:>9.1f}s"
            f"  {values['known_input_tokens']:>6}  {values['known_cached_input_tokens']:>7}"
            f"  {values['known_output_tokens']:>7}  {values['missing_usage_runs']:>13}"
        )
    print("* Known reported tokens only; missing usage is never counted as zero.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="action", required=True)
    run = subcommands.add_parser("run", help="Run a Codex JSONL command and record its metrics")
    run.add_argument("--target-dir", required=True, type=Path)
    run.add_argument("--phase", required=True, choices=PHASES)
    run.add_argument("--role", required=True, choices=ROLES)
    run.add_argument("command", nargs=argparse.REMAINDER)
    report = subcommands.add_parser("summarize", help="Summarize a plan or task's metrics")
    report.add_argument("--target-dir", required=True, type=Path)
    report.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        return run_phase(args) if args.action == "run" else summarize(args)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
