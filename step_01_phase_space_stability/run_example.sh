#!/usr/bin/env bash
set -euo pipefail
STEP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${STEP_DIR}/.." && pwd)"
PYTHON="${VENV_PYTHON:-python}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib}"
mkdir -p "${STEP_DIR}/output/logs"
cd "${REPO_ROOT}"
"${PYTHON}" "${STEP_DIR}/run_phase_space_stability.py" "$@" 2>&1 | tee "${STEP_DIR}/output/logs/run_example.log"
