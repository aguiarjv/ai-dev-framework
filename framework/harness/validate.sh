#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/validate.py" "$@"
python3 -m unittest discover -s "$SCRIPT_DIR/tests" -p 'test_*.py'
