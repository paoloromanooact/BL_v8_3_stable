#!/bin/bash
# Waits for the C queue (runner + recount) and the G3 trial, then runs Codex's probe unchanged (copy run_codex.sh,
# original in /tmp/bq_psi_sonda_20261127); its outputs are copied here at the end (the /tmp copy is not persistent).
W=/home/gianluca/BL_v8_3_stable/reviews/BQ_PSI_SONDA_20261127
log() { echo "$1 $(date '+%Y-%m-%d %H:%M:%S')" >> $W/wrapper.log; }
log "waiting for C and G3"
until grep -q "C queue completed" /home/gianluca/BL_v8_3_stable/reviews/C_RUN_20261127/queue.log 2>/dev/null; do sleep 30; done
while pgrep -f "BQ_SID_G3_V_20261127/run.sh" >/dev/null; do sleep 30; done
log "start Codex probe"
bash /tmp/bq_psi_sonda_20261127/run.sh > $W/sonda.log 2>&1
log "probe end exit $?"
cp -r /tmp/bq_psi_sonda_20261127/L2 /tmp/bq_psi_sonda_20261127/L3 $W/ 2>/dev/null
log "outputs copied; probe completed"
