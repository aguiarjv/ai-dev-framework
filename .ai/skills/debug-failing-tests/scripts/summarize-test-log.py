#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERNS = re.compile(
    r"(fail|failed|failure|error|exception|traceback|assert|expected|actual|panic|timeout)",
    re.IGNORECASE,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize likely-relevant lines from a test or build log.")
    parser.add_argument("logfile", type=Path)
    parser.add_argument("--context", type=int, default=2)
    args = parser.parse_args()

    lines = args.logfile.read_text(encoding="utf-8", errors="replace").splitlines()
    selected: set[int] = set()
    for index, line in enumerate(lines):
        if PATTERNS.search(line):
            for offset in range(-args.context, args.context + 1):
                candidate = index + offset
                if 0 <= candidate < len(lines):
                    selected.add(candidate)

    for index in sorted(selected):
        print(f"{index + 1}: {lines[index]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
