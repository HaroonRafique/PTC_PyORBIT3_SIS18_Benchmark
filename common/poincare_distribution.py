"""Deterministic Poincare amplitude scans reusable by SIS18 steps."""

from __future__ import annotations

import numpy as np


def horizontal_poincare_coordinates(*, n_particles: int, n_sigma: float, betax: float, epsn_x: float, beta_rel: float, gamma_rel: float) -> np.ndarray:
    """Return legacy ``i/N`` horizontal scan coordinates in PyORBIT units."""

    sigma_x = np.sqrt(betax * epsn_x / (beta_rel * gamma_rel))
    coordinates = np.zeros((n_particles, 6), dtype=float)
    coordinates[:, 0] = np.arange(n_particles) * (n_sigma / n_particles) * sigma_x
    return coordinates
