"""Immutable SIS18 benchmark case configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal


Profile = Literal["smoke", "reference", "legacy_artifact", "exploratory"]


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

    if profile not in {"smoke", "reference", "legacy_artifact", "exploratory"}:
        raise ValueError(f"Unknown profile {profile!r}.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "profiles" in payload:
        if payload.get("step") != step:
            raise ValueError(f"Configuration {path} is for step {payload.get('step')!r}, not SIS18 step {step}.")
        profiles = payload["profiles"]
        if "reference" not in profiles or profile not in profiles:
            raise ValueError(f"No {profile!r} profile exists for SIS18 step {step}.")
        raw = dict(profiles["reference"])
        overrides = profiles[profile] if profile != "reference" else {}
    else:
        try:
            raw = dict(payload["steps"][str(step)])
        except KeyError as exc:
            raise ValueError(f"No configuration exists for SIS18 step {step}.") from exc
        overrides = raw.pop("profile_overrides", {}).get(profile, {})
    raw.update(overrides)
    fields = {"intensity", "n_macroparticles", "turns", "sextupole_enabled", "qx", "qy", "restoring_force", "distribution", "seed"}
    return StepConfig(step=step, profile=profile, **{key: value for key, value in raw.items() if key in fields})


def load_profile_payload(path: Path, *, step: int, profile: str) -> dict[str, Any]:
    """Return the fully resolved local profile payload for a standalone step config."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("step") != step or "profiles" not in payload:
        raise ValueError(f"{path} is not a standalone SIS18 step {step} config.")
    profiles = payload["profiles"]
    if "reference" not in profiles or profile not in profiles:
        raise ValueError(f"No {profile!r} profile exists for SIS18 step {step}.")
    resolved: dict[str, Any] = dict(profiles["reference"])
    if profile != "reference":
        for key, value in profiles[profile].items():
            if isinstance(value, dict) and isinstance(resolved.get(key), dict):
                resolved[key] = {**resolved[key], **value}
            else:
                resolved[key] = value
    return resolved
