#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_MPI_PROCS="$(python -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["mpi"]["default_processes"])' "$SCRIPT_DIR/config.json")"
MPI_LAUNCHER="${MPI_LAUNCHER:-mpirun}"
MPI_PROCS="${MPI_PROCS:-$DEFAULT_MPI_PROCS}"
LOG_DIR="$SCRIPT_DIR/output/logs"
mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR"
"$MPI_LAUNCHER" -np "$MPI_PROCS" bash -c '
set -o pipefail
rank="${OMPI_COMM_WORLD_RANK:-${PMI_RANK:-${PMIX_RANK:-${MV2_COMM_WORLD_RANK:-0}}}}"
log_path="$1/run_example.rank$(printf "%04d" "$rank").log"
shift
"$@" 2>&1 | tee "$log_path"
' bash "$LOG_DIR" python run_bunch_emittance_evolution.py "$@"
