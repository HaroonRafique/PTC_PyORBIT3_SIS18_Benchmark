"""Poincare plots matching the historical SIS18 Step 1 observables."""

from __future__ import annotations

from pathlib import Path
import numpy as np
from .sis18_plots import BENCHMARK_COLORS, CURRENT_MARKER, CURRENT_SCATTER_SIZE, plt


HORIZONTAL_X_LIMITS = (-0.095, 0.060)
HORIZONTAL_XP_LIMITS = (-0.0115, 0.0080)


def plot_poincare_views(snapshots: np.ndarray, output_dir: Path) -> tuple[Path, Path]:
    """Write historical five-panel and horizontal-phase-space zoom plots."""

    output_dir.mkdir(parents=True, exist_ok=True)
    values = np.asarray(snapshots).reshape(-1, 6)
    pairs = ((0, 2, "x [m]", "y [m]", "Real space"), (1, 3, "xp", "yp", "xp yp"), (0, 1, "x [m]", "xp", "Horizontal phase space"), (2, 3, "y [m]", "yp", "Vertical phase space"), (4, 5, "z [m]", "dE [GeV]", "Longitudinal"))
    figure, axes = plt.subplots(3, 2, figsize=(6, 10))
    figure.subplots_adjust(wspace=0.3, hspace=0.3, left=0.1, right=0.99, top=0.95, bottom=0.05)
    for axis, (x, y, xlabel, ylabel, title) in zip(axes.flat, pairs):
        axis.scatter(values[:, x], values[:, y], s=CURRENT_SCATTER_SIZE, color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER)
        axis.set(xlabel=xlabel, ylabel=ylabel, title=title)
        axis.set_box_aspect(1)
        axis.grid(True, alpha=0.3)
    axes.flat[2].set(xlim=HORIZONTAL_X_LIMITS, ylim=HORIZONTAL_XP_LIMITS)
    axes.flat[4].set(ylim=(-5e-6, 5e-6))
    axes.flat[-1].axis("off")
    full = output_dir / "poincare_full.png"
    figure.savefig(full, dpi=600)
    plt.close(figure)
    figure, axis = plt.subplots(figsize=(6, 6))
    axis.scatter(values[:, 0], values[:, 1], s=CURRENT_SCATTER_SIZE * 1.25, color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER)
    axis.set(xlabel="x [m]", ylabel="xp", title="Horizontal phase space (zoom)", xlim=HORIZONTAL_X_LIMITS, ylim=HORIZONTAL_XP_LIMITS)
    axis.set_box_aspect(1)
    axis.grid(True, alpha=0.3)
    zoom = output_dir / "poincare_x_xp_zoom.png"
    figure.savefig(zoom, dpi=300)
    plt.close(figure)
    return full, zoom
