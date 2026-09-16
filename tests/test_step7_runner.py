from step_07_fast_trapping.run_fast_trapping import public_action_plot_limits, public_action_records


def test_step_7_public_action_plot_uses_the_first_synchrotron_oscillation_window():
    assert public_action_plot_limits() == ((0.0, 1000.0), (0.9, 1.6))


def test_step_7_public_action_records_exclude_the_second_oscillation():
    assert public_action_records(turns=2000).tolist() == list(range(1000))
