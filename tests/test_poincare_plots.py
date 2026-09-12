from pathlib import Path

import numpy as np
from PIL import Image

from common.poincare_plots import TRANSVERSE_ANGLE_SCALE, TRANSVERSE_POSITION_SCALE, plot_poincare_views
from common.sis18_plots import BENCHMARK_COLORS, CURRENT_MARKER, CURRENT_SCATTER_SIZE


def test_plot_poincare_views_writes_full_and_zoom(tmp_path: Path):
    snapshots = np.zeros((2, 3, 6))
    snapshots[:, :, 0] = [[0.0, 0.001, 0.002], [0.0, 0.0015, 0.0025]]
    full, zoom = plot_poincare_views(snapshots, tmp_path)

    assert full.is_file()
    assert zoom.is_file()


def test_poincare_views_use_the_explicit_current_colour_and_square_zoom(tmp_path: Path):
    snapshots = np.zeros((1, 2, 6))
    snapshots[0, :, 0] = [-0.05, 0.03]
    snapshots[0, :, 1] = [0.005, -0.006]

    _, zoom = plot_poincare_views(snapshots, tmp_path)

    assert BENCHMARK_COLORS["current"] == "#0072B2"
    assert CURRENT_MARKER == "x"
    assert CURRENT_SCATTER_SIZE == 2.0
    assert Image.open(zoom).size[0] == Image.open(zoom).size[1]


def test_poincare_zoom_reserves_a_left_margin_for_the_y_axis_label(tmp_path: Path):
    snapshots = np.zeros((1, 2, 6))
    snapshots[0, :, 0] = [-0.05, 0.03]
    snapshots[0, :, 1] = [0.005, -0.006]

    _, zoom = plot_poincare_views(snapshots, tmp_path)

    pixels = np.asarray(Image.open(zoom).convert("RGB"))
    assert np.all(pixels[:, :5] > 245)


def test_poincare_transverse_coordinates_use_mm_and_mrad():
    assert TRANSVERSE_POSITION_SCALE == 1000.0
    assert TRANSVERSE_ANGLE_SCALE == 1000.0


def test_poincare_views_accept_step_specific_horizontal_limits(tmp_path: Path):
    snapshots = np.zeros((1, 2, 6))
    snapshots[0, :, 0] = [-0.04, 0.03]
    snapshots[0, :, 1] = [0.004, -0.004]

    full, zoom = plot_poincare_views(snapshots, tmp_path, horizontal_limits=((-50.0, 50.0), (-5.0, 5.0)))

    assert full.is_file()
    assert zoom.is_file()
