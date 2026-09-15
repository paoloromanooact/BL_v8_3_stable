#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
: "${JSOC_EMAIL:?Set JSOC_EMAIL to your JSOC registered email address}"
python3 "$PROJECT_ROOT/python/download_sharp_day.py" 2024-05-08 \
  --email "$JSOC_EMAIL" \
  --times 03:12 \
  --out "$PROJECT_ROOT/data/20240508_0312"
