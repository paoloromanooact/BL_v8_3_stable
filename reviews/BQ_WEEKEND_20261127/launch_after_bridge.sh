#!/bin/bash
# Starts the weekend queue (pilot first) when the bridge check has ended, so that the pilot measures the parallel yield
# on a free machine. One SMC run at a time (shared rule of 27 Nov, docs/HANDOFF.md: --procs 1 for SMC L2/L3).
L=/tmp/claude-1004/-home-gianluca-MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/e7fed292-eee8-4387-bbbc-0aaa56464077/scratchpad/bridge_paired3.log
until grep -q "study exit" "$L" 2>/dev/null; do sleep 20; done
cd /home/gianluca/BL_v8_3_stable
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
echo 1 > reviews/BQ_WEEKEND_20261127/RUNS/PROCS
.venv/bin/python -u scripts/bq_weekend_queue.py --manifest reviews/BQ_WEEKEND_20261127/preflight --out reviews/BQ_WEEKEND_20261127/RUNS \
    --procs 1 --hard-deadline 2026-11-30T09:00 --no-new-after 2026-11-30T06:00 > reviews/BQ_WEEKEND_20261127/queue_stdout.log 2>&1
