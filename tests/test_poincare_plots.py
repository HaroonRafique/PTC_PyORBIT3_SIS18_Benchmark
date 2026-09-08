from pathlib import Path

import numpy as np

from common.poincare_plots import plot_poincare_views


def test_plot_poincare_views_writes_full_and_zoom(tmp_path: Path):
    snapshots = np.zeros((2, 3, 6))
    snapshots[:, :, 0] = [[0.0, 0.001, 0.002], [0.0, 0.0015, 0.0025]]
    full, zoom = plot_poincare_views(snapshots, tmp_path)

    assert full.is_file()
    assert zoom.is_file()
