from step_03_tunes_with_sextupole.run_tunes_with_sextupole import scan_sigma_limit


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
