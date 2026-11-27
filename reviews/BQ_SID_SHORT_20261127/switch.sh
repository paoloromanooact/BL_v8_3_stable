#!/bin/bash
set -euo pipefail
root=/tmp/bq_sid_short_20261127
pgid=2595550
owner=$(ps -p "$pgid" -o pgid=,stat=,args=)
[[ $owner =~ ^[[:space:]]*2595550[[:space:]]+S[^[:space:]]*[[:space:]]+bash[[:space:]]+/home/gianluca/BL_v8_3_stable/reviews/BQ_QUEUE_20261127/queue_part2.sh$ ]]
[[ ! -e "$root/results" ]]
kill -STOP -- "-$pgid"
setsid nohup bash "$root/run.sh" > "$root/pilot.log" 2>&1 < /dev/null &
printf 'Paused process group %s and started short-run launcher %s\n' "$pgid" "$!"
