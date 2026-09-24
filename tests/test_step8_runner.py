from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from step_08_long_term_trapping import run_long_term_trapping
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


def test_step_8_plot_only_rebuilds_the_website_slide_comparison_from_saved_records(tmp_path: Path, monkeypatch):
    output = tmp_path / "output"
    trajectory = output / "trajectories" / "single_particle_turn_records.npz"
    trajectory.parent.mkdir(parents=True)
    (output / "manifest.json").write_text("{}\n", encoding="utf-8")
    turns = 128
    records = np.column_stack((observation_turns(turns=turns), np.full(turns + 1, 0.005), np.zeros((turns + 1, 5))))
    np.savez_compressed(trajectory, records=records)
    reference = tmp_path / "reference" / "Step8" / "final_output"
    reference.mkdir(parents=True)
    legacy = np.column_stack((np.zeros(turns + 1), observation_turns(turns=turns), np.full(turns + 1, 0.005), np.zeros((turns + 1, 5))))
    np.savetxt(reference / "Particle_0.dat", legacy, fmt="%.6f")
    for name in ("Particle_trapping_SIS18_Step_8.png", "Particle_trapping_z_SIS18_Step_8.png", "Poincare_x_xp_SIS18_Step_8.png", "Poincare_z_dE_SIS18_Step_8.png"):
        plt.imsave(reference / name, [[0.0, 1.0], [1.0, 0.0]])

    monkeypatch.setattr(run_long_term_trapping, "prepare_pyorbit3_runtime", lambda *_: (_ for _ in ()).throw(AssertionError("tracking runtime must not start")))

    assert run_long_term_trapping.main(["--plot-only", "--profile", "smoke", "--output-dir", str(output), "--reference-root", str(reference.parents[1])]) == 0
    assert (output / "plots" / "website_vs_current_action_same_axes.png").is_file()
