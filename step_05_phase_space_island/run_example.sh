#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec python run_phase_space_island.py "$@"
