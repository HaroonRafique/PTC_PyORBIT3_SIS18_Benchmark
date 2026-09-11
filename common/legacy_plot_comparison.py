"""Read-only visual comparisons against external legacy benchmark plots."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from .sis18_plots import plt


def plot_legacy_comparison(legacy: Path, current: Path, output: Path, *, title: str) -> Path:
    """Write a labelled legacy/current side-by-side PNG without copying inputs."""

    return plot_labeled_comparison(
        legacy,
        current,
        output,
        title=title,
        left_label="Legacy PTC-PyORBIT",
        right_label="PTC-PyORBIT3",
    )


def plot_labeled_comparison(
    left: Path, right: Path, output: Path, *, title: str, left_label: str, right_label: str
) -> Path:
    """Write a labelled two-panel visual comparison without copying inputs."""

    if not left.is_file():
        raise FileNotFoundError(f"Left comparison plot is missing: {left}")
    if not right.is_file():
        raise FileNotFoundError(f"Right comparison plot is missing: {right}")
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(14, 7), constrained_layout=True)
    for axis, image, label in ((axes[0], left, left_label), (axes[1], right, right_label)):
        axis.imshow(plt.imread(image))
        axis.set(title=label)
        axis.axis("off")
    figure.suptitle(title)
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output


def plot_same_axes_references(
    *, current: Path, references: Sequence[tuple[str, Path]], output: Path
) -> Path:
    """Write a compact horizontal-only panel of reference plots and current output."""

    panels = [*references, ("PTC-PyORBIT3", current)]
    missing = [str(path) for _, path in panels if not path.is_file()]
    if missing:
        raise FileNotFoundError("Reference comparison plot is missing: " + ", ".join(missing))
    output.parent.mkdir(parents=True, exist_ok=True)
    rows, columns = comparison_grid_shape(len(panels))
    figure, axes = plt.subplots(rows, columns, figsize=(4 * columns, 4 * rows), constrained_layout=True, squeeze=False)
    for axis, (label, image) in zip(axes.flat, panels):
        axis.imshow(plt.imread(image))
        axis.set(title=label)
        axis.axis("off")
    for axis in list(axes.flat)[len(panels) :]:
        axis.axis("off")
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output


def comparison_grid_shape(panel_count: int) -> tuple[int, int]:
    """Return a compact near-square grid for a positive number of panels."""

    if panel_count < 1:
        raise ValueError("panel_count must be positive")
    columns = math.ceil(math.sqrt(panel_count))
    return math.ceil(panel_count / columns), columns
