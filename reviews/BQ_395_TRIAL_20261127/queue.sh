#!/bin/bash
# BQ L2/L3 trial on the 395-record block (block 8), for the weekend plan (Codex, 27 Nov): fit and SMC cost measured
# separately, isolated first, then 3 concurrent processes to measure the parallel yield. Synthetic responses G1
# (beta -5, no v), MQ without v, bq_cv_psi_smc.py at 20a673d. Absolute deadline 23:00 today for every run.
Q=/home/gianluca/BL_v8_3_stable/reviews/BQ_395_TRIAL_20261127
cd /home/gianluca/BL_v8_3_stable
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
log() { echo "$1 $(date '+%Y-%m-%d %H:%M:%S')" >> $Q/queue.log; }
log "waiting for the C queue and the G3 trial"
until grep -q "C queue completed" reviews/C_RUN_20261127/queue.log 2>/dev/null; do sleep 30; done
while pgrep -f "BQ_SID_G3_V_20261127/run.sh" >/dev/null; do sleep 30; done
log "start; HEAD $(git rev-parse HEAD)"
sha256sum scripts/bq_cv_psi_smc.py python/sharpbl/bq_smc.py python/sharpbl/bq_core.py python/sharpbl/bq_robust.py >> $Q/queue.log
COMMON="--model MQ --v none --response G1 --chains 4 --warm 300 --keep 600 --thin 6 --particles 1000 --smc-reps 1 --repeat-every 5 --extra-reps 2 --deadline 2026-11-27T23:00"
for K in L2 L3; do
  .venv/bin/python -u scripts/bq_cv_psi_smc.py --kind $K --block-id 8 $COMMON --checkpoints 8,16,24,40 --budget-draws 40 --budget-hours 1.6 --out $Q/ISOLATED_$K > $Q/ISOLATED_$K.log 2>&1
  log "isolated $K end exit $?"
done
# parallel yield: 3 concurrent L2 runs (blocks 7, 8, 9), short SMC budget
for B in 7 8 9; do
  .venv/bin/python -u scripts/bq_cv_psi_smc.py --kind L2 --block-id $B $COMMON --checkpoints 8 --budget-draws 8 --budget-hours 1.0 --out $Q/PARALLEL3_L2_b$B > $Q/PARALLEL3_L2_b$B.log 2>&1 &
done
wait
log "parallel3 L2 end"
log "395 trial completed"
