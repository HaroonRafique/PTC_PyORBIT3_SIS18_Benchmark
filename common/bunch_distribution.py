"""Deterministic matched six-dimensional Gaussian bunch generation."""

from __future__ import annotations

import numpy as np


def _truncated_normal_pairs(
    generator: np.random.Generator, *, count: int, cut_sigma: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``count`` independent normal pairs inside a radial sigma cut."""

    first = np.empty(count)
    second = np.empty(count)
    accepted = 0
    while accepted < count:
        candidates = generator.normal(size=(max(2 * (count - accepted), 8), 2))
        candidates = candidates[np.sum(candidates**2, axis=1) <= cut_sigma**2]
        take = min(len(candidates), count - accepted)
        first[accepted : accepted + take] = candidates[:take, 0]
        second[accepted : accepted + take] = candidates[:take, 1]
        accepted += take
    return first, second


def matched_gaussian_coordinates(
    *,
    n_particles: int,
    seed: int,
    betax: float,
    alphax: float,
    betay: float,
    alphay: float,
    etax: float,
    etapx: float,
    epsn_x: float,
    epsn_y: float,
    beta_rel: float,
    gamma_rel: float,
    dpp_rms: float,
    bunch_length_rms_m: float,
    particle_mass_GeV: float,
    transverse_cut_sigma: float,
) -> np.ndarray:
    """Return seeded matched coordinates in PyORBIT ``x,xp,y,yp,z,dE`` units.

    ``dE`` is GeV and is converted from the configured relative momentum
    spread via ``dE = dpp * gamma * mass * beta**2``.  Horizontal dispersion
    is applied explicitly after sampling the betatron coordinates.
    """

    if n_particles < 1:
        raise ValueError("n_particles must be positive")
    if min(betax, betay, beta_rel, gamma_rel, particle_mass_GeV, transverse_cut_sigma) <= 0.0:
        raise ValueError("Twiss, beam, mass, and cut values must be positive")
    generator = np.random.default_rng(seed)
    ux, vx = _truncated_normal_pairs(generator, count=n_particles, cut_sigma=transverse_cut_sigma)
    uy, vy = _truncated_normal_pairs(generator, count=n_particles, cut_sigma=transverse_cut_sigma)
    geometric_x, geometric_y = epsn_x / (beta_rel * gamma_rel), epsn_y / (beta_rel * gamma_rel)
    coordinates = np.empty((n_particles, 6), dtype=float)
    coordinates[:, 0] = np.sqrt(betax * geometric_x) * ux
    coordinates[:, 1] = np.sqrt(geometric_x / betax) * (vx - alphax * ux)
    coordinates[:, 2] = np.sqrt(betay * geometric_y) * uy
    coordinates[:, 3] = np.sqrt(geometric_y / betay) * (vy - alphay * uy)
    coordinates[:, 4] = generator.normal(scale=bunch_length_rms_m, size=n_particles)
    dpp = generator.normal(scale=dpp_rms, size=n_particles)
    coordinates[:, 5] = dpp * gamma_rel * particle_mass_GeV * beta_rel**2
    coordinates[:, 0] += etax * dpp
    coordinates[:, 1] += etapx * dpp
    return coordinates
