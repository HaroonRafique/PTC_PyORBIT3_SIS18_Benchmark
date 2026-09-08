"""Step-local, portable turn-by-turn diagnostic storage."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class TurnRecord:
    turn: int
    x: float
    xp: float
    z: float
    dE: float
    action_x: float


def write_diagnostics(output_dir: Path, records: Sequence[TurnRecord]) -> Path:
    """Write reproducible turn records under the requested step output root."""

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "turn_diagnostics.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(TurnRecord.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    return path
