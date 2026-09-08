"""Numerical comparisons against extractable historical SIS18 data."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class ComparisonResult:
    samples: int
    max_abs_residual: float
    rms_residual: float


def compare_tune_tables(reference: np.ndarray, candidate: np.ndarray) -> ComparisonResult:
    """Interpolate candidate tunes to the reference amplitude grid."""

    reference = np.asarray(reference, dtype=float)
    candidate = np.asarray(candidate, dtype=float)
    if reference.ndim != 2 or candidate.ndim != 2 or reference.shape[1] != 2 or candidate.shape[1] != 2:
        raise ValueError("Tune tables must each have two columns: amplitude and tune.")
    interpolated = np.interp(reference[:, 0], candidate[:, 0], candidate[:, 1])
    residuals = interpolated - reference[:, 1]
    return ComparisonResult(
        samples=len(residuals),
        max_abs_residual=round(float(np.max(np.abs(residuals))), 12),
        rms_residual=round(float(np.sqrt(np.mean(residuals**2))), 12),
    )
