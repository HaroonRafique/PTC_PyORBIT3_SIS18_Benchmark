import numpy as np

from step_03_tunes_with_sextupole.run_tunes_with_sextupole import scan_sigma_limit, surviving_particle_ids


def test_step_3_uses_the_historical_unequal_scan_limits():
    assert scan_sigma_limit("x") == 3.3
    assert scan_sigma_limit("y") == 4.0


def test_step_3_rejects_an_unknown_scan_plane():
    try:
        scan_sigma_limit("z")
    except ValueError as error:
        assert "plane" in str(error)
    else:
        raise AssertionError("unknown plane should be rejected")


def test_step_3_derives_survivors_from_an_id_indexed_snapshot():
    snapshot = np.array([[0.0, 0, 0, 0, 0, 0], [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan], [1.0, 0, 0, 0, 0, 0]])

    assert surviving_particle_ids(snapshot) == {0, 2}
