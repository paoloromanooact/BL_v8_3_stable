#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/run_pipeline.sh YYYY-MM-DD HH:MM --email you@example.com [options]
  bash scripts/run_pipeline.sh YYYY-MM-DD --email you@example.com [options]

Examples:
  bash scripts/run_pipeline.sh 2024-05-08 03:12 --email you@example.com
  bash scripts/run_pipeline.sh 2024-05-08 --email you@example.com --full-day

Options:
  --email EMAIL          JSOC registered email. Can also use JSOC_EMAIL env var.
  --full-day             Download/process the whole day instead of one HH:MM sample.
  --skip-download        Do not call JSOC; process files already in data directory.
  --no-diagnostics       Do not create diagnostic PNGs.
  --all-diagnostics      Plot all rows, not only suspicious rows.
  --threshold VALUE      Br threshold in Gauss. Default: 100
  --max-abs-br VALUE     Reject |Br| above this value. Default: 10000
  --bmap-min VALUE       Bitmap minimum included in mask. Default: 1
  --leading-side VALUE   XMAX or XMIN. Default: XMAX
  --idl-root PATH        Project root as seen by IDL/SSW. Usually auto-detected.
  --idl-command CMD      IDL command to run. Default: sswidl
  --idl-shell SHELL      Shell used to start IDL. Default: tcsh
  --help                 Show this help.

Notes:
  The project root is derived from the script location.
  Use --idl-root if IDL/SSW sees the project under a different path.
  Times are TAI, not local time or UTC.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if [[ "$1" == --help || "$1" == -h ]]; then
  usage
  exit 0
fi

DATE="$1"
shift

TIME_ARG=""
if [[ $# -gt 0 && "$1" != --* ]]; then
  TIME_ARG="$1"
  shift
fi

EMAIL="${JSOC_EMAIL:-}"
FULL_DAY=0
SKIP_DOWNLOAD=0
DO_DIAGNOSTICS=1
ALL_DIAGNOSTICS=0
THRESHOLD="100D"
MAX_ABS_BR="10000D"
BMAP_MIN="1D"
LEADING_SIDE="XMAX"
IDL_ROOT_OVERRIDE=""
IDL_COMMAND="sswidl"
IDL_SHELL="tcsh"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --email)
      EMAIL="$2"
      shift 2
      ;;
    --full-day)
      FULL_DAY=1
      shift
      ;;
    --skip-download)
      SKIP_DOWNLOAD=1
      shift
      ;;
    --no-diagnostics)
      DO_DIAGNOSTICS=0
      shift
      ;;
    --all-diagnostics)
      ALL_DIAGNOSTICS=1
      shift
      ;;
    --threshold)
      THRESHOLD="$2D"
      shift 2
      ;;
    --max-abs-br)
      MAX_ABS_BR="$2D"
      shift 2
      ;;
    --bmap-min)
      BMAP_MIN="$2D"
      shift 2
      ;;
    --leading-side)
      LEADING_SIDE="$2"
      shift 2
      ;;
    --idl-root)
      IDL_ROOT_OVERRIDE="$2"
      shift 2
      ;;
    --idl-command)
      IDL_COMMAND="$2"
      shift 2
      ;;
    --idl-shell)
      IDL_SHELL="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$FULL_DAY" -eq 1 ]]; then
  TIME_ARG=""
fi

if [[ "$SKIP_DOWNLOAD" -eq 0 && -z "$EMAIL" ]]; then
  echo "ERROR: provide --email or set JSOC_EMAIL." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -n "$IDL_ROOT_OVERRIDE" ]]; then
  IDL_PROJECT_ROOT="$IDL_ROOT_OVERRIDE"
else
  IDL_PROJECT_ROOT="$PROJECT_ROOT"
fi

DATE_COMPACT="${DATE//-/}"
if [[ -n "$TIME_ARG" ]]; then
  TIME_COMPACT="${TIME_ARG//:/}"
  RUN_TAG="${DATE_COMPACT}_${TIME_COMPACT}"
  DATA_SUBDIR="data/${RUN_TAG}"
  CSV_NAME="sharp_bl_${RUN_TAG}.csv"
else
  RUN_TAG="${DATE_COMPACT}_full"
  DATA_SUBDIR="data/${RUN_TAG}"
  CSV_NAME="sharp_bl_${RUN_TAG}.csv"
fi

DATA_DIR="$PROJECT_ROOT/$DATA_SUBDIR"
OUTPUT_DIR="$PROJECT_ROOT/output"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$DATA_DIR" "$OUTPUT_DIR" "$LOG_DIR"

RUN_LOG="$LOG_DIR/run_${RUN_TAG}.log"
IDL_BATCH="$LOG_DIR/run_${RUN_TAG}_idl_batch.pro"
IDL_LOG="$LOG_DIR/run_${RUN_TAG}_idl.log"
CSV_FILE_IDL="$IDL_PROJECT_ROOT/output/$CSV_NAME"
DATA_DIR_IDL="$IDL_PROJECT_ROOT/$DATA_SUBDIR"
DIAG_DIR_IDL="$IDL_PROJECT_ROOT/output/diagnostics_${RUN_TAG}"

