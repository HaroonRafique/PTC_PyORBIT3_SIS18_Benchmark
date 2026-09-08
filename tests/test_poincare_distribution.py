import numpy as np

from common.poincare_distribution import horizontal_poincare_coordinates


def test_horizontal_poincare_coordinates_match_legacy_i_over_n_scan():
    coordinates = horizontal_poincare_coordinates(
        n_particles=4, n_sigma=6.42, betax=10.0, epsn_x=4.91e-7, beta_rel=0.15448, gamma_rel=1.01215
    )

    sigma_x = np.sqrt(10.0 * 4.91e-7 / (0.15448 * 1.01215))
    assert coordinates.shape == (4, 6)
    assert np.allclose(coordinates[:, 0], [0.0, 1.605 * sigma_x, 3.21 * sigma_x, 4.815 * sigma_x])
    assert np.allclose(coordinates[:, 1:], 0.0)
