#!/bin/bash
set -euo pipefail
pilot_dir=/tmp/bq_sid_short_20261127
cd /home/gianluca/BL_v8_3_stable
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
date -Is
git rev-parse HEAD
sha256sum scripts/bq_sizing_pilot.py python/sharpbl/bq_core.py python/sharpbl/bq_diag.py
timeout 35m .venv/bin/python -u -c '
import sys
from pathlib import Path
sys.path.insert(0, str(Path("scripts").resolve()))
import bq_sizing_pilot as p
p.CHECKPOINTS = (100, 250, 500)
p.SEED0 = 36_404_000
p.main()
' --out "$pilot_dir/results" --reps 1 --gens 0 --warm 300 --keep 500 --procs 8
date -Is
