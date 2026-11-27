#!/bin/bash
# Weekend extension (Codex, 27 Nov): NOT started automatically. Start it only after the pilot queue has completed
# (RUNS/queue.log: "queue completed") and after the decision with Codex. Committed blocks 5 and 6 for the likelihoods
# that passed the pilot gate; then block 3 only if it fits entirely (worst case: cap 200 draws, measured costs), otherwise
# block 4; no new run after Mon 06:00, everything ends by 09:00; one SMC run at a time. Manifest: preflight_lf (LF CSVs,
# same content as preflight; SHAs valid in a fresh checkout).
cd /home/gianluca/BL_v8_3_stable
grep -q "queue completed" reviews/BQ_WEEKEND_20261127/RUNS/queue.log || { echo "pilot queue not completed"; exit 1; }
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
echo 1 > reviews/BQ_WEEKEND_20261127/RUNS/PROCS
.venv/bin/python -u scripts/bq_weekend_queue.py --manifest reviews/BQ_WEEKEND_20261127/preflight_lf --out reviews/BQ_WEEKEND_20261127/RUNS \
    --procs 1 --hard-deadline 2026-11-30T09:00 --no-new-after 2026-11-30T06:00 --extend --blocks 5,6 --next 3 --reserve 4 \
    > reviews/BQ_WEEKEND_20261127/queue_extension_stdout.log 2>&1
