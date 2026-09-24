from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from step_05_phase_space_island import run_phase_space_island
from step_05_phase_space_island.run_phase_space_island import phase_space_limits, reference_launch_extent_sigma


def test_step_5_keeps_the_legacy_four_sigma_horizontal_scan():
    assert reference_launch_extent_sigma(particles=16) == 3.75


def test_step_5_uses_the_reference_physical_phase_space_window():
    assert phase_space_limits() == ((-50.0, 50.0), (-5.0, 5.0))


def test_step_5_plot_only_rebuilds_website_comparison_from_saved_trajectory(tmp_path: Path, monkeypatch):
    output = tmp_path / "output"
    trajectory = output / "trajectories" / "poincare_turn_by_particle.npz"
    trajectory.parent.mkdir(parents=True)
    (output / "manifest.json").write_text("{}\n", encoding="utf-8")
    snapshots = np.zeros((2, 1, 6))
    snapshots[1, 0, :2] = (0.01, 0.001)
    np.savez_compressed(trajectory, coordinates=snapshots)
    reference = tmp_path / "reference" / "Step5" / "output"
    reference.mkdir(parents=True)
    for name in ("Poincare_Dist_SIS18_Step5.png", "Poincare_Dist_SIS18_Step5_zoom.png"):
        plt.imsave(reference / name, [[0.0, 1.0], [1.0, 0.0]])

    monkeypatch.setattr(run_phase_space_island, "prepare_pyorbit3_runtime", lambda *_: (_ for _ in ()).throw(AssertionError("tracking runtime must not start")))

    assert run_phase_space_island.main(["--plot-only", "--output-dir", str(output), "--reference-root", str(reference.parents[1])]) == 0
    assert (output / "plots" / "website_vs_current_horizontal_phase_space.png").is_file()
