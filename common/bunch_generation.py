"""Matched bunch generation adapted from the PTC-PyORBIT3 examples API."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

import numpy as np


@dataclass(frozen=True)
class MatchedGaussianConfig:
    """Explicit matched-Gaussian input for a local MPI particle share."""

    n_macroparticles: int
    seed: int
    eps_x_rms: float
    eps_y_rms: float
    z_rms: float
    dE_rms: float
    intensity: float = 1.0
    mass_gev: float = 0.9382720813
    kinetic_energy_gev: float = 0.011400033408140997
    x_limit: float = 5.0
    y_limit: float = 5.0
    longitudinal_cut_sigma: float = 5.0


def _truncated_normal(generator: np.random.Generator, *, count: int, sigma: float, cut_sigma: float) -> np.ndarray:
    values = np.empty(count, dtype=float)
    accepted = 0
    while accepted < count:
        candidates = generator.normal(0.0, sigma, size=max(2 * (count - accepted), 8))
        candidates = candidates[np.abs(candidates) < cut_sigma * sigma]
        take = min(len(candidates), count - accepted)
        values[accepted : accepted + take] = candidates[:take]
        accepted += take
    return values


def make_configured_particle_bunch(start: Any, config: MatchedGaussianConfig):
    """Build the examples-style transverse Gaussian plus Step 9 longitudinal cut.

    ``start`` follows the examples' lattice-start interface with Twiss,
    dispersion, and closed-orbit attributes.  The returned ParticleBunch uses
    local-rank coordinates; callers set global PyORBIT macrosize afterwards.
    """

    if config.n_macroparticles < 1:
        raise ValueError("n_macroparticles must be positive")
    if min(config.eps_x_rms, config.eps_y_rms, config.z_rms, config.dE_rms, config.longitudinal_cut_sigma) <= 0.0:
        raise ValueError("emittances, longitudinal RMS values, and cuts must be positive")
    from pyparticlebunch import ParticleBunch

    np.random.seed(config.seed)
    random.seed(config.seed)
    particle_bunch = ParticleBunch.MatchedGaussian_4D(
        n=config.n_macroparticles,
        emittance_x=config.eps_x_rms,
        emittance_y=config.eps_y_rms,
        alpha_x=start.alpha_x,
        beta_x=start.beta_x,
        alpha_y=start.alpha_y,
        beta_y=start.beta_y,
        x_limit=config.x_limit,
        y_limit=config.y_limit,
    )
    values = particle_bunch.to_numpy()
    generator = np.random.default_rng(config.seed)
    values[:, 4] = _truncated_normal(generator, count=len(values), sigma=config.z_rms, cut_sigma=config.longitudinal_cut_sigma)
    values[:, 5] = _truncated_normal(generator, count=len(values), sigma=config.dE_rms, cut_sigma=config.longitudinal_cut_sigma)
    total_energy = config.kinetic_energy_gev + config.mass_gev
    beta = np.sqrt(max(0.0, 1.0 - (config.mass_gev / total_energy) ** 2))
    delta = values[:, 5] / (beta * beta * total_energy)
    values[:, 0] += start.orbit_x + start.disp_x * delta
    values[:, 1] += start.orbit_px + start.disp_px * delta
    values[:, 2] += start.orbit_y + start.disp_y * delta
    values[:, 3] += start.orbit_py + start.disp_py * delta
    return ParticleBunch.from_numpy(values)


def make_pyorbit_bunch(particle_bunch: Any, config: MatchedGaussianConfig):
    """Convert an examples-style ParticleBunch into a compiled PyORBIT bunch."""

    from pyparticlebunch import BeamParameters, to_pyorbit_bunch

    return to_pyorbit_bunch(
        particle_bunch,
        BeamParameters(
            mass_gev=config.mass_gev,
            kinetic_energy_gev=config.kinetic_energy_gev,
            total_macro_size=config.intensity,
        ),
    )
