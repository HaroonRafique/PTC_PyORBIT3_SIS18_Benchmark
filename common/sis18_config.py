"""Immutable SIS18 benchmark case configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal


Profile = Literal["smoke", "reference"]


@dataclass(frozen=True)
class StepConfig:
    """Resolved configuration for one SIS18 benchmark step and profile."""

    step: int
    profile: Profile
    intensity: float
    n_macroparticles: int
    turns: int
    sextupole_enabled: bool
    qx: float
    qy: float
    restoring_force: float = 0.0
    distribution: str = "poincare"
    seed: int = 20260908


def load_step_config(path: Path, *, step: int, profile: str) -> StepConfig:
    """Load a step/profile configuration and apply its explicit overrides."""

    if profile not in {"smoke", "reference"}:
        raise ValueError(f"Unknown profile {profile!r}; expected 'smoke' or 'reference'.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    try:
        raw: dict[str, Any] = dict(payload["steps"][str(step)])
    except KeyError as exc:
        raise ValueError(f"No configuration exists for SIS18 step {step}.") from exc
    overrides = raw.pop("profile_overrides", {}).get(profile, {})
    raw.update(overrides)
    return StepConfig(step=step, profile=profile, **raw)
