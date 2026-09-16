"""Portable single-particle trapping diagnostics and legacy comparisons."""

from __future__ import annotations

from pathlib import Path

import numpy as np


HISTORICAL_BETAX = 12.79426135
HISTORICAL_ALPHAX = 1.283306757


def single_particle_coordinates(*, launch: str, bunch_length_rms_m: float) -> np.ndarray:
    """Return the published or stored-artifact Step 6 launch in PyORBIT units."""

    launches = {"reference": 5.0e-3, "legacy_artifact": 0.0, "smoke": 5.0e-3}
    try:
        x = launches[launch]
    except KeyError as error:
        raise ValueError(f"unknown single-particle launch {launch!r}") from error
    return single_particle_coordinates_at(x_m=x, bunch_length_rms_m=bunch_length_rms_m)


def single_particle_coordinates_at(*, x_m: float, bunch_length_rms_m: float) -> np.ndarray:
    """Return a deterministic horizontal launch at ``z=2.5 sigma_z``."""

    return np.asarray((x_m, 0.0, 0.0, 0.0, 2.5 * bunch_length_rms_m, 0.0))


def horizontal_action(x: float | np.ndarray, xp: float | np.ndarray) -> float | np.ndarray:
    """Return the historical Step 6 unnormalised horizontal action."""

    gamma_x = (1.0 + HISTORICAL_ALPHAX**2) / HISTORICAL_BETAX
    return HISTORICAL_BETAX * np.asarray(xp) ** 2 + 2.0 * HISTORICAL_ALPHAX * np.asarray(x) * np.asarray(xp) + gamma_x * np.asarray(x) ** 2


def legacy_particle_records(path: Path) -> np.ndarray:
    """Read legacy ``Particles_all.dat`` as turn, x, xp, y, yp, z, dE records."""

    values = np.loadtxt(path, comments="#", usecols=(1, 2, 3, 4, 5, 6, 7), dtype=float)
    return np.atleast_2d(values)


def trajectory_comparison(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    """Compare equal-turn trajectories at the six-decimal legacy export precision."""

    reference, candidate = np.asarray(reference, dtype=float), np.asarray(candidate, dtype=float)
    if reference.ndim != 2 or candidate.ndim != 2 or reference.shape[1] != 7 or candidate.shape[1] != 7:
        raise ValueError("trajectory records must have turn, x, xp, y, yp, z, and dE columns")
    if reference.shape != candidate.shape or not np.array_equal(reference[:, 0], candidate[:, 0]):
        return {"agreement": False, "samples": 0, "reason": "turn grids differ"}
    residuals = np.round(candidate[:, 1:], 6) - np.round(reference[:, 1:], 6)
    labels = ("x_m", "xp_rad", "y_m", "yp_rad", "z_m", "dE_GeV")
    maxima = {label: float(np.max(np.abs(residuals[:, index]))) for index, label in enumerate(labels)}
    return {"agreement": not bool(np.any(residuals)), "samples": len(reference), "max_abs_residual": maxima}
