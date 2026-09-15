#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec python run_slow_trapping.py "$@"
