#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec python run_tunes_with_sextupole.py "$@"
