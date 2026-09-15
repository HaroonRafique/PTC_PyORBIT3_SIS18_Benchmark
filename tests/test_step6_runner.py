from step_06_slow_trapping.run_slow_trapping import action_plot_limits, observation_turns


def test_step_6_action_plot_matches_the_public_synchrotron_window():
    assert action_plot_limits() == ((0.0, 1.0), (0.0, 17.0))


def test_step_6_tracks_the_historical_pretracking_and_final_turn_records():
    assert observation_turns(turns=64).tolist() == [-1, *range(64)]
