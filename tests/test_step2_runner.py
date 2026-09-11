import numpy as np

from step_02_tunes_no_sextupole.run_tunes_no_sextupole import _write_table, absolute_tunes


def test_step_2_absolute_tunes_preserve_the_bare_tune_integer_part():
    assert np.allclose(absolute_tunes(4.338, np.array([0.2370312])), [4.2370312])
    assert np.allclose(absolute_tunes(3.2, np.array([0.06323432])), [3.06323432])


def test_step_2_writes_separate_pynaff_and_fft_tune_tables(tmp_path):
    table = _write_table(
        tmp_path / "tunes_x.csv",
        np.array([[0.0, 0.0], [0.04, 0.065], [0.08, 0.13]]),
        np.array([0.237, 0.238]),
        np.array([0.238, 0.239]),
        4.338,
    )

    assert table.is_file()
    assert (tmp_path / "tunes_x_pynaff.csv").is_file()
    assert (tmp_path / "tunes_x_fft.csv").is_file()
    assert "4.237" in table.read_text(encoding="utf-8")
