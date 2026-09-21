#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec python run_bunch_emittance_evolution.py "$@"
