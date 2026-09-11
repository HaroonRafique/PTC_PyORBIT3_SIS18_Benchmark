"""Deterministic Poincare amplitude scans reusable by SIS18 steps."""

from __future__ import annotations

import numpy as np


def horizontal_poincare_coordinates(*, n_particles: int, n_sigma: float, betax: float, epsn_x: float, beta_rel: float, gamma_rel: float) -> np.ndarray:
    """Return legacy ``i/N`` horizontal scan coordinates in PyORBIT units."""

    sigma_x = np.sqrt(betax * epsn_x / (beta_rel * gamma_rel))
    coordinates = np.zeros((n_particles, 6), dtype=float)
    coordinates[:, 0] = np.arange(n_particles) * (n_sigma / n_particles) * sigma_x
    return coordinates


def amplitude_scan_coordinates(
    *,
    plane: str,
    n_particles: int,
    n_sigma: float,
    betax: float,
    betay: float,
    epsn_x: float,
    epsn_y: float,
    beta_rel: float,
    gamma_rel: float,
) -> np.ndarray:
    """Return a legacy equal-spaced Poincare amplitude scan for one plane."""

    if plane not in {"x", "y"}:
        raise ValueError("plane must be 'x' or 'y'")
    beta_twiss, epsn, coordinate = (betax, epsn_x, 0) if plane == "x" else (betay, epsn_y, 2)
    sigma = np.sqrt(beta_twiss * epsn / (beta_rel * gamma_rel))
    coordinates = np.zeros((n_particles, 6), dtype=float)
    coordinates[:, coordinate] = np.arange(n_particles) * (n_sigma / n_particles) * sigma
    return coordinates


def dominant_fft_tune(signal: np.ndarray) -> float:
    """Return the positive non-DC Fourier bin with the greatest magnitude."""

    spectrum = np.fft.rfft(np.asarray(signal, dtype=float))
    if len(spectrum) < 2:
        raise ValueError("at least two signal samples are required")
    index = int(np.argmax(np.abs(spectrum[1:])) + 1)
    return float(np.fft.rfftfreq(len(spectrum) * 2 - 2)[index])