{
  echo "BL pipeline run"
  echo "  date             : $DATE"
  echo "  time             : ${TIME_ARG:-FULL_DAY}"
  echo "  shell root       : $PROJECT_ROOT"
  echo "  IDL root         : $IDL_PROJECT_ROOT"
  echo "  data dir shell   : $DATA_DIR"
  echo "  data dir IDL     : $DATA_DIR_IDL"
  echo "  output CSV       : $OUTPUT_DIR/$CSV_NAME"
  echo "  diagnostics      : $DO_DIAGNOSTICS"
  echo "  IDL shell        : $IDL_SHELL"
  echo "  IDL command      : $IDL_COMMAND"
} | tee "$RUN_LOG"

if [[ "$SKIP_DOWNLOAD" -eq 0 ]]; then
  echo "Downloading SHARP files..." | tee -a "$RUN_LOG"
  if [[ -n "$TIME_ARG" ]]; then
    python3 "$PROJECT_ROOT/python/download_sharp_day.py" "$DATE" \
      --email "$EMAIL" \
      --times "$TIME_ARG" \
      --out "$DATA_DIR" 2>&1 | tee -a "$RUN_LOG"
  else
    python3 "$PROJECT_ROOT/python/download_sharp_day.py" "$DATE" \
      --email "$EMAIL" \
      --out "$DATA_DIR" 2>&1 | tee -a "$RUN_LOG"
  fi
else
  echo "Skipping download; using existing files in $DATA_DIR" | tee -a "$RUN_LOG"
fi

cat > "$IDL_BATCH" <<EOFIDL
project_root = '$IDL_PROJECT_ROOT'
CD, project_root + '/idl'
.compile *.pro

data_dir = '$DATA_DIR_IDL'
csv_file = '$CSV_FILE_IDL'

process_sharp_day, data_dir, \$
  OUTPUT_CSV=csv_file, \$
  THRESHOLD=$THRESHOLD, MAX_ABS_BR=$MAX_ABS_BR, BMAP_MIN=$BMAP_MIN, \$
  LEADING_SIDE='$LEADING_SIDE', /VERBOSE

EOFIDL

if [[ "$DO_DIAGNOSTICS" -eq 1 ]]; then
  if [[ "$ALL_DIAGNOSTICS" -eq 1 ]]; then
    cat >> "$IDL_BATCH" <<EOFIDL
plot_sharp_diagnostics_from_csv, csv_file, DATA_DIR=data_dir, \$
  OUT_DIR='$DIAG_DIR_IDL', /VERBOSE
EOFIDL
  else
    cat >> "$IDL_BATCH" <<EOFIDL
plot_sharp_diagnostics_from_csv, csv_file, DATA_DIR=data_dir, \$
  OUT_DIR='$DIAG_DIR_IDL', /SUSPICIOUS, /VERBOSE
EOFIDL
  fi
fi

cat >> "$IDL_BATCH" <<'EOFIDL'
EXIT
EOFIDL

if ! command -v "$IDL_SHELL" >/dev/null 2>&1; then
  echo "ERROR: IDL shell not found: $IDL_SHELL" | tee -a "$RUN_LOG"
  echo "On your system this should usually be tcsh." | tee -a "$RUN_LOG"
  echo "Run the generated IDL commands manually from: $IDL_BATCH" | tee -a "$RUN_LOG"
  exit 1
fi

echo "Running IDL batch through $IDL_SHELL using command: $IDL_COMMAND" | tee -a "$RUN_LOG"
# Use tcsh/SSW so that .cshrc initializes SolarSoft and READ_SDO is available.
# This mirrors the manual workflow: tcsh -> sswidl.
IDL_TCSH_COMMAND="$IDL_COMMAND < '$IDL_BATCH' > '$IDL_LOG'"
"$IDL_SHELL" -c "$IDL_TCSH_COMMAND" || {
  echo "ERROR: IDL/SSW pipeline failed. See: $IDL_LOG" | tee -a "$RUN_LOG"
  tail -80 "$IDL_LOG" | tee -a "$RUN_LOG"
  echo "If needed, test manually with:" | tee -a "$RUN_LOG"
  echo "  tcsh" | tee -a "$RUN_LOG"
  echo "  $IDL_COMMAND < $IDL_BATCH" | tee -a "$RUN_LOG"
  exit 1
}

cat "$IDL_LOG" >> "$RUN_LOG"

echo "Done." | tee -a "$RUN_LOG"
echo "CSV: $OUTPUT_DIR/$CSV_NAME" | tee -a "$RUN_LOG"
if [[ "$DO_DIAGNOSTICS" -eq 1 ]]; then
  echo "Diagnostics: $OUTPUT_DIR/diagnostics_${RUN_TAG}" | tee -a "$RUN_LOG"
fi
echo "Log: $RUN_LOG" | tee -a "$RUN_LOG"
