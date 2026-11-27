#!/bin/bash
# G3 sizing trial requested by Codex (27 Nov): only MQ_v_hn20, 4 chains, 300 warm-up + 1500 draws, checkpoints 500/1000/1500.
# Same seed zone as the G1/G2 short trials (SEED0 36_404_000): response seed 36_404_000 + 1000 g + 100 r + 99 (unchanged);
# chain seeds 36_404_000 + 1000 g + 100 r + 10 f + c with f = 1 (the v fit in the full FITS list). Running only the v fit,
# FITS is reduced to it (f = 0), so SEED0 is set to 36_404_010 for the chains and the response keeps its base 36_404_000.
set -euo pipefail
pilot_dir=/home/gianluca/BL_v8_3_stable/reviews/BQ_SID_G3_V_20261127
cd /home/gianluca/BL_v8_3_stable
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
date -Is
git rev-parse HEAD
sha256sum scripts/bq_sizing_pilot.py python/sharpbl/bq_core.py python/sharpbl/bq_diag.py
timeout 45m .venv/bin/python -u -c '
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path("scripts").resolve()))
import bq_sizing_pilot as p
p.CHECKPOINTS = (500, 1000, 1500)
p.FITS = (p.FITS[1],)
p.SEED0 = 36_404_010
p.response = lambda D, g, r: p.IP.simulate(D, p.GENS[g], np.random.default_rng(36_404_000 + 1000 * g + 100 * r + 99))
p.main()
' --out "$pilot_dir/results" --reps 1 --gens 2 --warm 300 --keep 1500 --procs 4
date -Is
