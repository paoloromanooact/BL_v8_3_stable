#!/usr/bin/env bash
set -euo pipefail

repo=/home/gianluca/BL_v8_3_stable
sonda_dir=/tmp/bq_psi_sonda_20261127
c_queue="$repo/reviews/C_RUN_20261127/queue.log"
driver=scripts/bq_cv_psi_smc.py
driver_sha=$(sha256sum "$repo/$driver")
driver_sha=${driver_sha%% *}

cd "$repo"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1

c_complete() {
    grep -q '^run end exit 0 ' "$c_queue" && grep -q '^recount end exit 0 ' "$c_queue"
}

for likelihood in L2 L3; do
    command_line=(
        timeout --kill-after=30s 110m .venv/bin/python -u "$driver"
        --kind "$likelihood" --out "$sonda_dir/$likelihood" --size 395
        --chains 4 --warm 300 --keep 120 --thin 6 --checkpoints 4,8,12
        --budget-draws 12 --budget-hours 1 --particles 1000 --smc-reps 1
        --repeat-every 10 --extra-reps 1
    )
    if [[ ${1:-} == --dry-run ]]; then
        printf '%q ' "${command_line[@]}"
        printf '\n'
        continue
    fi
    if ! c_complete; then
        printf 'C: runner and recount have not both exited successfully.\n' >&2
        exit 1
    fi
    if [[ $(sha256sum "$repo/$driver") != "$driver_sha  $repo/$driver" ]]; then
        printf 'The driver changed during the probe.\n' >&2
        exit 1
    fi
    date -Is
    printf '%s %s\n' "$likelihood" "$driver_sha"
    "${command_line[@]}"
    date -Is
done

if [[ ${1:-} == --dry-run ]]; then
    if c_complete; then
        printf 'C: ready.\n'
    else
        printf 'C: waiting for successful runner and recount.\n'
    fi
fi
