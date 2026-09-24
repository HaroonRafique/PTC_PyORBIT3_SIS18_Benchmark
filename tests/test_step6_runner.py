from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from step_06_slow_trapping import run_slow_trapping
from step_06_slow_trapping.run_slow_trapping import action_plot_limits, observation_turns


def test_step_6_action_plot_matches_the_public_synchrotron_window():
    assert action_plot_limits() == ((0.0, 1.0), (0.0, 17.0))


def test_step_6_tracks_the_historical_pretracking_and_final_turn_records():
    assert observation_turns(turns=64).tolist() == [-1, *range(64)]


def test_step_6_plot_only_rebuilds_website_and_slide_comparisons_from_saved_records(tmp_path: Path, monkeypatch):
    output = tmp_path / "output"
    trajectory = output / "trajectories" / "single_particle_turn_records.npz"
    trajectory.parent.mkdir(parents=True)
    (output / "manifest.json").write_text("{}\n", encoding="utf-8")
    records = np.asarray(((-1, 0.005, 0.0, 0.0, 0.0, 100.0, 0.0), (0, 0.0051, 0.0001, 0.0, 0.0, 99.0, 0.0)))
    np.savez_compressed(trajectory, records=records)
    reference = tmp_path / "reference" / "Step6" / "output"
    reference.mkdir(parents=True)
    for name in (
        "Particle_trapping_15000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png",
        "Particle_trapping_z_15000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png",
        "Poincare_x_xp_15000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png",
        "Poincare_z_dE_15000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png",
    ):
        plt.imsave(reference / name, [[0.0, 1.0], [1.0, 0.0]])

    monkeypatch.setattr(run_slow_trapping, "prepare_pyorbit3_runtime", lambda *_: (_ for _ in ()).throw(AssertionError("tracking runtime must not start")))

    assert run_slow_trapping.main(["--plot-only", "--profile", "reference", "--output-dir", str(output), "--reference-root", str(reference.parents[1])]) == 0
    assert (output / "plots" / "website_vs_current_action_same_axes.png").is_file()
    assert (output / "plots" / "website_slide_vs_current_action.png").is_file()
