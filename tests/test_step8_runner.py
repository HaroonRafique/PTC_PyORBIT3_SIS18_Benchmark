import numpy as np

from step_08_long_term_trapping.run_long_term_trapping import comparison_records, observation_turns


def test_step_8_records_the_initial_condition_and_every_tracked_turn():
    turns = observation_turns(turns=100_000)

    assert len(turns) == 100_001
    assert turns[:3].tolist() == [-1, 0, 1]
    assert turns[-1] == 99_999


def test_step_8_reference_comparison_uses_the_legacy_prefix_matching_its_turn_count():
    legacy_turns = observation_turns(turns=200_000)
    legacy_records = np.column_stack((legacy_turns, np.zeros((len(legacy_turns), 6))))

    compared = comparison_records(legacy_records, turns=100_000)

    assert len(compared) == 100_001
    assert compared[-1, 0] == 99_999
