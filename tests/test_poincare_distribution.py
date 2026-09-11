import numpy as np

from common.poincare_distribution import amplitude_scan_coordinates, dominant_fft_tune, horizontal_poincare_coordinates


def test_horizontal_poincare_coordinates_match_legacy_i_over_n_scan():
    coordinates = horizontal_poincare_coordinates(
        n_particles=4, n_sigma=6.42, betax=10.0, epsn_x=4.91e-7, beta_rel=0.15448, gamma_rel=1.01215
    )

    sigma_x = np.sqrt(10.0 * 4.91e-7 / (0.15448 * 1.01215))
    assert coordinates.shape == (4, 6)
    assert np.allclose(coordinates[:, 0], [0.0, 1.605 * sigma_x, 3.21 * sigma_x, 4.815 * sigma_x])
    assert np.allclose(coordinates[:, 1:], 0.0)


def test_vertical_amplitude_scan_populates_only_y_coordinates():
    coordinates = amplitude_scan_coordinates(
        plane="y", n_particles=4, n_sigma=4.0, betax=10.0, betay=16.0, epsn_x=2.0, epsn_y=3.0, beta_rel=1.0, gamma_rel=1.0
    )

    assert np.allclose(coordinates[:, 2], [0.0, np.sqrt(48.0), 2 * np.sqrt(48.0), 3 * np.sqrt(48.0)])
    assert np.allclose(coordinates[:, [0, 1, 3, 4, 5]], 0.0)


def test_plain_fft_reports_the_dominant_fractional_tune():
    turns = np.arange(1024)

    assert dominant_fft_tune(np.cos(2 * np.pi * 0.25 * turns)) == 0.25
