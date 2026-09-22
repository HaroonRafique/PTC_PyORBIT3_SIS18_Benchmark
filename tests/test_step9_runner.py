import numpy as np
from pathlib import Path

from common.madx import set_madx_bare_tunes
from common.mpi import MPIContext, local_count_for_rank, local_counts_for_size
from common.bunch_generation import MatchedGaussianConfig, make_configured_particle_bunch
from step_09_bunch_emittance_evolution.run_bunch_emittance_evolution import (
    MULTICODE_CURRENT_COLOR,
    MULTICODE_LEGACY_COLOR,
    MULTICODE_TITLE,
    normalised_emittance_history,
    plot_multicode_overlay_side_by_side,
    resolved_payload,
    sampled_turns,
)


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
    assert payload["profiles"]["reference"]["qx"] == 4.3604


def test_step_9_multicode_comparison_reconstructs_the_historical_pyorbit_curve_on_the_raw_axes(tmp_path):
    from common.sis18_plots import plt

    historical_overlay = tmp_path / "historical_overlay.png"
    historical_background = tmp_path / "historical_background.png"
    plt.imsave(historical_overlay, np.full((12, 12, 3), 0.8))
    plt.imsave(historical_background, np.full((12, 12, 3), 0.9))

    output = plot_multicode_overlay_side_by_side(
        legacy_overlay=historical_overlay,
        historical_background=historical_background,
        legacy_turns=np.array([0.0, 50_000.0, 100_000.0]),
        legacy_epsn_x=np.array([1.0, 1.5, 2.0]),
        current_turns=np.array([0.0, 50_000.0, 100_000.0]),
        current_epsn_x=np.array([1.0, 1.5, 2.0]),
        output=tmp_path / "comparison.png",
    )

    assert output.is_file()
    assert plt.imread(output).shape[1] > plt.imread(output).shape[0]


def test_step_9_multicode_current_curve_uses_a_colour_not_in_the_historical_overlay():
    assert MULTICODE_CURRENT_COLOR == "#FF00FF"


def test_step_9_multicode_comparison_uses_the_requested_title_and_bright_legacy_blue():
    assert MULTICODE_TITLE == "SIS18 Benchmark Step 9"
    assert MULTICODE_LEGACY_COLOR == "#00A6FF"


def test_examples_style_mpi_partition_preserves_global_particle_count():
    counts = local_counts_for_size(global_count=1_000, size=4)
    context = MPIContext(comm=None, rank=3, size=4, enabled=False)

    assert counts == [250, 250, 250, 250]
    assert sum(counts) == 1_000
    assert local_count_for_rank(1_000, context) == 250


def test_examples_style_gaussian_bunch_applies_step9_longitudinal_five_sigma_cut():
    class Start:
        alpha_x = 1.2
        beta_x = 12.0
        alpha_y = -0.4
        beta_y = 15.0
        disp_x = 0.7
        disp_px = 0.03
        disp_y = 0.0
        disp_py = 0.0
        orbit_x = orbit_px = orbit_y = orbit_py = 0.0

    config = MatchedGaussianConfig(
        n_macroparticles=128,
        seed=20260909,
        eps_x_rms=4.91e-7 / (0.15448 * 1.012149995),
        eps_y_rms=3.635e-7 / (0.15448 * 1.012149995),
        z_rms=2.680419244,
        dE_rms=(2.5e-4 / 3.0) * 1.012149995 * 0.9382720813 * 0.15448**2,
        longitudinal_cut_sigma=5.0,
    )

    values = make_configured_particle_bunch(Start(), config).to_numpy()

    assert np.max(np.abs(values[:, 4])) < 5.0 * config.z_rms
    assert np.max(np.abs(values[:, 5])) < 5.0 * config.dE_rms


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


def test_step_9_wrapper_uses_examples_style_mpi_launcher():
    wrapper = Path(__file__).resolve().parents[1] / "step_09_bunch_emittance_evolution" / "run_example.sh"
    text = wrapper.read_text(encoding="utf-8")

    assert "MPI_LAUNCHER" in text
    assert "MPI_PROCS" in text
    assert "run_example.rank" in text
