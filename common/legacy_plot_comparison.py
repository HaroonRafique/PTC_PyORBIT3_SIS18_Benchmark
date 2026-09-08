"""Read-only visual comparisons against external legacy benchmark plots."""

from __future__ import annotations

from pathlib import Path

from .sis18_plots import plt


def plot_legacy_comparison(legacy: Path, current: Path, output: Path, *, title: str) -> Path:
    """Write a labelled legacy/current side-by-side PNG without copying inputs."""

    if not legacy.is_file():
        raise FileNotFoundError(f"Legacy comparison plot is missing: {legacy}")
    if not current.is_file():
        raise FileNotFoundError(f"Current comparison plot is missing: {current}")
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(14, 7), constrained_layout=True)
    for axis, image, label in ((axes[0], legacy, "Legacy PTC-PyORBIT"), (axes[1], current, "PTC-PyORBIT3")):
        axis.imshow(plt.imread(image))
        axis.set(title=label)
        axis.axis("off")
    figure.suptitle(title)
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output
