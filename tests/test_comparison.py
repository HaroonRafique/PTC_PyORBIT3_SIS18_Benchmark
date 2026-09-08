import numpy as np

from common.sis18_comparison import compare_tune_tables


def test_compare_tune_tables_interpolates_and_reports_residuals():
    reference = np.array([[0.0, 0.20], [1.0, 0.25], [2.0, 0.30]])
    candidate = np.array([[0.0, 0.21], [2.0, 0.31]])

    result = compare_tune_tables(reference, candidate)

    assert result.samples == 3
    assert result.max_abs_residual == 0.01
    assert result.rms_residual == 0.01
