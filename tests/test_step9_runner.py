import numpy as np

from common.bunch_distribution import matched_gaussian_coordinates
from common.madx import set_madx_bare_tunes
from step_09_bunch_emittance_evolution.run_bunch_emittance_evolution import (
    normalised_emittance_history,
    resolved_payload,
    sampled_turns,
)


def test_seeded_matched_gaussian_is_reproducible_and_respects_transverse_cut():
    parameters = dict(
        n_particles=32,
        seed=20260909,
        betax=12.0,
        alphax=1.2,
        betay=15.0,
        alphay=-0.4,
        etax=0.7,
        etapx=0.03,
        epsn_x=4.91e-7,
        epsn_y=3.635e-7,
        beta_rel=0.15448,
        gamma_rel=1.012149995,
        dpp_rms=2.5e-4 / 3.0,
        bunch_length_rms_m=2.680419244,
        particle_mass_GeV=0.9382720813,
        transverse_cut_sigma=5.0,
    )

    first = matched_gaussian_coordinates(**parameters)
    second = matched_gaussian_coordinates(**parameters)

    np.testing.assert_allclose(first, second)
    assert first.shape == (32, 6)
    assert np.all(np.isfinite(first))


def test_emittance_history_normalises_to_its_initial_sample_and_retains_final_turn():
    turns = sampled_turns(turns=250, stride=100)
    normalised = normalised_emittance_history(np.array([4.0, 6.0, 8.0]))

    assert turns.tolist() == [0, 100, 200, 250]
    np.testing.assert_allclose(normalised, [1.0, 1.5, 2.0])


def test_step_9_resolved_payload_includes_global_beam_settings():
    payload = resolved_payload(profile="smoke")

    assert payload["beam"]["epsn_x"] == 4.91e-7
    assert payload["diagnostics"]["sample_stride_turns"] == 100
    assert payload["profiles"]["reference"]["n_macroparticles"] == 1000


def test_step_9_staged_madx_tunes_are_replaced_from_the_selected_profile(tmp_path):
    madx = tmp_path / "SIS18.madx"
    madx.write_text(
        "CONSTRAINT, expr=  table(ptc_twiss_summary,Q1)= 0.3604;\n"
        "CONSTRAINT, expr=  table(ptc_twiss_summary,Q2)= 0.2;\n",
        encoding="utf-8",
    )

    set_madx_bare_tunes(madx, qx=4.3504, qy=3.2)

    assert "Q1)= 0.3504;" in madx.read_text(encoding="utf-8")
    assert "Q2)= 0.2;" in madx.read_text(encoding="utf-8")
