from pathlib import Path

import numpy as np

from common.trapping_diagnostics import (
    horizontal_action,
    legacy_particle_records,
    single_particle_coordinates,
    trajectory_comparison,
    single_particle_coordinates_at,
)


def test_published_single_particle_launch_is_five_mm_at_two_point_five_sigma_z():
    coordinates = single_particle_coordinates(launch="reference", bunch_length_rms_m=40.206868)

    np.testing.assert_allclose(coordinates, [0.005, 0.0, 0.0, 0.0, 100.51717, 0.0])


def test_legacy_artifact_single_particle_launch_preserves_zero_x():
    coordinates = single_particle_coordinates(launch="legacy_artifact", bunch_length_rms_m=40.206868)

    np.testing.assert_allclose(coordinates, [0.0, 0.0, 0.0, 0.0, 100.51717, 0.0])


def test_single_particle_coordinates_accept_the_exact_historical_launch_position():
    coordinates = single_particle_coordinates_at(x_m=0.0051, bunch_length_rms_m=2.680419244)

    np.testing.assert_allclose(coordinates, [0.0051, 0.0, 0.0, 0.0, 6.70104811, 0.0])


def test_horizontal_action_uses_the_historical_twiss_constants():
    assert np.isclose(horizontal_action(0.005, 0.0), 0.005**2 * (1.0 + 1.283306757**2) / 12.79426135)


def test_legacy_particle_records_parse_the_historical_tabular_format(tmp_path: Path):
    path = tmp_path / "Particles_all.dat"
    path.write_text(
        "#ParticleID\tTurn\tx[m]\txp\ty[m]\typ\tz[m]\tdE[GeV]\n"
        "0\t-1\t0.000000\t0.000000\t0.000000\t0.000000\t100.517169\t0.000000\n",
        encoding="utf-8",
    )

    records = legacy_particle_records(path)

    assert records.shape == (1, 7)
    np.testing.assert_allclose(records[0], [-1.0, 0.0, 0.0, 0.0, 0.0, 100.517169, 0.0])


def test_trajectory_comparison_uses_historical_six_decimal_precision():
    reference = np.array([[-1.0, 0.0, 0.0, 0.0, 0.0, 100.517169, 0.0]])
    candidate = reference.copy()
    candidate[0, 5] += 4.0e-7

    result = trajectory_comparison(reference, candidate)

    assert result["agreement"] is True
    assert result["samples"] == 1
