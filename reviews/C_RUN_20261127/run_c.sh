#!/bin/bash
# Repeatability C, observed run after the freeze (receipt 91bca29), user's go 27 Nov. Waits for the G3 sizing trial to end
# (no concurrent heavy jobs), then: runner --run (gate + unique files + assembly + products), recount --check (receipt only
# if every check passes and the run is valid). Isolated, single process each.
L=/home/gianluca/BL_v8_3_stable/reviews/C_RUN_20261127/queue.log
cd /home/gianluca/BL_v8_3_stable
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
log() { echo "$1 $(date '+%Y-%m-%d %H:%M:%S')" >> $L; }
log "waiting for the G3 trial"
while pgrep -f "BQ_SID_G3_V_20261127/run.sh" >/dev/null; do sleep 30; done
log "start; HEAD $(git rev-parse HEAD)"
sha256sum docs/SFT_HMI_REPEATABILITY_FREEZE.json docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md scripts/sft_c_repeatability.py scripts/sft_c_repeatability_recount.py >> $L
.venv/bin/python -u scripts/sft_c_repeatability.py --run > reviews/C_RUN_20261127/run.log 2>&1
log "run end exit $?"
.venv/bin/python -u scripts/sft_c_repeatability_recount.py --check > reviews/C_RUN_20261127/recount.log 2>&1
log "recount end exit $?"
log "C queue completed"
