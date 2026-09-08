from pathlib import Path

import matplotlib.pyplot as plt

from common.legacy_plot_comparison import plot_legacy_comparison


def test_plot_legacy_comparison_writes_side_by_side_panel(tmp_path: Path):
    legacy = tmp_path / "legacy.png"
    current = tmp_path / "current.png"
    plt.imsave(legacy, [[0.0, 1.0], [1.0, 0.0]])
    plt.imsave(current, [[1.0, 0.0], [0.0, 1.0]])

    output = plot_legacy_comparison(legacy, current, tmp_path / "comparison.png", title="Step 1")

    assert output.is_file()
