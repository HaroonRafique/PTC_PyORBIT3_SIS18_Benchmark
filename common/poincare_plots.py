"""Poincare plots matching the historical SIS18 Step 1 observables."""

from __future__ import annotations

from pathlib import Path
import numpy as np
from .sis18_plots import plt


def plot_poincare_views(snapshots: np.ndarray, output_dir: Path) -> tuple[Path, Path]:
    """Write historical five-panel and horizontal-phase-space zoom plots."""

    output_dir.mkdir(parents=True, exist_ok=True)
    values = np.asarray(snapshots).reshape(-1, 6)
    pairs = ((0, 2, "x [m]", "y [m]", "Real space"), (1, 3, "xp", "yp", "xp yp"), (0, 1, "x [m]", "xp", "Horizontal phase space"), (2, 3, "y [m]", "yp", "Vertical phase space"), (4, 5, "z [m]", "dE [GeV]", "Longitudinal"))
    figure, axes = plt.subplots(3, 2, figsize=(10, 12), constrained_layout=True)
    for axis, (x, y, xlabel, ylabel, title) in zip(axes.flat, pairs):
        axis.scatter(values[:, x], values[:, y], s=3, c="m")
        axis.set(xlabel=xlabel, ylabel=ylabel, title=title)
        axis.grid(True, alpha=0.3)
    axes.flat[-1].axis("off")
    full = output_dir / "poincare_full.png"
    figure.savefig(full, dpi=180)
    plt.close(figure)
    figure, axis = plt.subplots(figsize=(7, 5), constrained_layout=True)
    axis.scatter(values[:, 0], values[:, 1], s=4, c="m")
    axis.set(xlabel="x [m]", ylabel="xp", title="Horizontal phase space (zoom)")
    axis.grid(True, alpha=0.3)
    zoom = output_dir / "poincare_x_xp_zoom.png"
    figure.savefig(zoom, dpi=180)
    plt.close(figure)
    return full, zoom
