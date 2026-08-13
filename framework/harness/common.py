#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def framework_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_pack(path: Path) -> dict:
    """Parse the small YAML subset used by framework/packs/*.yaml."""
    pack: dict[str, object] = {}
    current_list: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" "):
            current_list = None
            if stripped.endswith(":"):
                key = stripped[:-1]
                if key in {"adapters", "agents", "guides", "harnesses", "skills", "templates"}:
                    pack[key] = []
                    current_list = key
                else:
                    raise ValueError(f"Unsupported mapping section: {key}")
                continue

            key, value = split_key_value(stripped)
            pack[key] = value
            continue

        if current_list and stripped.startswith("- "):
            item = stripped[2:].strip()
            cast_list = pack[current_list]
            assert isinstance(cast_list, list)
            cast_list.append(item)
            continue

        raise ValueError(f"Could not parse line in {path}: {raw}")

    return pack


def split_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise ValueError(f"Expected key/value line: {line}")
    key, value = line.split(":", 1)
    return key.strip(), value.strip().strip("\"'")


def pack_path(pack_name: str) -> Path:
    root = framework_root()
    candidate = root / "framework" / "packs" / f"{pack_name}.yaml"
    if not candidate.exists():
        raise FileNotFoundError(f"Pack not found: {candidate}")
    return candidate
