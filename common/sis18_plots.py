"""Matplotlib helpers following the active examples sampled-line policy."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_sampled_series(
    x: Sequence[float], y: Sequence[float], *, xlabel: str, ylabel: str, output: Path, label: str | None = None
) -> Path:
    """Write a sampled line plot with visible markers to ``output``."""

    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    axis.plot(x, y, marker="o", markersize=3.5, linewidth=1.25, label=label)
    axis.set(xlabel=xlabel, ylabel=ylabel)
    axis.grid(True, alpha=0.3)
    if label:
        axis.legend()
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output
