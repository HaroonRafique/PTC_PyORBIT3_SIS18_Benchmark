from pathlib import Path

import matplotlib.pyplot as plt

from common.legacy_plot_comparison import plot_legacy_comparison, plot_same_axes_references


def test_plot_legacy_comparison_writes_side_by_side_panel(tmp_path: Path):
    legacy = tmp_path / "legacy.png"
    current = tmp_path / "current.png"
    plt.imsave(legacy, [[0.0, 1.0], [1.0, 0.0]])
    plt.imsave(current, [[1.0, 0.0], [0.0, 1.0]])

    output = plot_legacy_comparison(legacy, current, tmp_path / "comparison.png", title="Step 1")

    assert output.is_file()


def test_same_axes_reference_plot_writes_only_requested_horizontal_panels(tmp_path: Path):
    current = tmp_path / "current.png"
    references = [("MICROMAP", tmp_path / "micromap.jpg"), ("ORBIT", tmp_path / "orbit.jpg")]
    plt.imsave(current, [[0.0, 1.0], [1.0, 0.0]])
    for _, path in references:
        plt.imsave(path, [[1.0, 0.0], [0.0, 1.0]])

    output = plot_same_axes_references(
        current=current,
        references=references,
        output=tmp_path / "website_horizontal_phase_space.png",
    )

    assert output.is_file()
