from pathlib import Path

from common.sis18_plots import CURRENT_LINE_MARKER_SIZE, layered_overlay_style, plot_sampled_series


def test_plot_sampled_series_writes_requested_png(tmp_path: Path):
    output = plot_sampled_series([0, 1], [0.2, 0.3], xlabel="turn", ylabel="tune", output=tmp_path / "plot.png")

    assert output.is_file()
    assert output.stat().st_size > 0
    assert CURRENT_LINE_MARKER_SIZE == 1.75


def test_layered_overlay_styles_use_distinct_markers_with_descending_sizes():
    bottom, middle, top = (layered_overlay_style(layer) for layer in range(3))

    assert [bottom["marker"], middle["marker"], top["marker"]] == ["o", "x", "s"]
    assert bottom["s"] > middle["s"] > top["s"]
    assert bottom["s"] >= 2 * middle["s"]
    assert middle["s"] >= 2 * top["s"]
    assert bottom["zorder"] < middle["zorder"] < top["zorder"]
