"""Structured, reproducible run-manifest writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def write_run_manifest(path: Path, payload: Mapping[str, Any]) -> Path:
    """Write an UTF-8 deterministic JSON run manifest and return its path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
