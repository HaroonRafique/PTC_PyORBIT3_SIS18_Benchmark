from step_04_tunes_resonance_crossing.run_tunes_resonance_crossing import plot_window, scan_sigma_limit


def test_step_4_uses_the_historical_symmetric_scan_limits():
    assert scan_sigma_limit("x") == 4.0
    assert scan_sigma_limit("y") == 4.0


def test_step_4_uses_the_historical_resonance_plot_windows():
    assert plot_window("x") == ((0.0, 6.0), (0.2325, 0.3505))
    assert plot_window("y") == ((0.0, 4.62), (0.05, 0.205))
