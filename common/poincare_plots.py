"""Poincare plots matching the historical SIS18 Step 1 observables."""

from __future__ import annotations

from pathlib import Path
import numpy as np
from .sis18_plots import BENCHMARK_COLORS, CURRENT_MARKER, CURRENT_SCATTER_SIZE, plt


TRANSVERSE_POSITION_SCALE = 1000.0  # m -> mm
TRANSVERSE_ANGLE_SCALE = 1000.0  # rad -> mrad
HORIZONTAL_X_LIMITS = (-95.0, 60.0)
HORIZONTAL_XP_LIMITS = (-11.5, 8.0)


def plot_poincare_views(
    snapshots: np.ndarray,
    output_dir: Path,
    *,
    horizontal_limits: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> tuple[Path, Path]:
    """Write historical five-panel and horizontal-phase-space zoom plots."""

    output_dir.mkdir(parents=True, exist_ok=True)
    x_limits, xp_limits = horizontal_limits or (HORIZONTAL_X_LIMITS, HORIZONTAL_XP_LIMITS)
    values = np.asarray(snapshots).reshape(-1, 6).copy()
    values[:, (0, 2)] *= TRANSVERSE_POSITION_SCALE
    values[:, (1, 3)] *= TRANSVERSE_ANGLE_SCALE
    pairs = ((0, 2, "x [mm]", "y [mm]", "Real space"), (1, 3, "xp [mrad]", "yp [mrad]", "xp yp"), (0, 1, "x [mm]", "xp [mrad]", "Horizontal phase space"), (2, 3, "y [mm]", "yp [mrad]", "Vertical phase space"), (4, 5, "z [m]", "dE [GeV]", "Longitudinal"))
    figure, axes = plt.subplots(3, 2, figsize=(6, 10))
    figure.subplots_adjust(wspace=0.45, hspace=0.3, left=0.18, right=0.97, top=0.95, bottom=0.05)
    for axis, (x, y, xlabel, ylabel, title) in zip(axes.flat, pairs):
        axis.scatter(values[:, x], values[:, y], s=CURRENT_SCATTER_SIZE, color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER)
        axis.set(xlabel=xlabel, ylabel=ylabel, title=title)
        axis.set_box_aspect(1)
        axis.grid(True, alpha=0.3)
    axes.flat[2].set(xlim=x_limits, ylim=xp_limits)
    axes.flat[4].set(ylim=(-5e-6, 5e-6))
    axes.flat[-1].axis("off")
    full = output_dir / "poincare_full.png"
    figure.savefig(full, dpi=600)
    plt.close(figure)
    figure, axis = plt.subplots(figsize=(6, 6))
    axis.scatter(values[:, 0], values[:, 1], s=CURRENT_SCATTER_SIZE * 1.25, color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER)
    axis.set(xlabel="x [mm]", ylabel="xp [mrad]", title="Horizontal phase space (zoom)", xlim=x_limits, ylim=xp_limits)
    axis.set_box_aspect(1)
    axis.grid(True, alpha=0.3)
    figure.subplots_adjust(left=0.23, right=0.96, top=0.90, bottom=0.14)
    zoom = output_dir / "poincare_x_xp_zoom.png"
    figure.savefig(zoom, dpi=300)
    plt.close(figure)
    return full, zoom
