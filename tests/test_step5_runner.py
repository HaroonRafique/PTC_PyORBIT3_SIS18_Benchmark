from step_05_phase_space_island.run_phase_space_island import phase_space_limits, reference_launch_extent_sigma


def test_step_5_keeps_the_legacy_four_sigma_horizontal_scan():
    assert reference_launch_extent_sigma(particles=16) == 3.75


def test_step_5_uses_the_reference_physical_phase_space_window():
    assert phase_space_limits() == ((-50.0, 50.0), (-5.0, 5.0))
