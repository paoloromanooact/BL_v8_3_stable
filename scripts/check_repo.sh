#!/usr/bin/env bash
# Offline checks; no download and no IDL execution.
# Syntax of all Bash and Python files (python/ and tests/, all subfolders) and,
# if pytest is available (.venv from requirements-v84.txt or system), the test suite.
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
paths = sorted(Path("python").rglob("*.py")) + sorted(Path("tests").rglob("*.py"))
for path in paths:
    ast.parse(path.read_text(), filename=str(path))
print(f"Python syntax OK: {len(paths)} files")
PYTHON
bash scripts/run_pipeline.sh --help >/dev/null
bash scripts/run_pipeline.sh -h >/dev/null
printf '%s\n' 'Bash syntax and launcher help OK.'
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
if "$PY" -c "import pytest" 2>/dev/null; then
  "$PY" -m pytest -q --color=no -p no:cacheprovider tests
else
  printf '%s\n' 'pytest not available: test suite NOT run (install requirements-v84.txt).'
fi
