from pathlib import Path

from common.sis18_plots import plot_sampled_series


def test_plot_sampled_series_writes_requested_png(tmp_path: Path):
    output = plot_sampled_series([0, 1], [0.2, 0.3], xlabel="turn", ylabel="tune", output=tmp_path / "plot.png")

    assert output.is_file()
    assert output.stat().st_size > 0
