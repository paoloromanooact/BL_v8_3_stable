#!/usr/bin/env bash
# Offline checks; no download and no IDL execution.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
for script in scripts/*.sh; do
  bash -n "$script"
done
python3 - <<'PYTHON'
import ast
from pathlib import Path
for path in sorted(Path("python").glob("*.py")):
    ast.parse(path.read_text(), filename=str(path))
    print(f"Python syntax OK: {path}")
PYTHON
bash scripts/run_pipeline.sh --help >/dev/null
bash scripts/run_pipeline.sh -h >/dev/null
printf '%s\n' 'Bash syntax and launcher help OK.'
