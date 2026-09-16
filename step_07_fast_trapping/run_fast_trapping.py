#!/usr/bin/env python
"""Run SIS18 Step 7: fast synchrotron scattering of one particle."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.environment import prepare_pyorbit3_runtime, resolve_runtime_paths
from common.legacy_plot_comparison import plot_legacy_comparison, plot_same_axes_references
from common.madx import generate_flat_file
from common.manifest import write_run_manifest
from common.reference_artifacts import maybe_reference_root, sha256_file, stage_packaged_inputs
from common.sis18_config import load_step_config
from common.sis18_lattice import in_workdir, load_sis18_lattice
from common.sis18_plots import BENCHMARK_COLORS, CURRENT_LINE_MARKER_SIZE, CURRENT_MARKER, plt
from common.trapping_diagnostics import horizontal_action, single_particle_coordinates_at

STEP_DIR = Path(__file__).resolve().parent
WEBSITE_REFERENCE_DIR = ROOT / "shared_inputs" / "reference_plots" / "step_07"
EPSN_X, EPSN_Y = 4.91e-7, 3.635e-7
DPP_RMS, BUNCH_LENGTH_RMS_M = 2.5e-4 / 3.0, 2.680419244
SC_PATH_LENGTH_MIN_M, LAUNCH_X_M = 1.0e-8, 5.1e-3


def public_action_plot_limits() -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the GSI first-synchrotron-oscillation action window."""

    return ((0.0, 1000.0), (0.9, 1.6))


def public_action_records(*, turns: int) -> np.ndarray:
    """Return turn indices shown by the public 1,000-turn comparison."""

    return np.arange(min(turns, 1000), dtype=int)


def _revision(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _install_historical_model(lattice, config):
    from orbit.aperture import TeapotApertureNode
    from orbit.core.spacecharge import GaussianLineDensityProfile, SpaceChargeCalcAnalyticGaussian
    from orbit.space_charge.analytical import setSCanalyticalAccNodes

    position = 0.0
    for node in lattice.getNodes():
        aperture = TeapotApertureNode(1, 10.0, 10.0, position)
        node.addChildNode(aperture, node.ENTRANCE)
        node.addChildNode(aperture, node.BODY)
        node.addChildNode(aperture, node.EXIT)
        position += node.getLength()
    calculator = SpaceChargeCalcAnalyticGaussian(config.intensity, EPSN_X, EPSN_Y, DPP_RMS, GaussianLineDensityProfile(BUNCH_LENGTH_RMS_M))
    return setSCanalyticalAccNodes(lattice, SC_PATH_LENGTH_MIN_M, calculator)


def _apply_restoring_force(bunch, force: float) -> None:
    for index in range(bunch.getSize()):
        bunch.dE(index, bunch.dE(index) + bunch.z(index) * force)


def _record(turn: int, bunch) -> np.ndarray:
    if bunch.getSize() != 1:
        return np.asarray((turn, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan))
    return np.asarray((turn, bunch.x(0), bunch.xp(0), bunch.y(0), bunch.yp(0), bunch.z(0), bunch.dE(0)))


def _run(*, flat: Path, inputs: Path, config, turns: int):
    lattice, bunch = load_sis18_lattice(flat)
    from ext.ptc_orbit.ptc_orbit import readScriptPTC

    with in_workdir(inputs / "Input"):
        readScriptPTC("time.ptc")
    sc_nodes = _install_historical_model(lattice, config)
    bunch.addPartAttr("macrosize")
    bunch.addPartAttr("ParticleIdNumber")
    bunch.addParticle(*single_particle_coordinates_at(x_m=LAUNCH_X_M, bunch_length_rms_m=BUNCH_LENGTH_RMS_M))
    bunch.partAttrValue("macrosize", 0, 0, config.intensity)
    bunch.partAttrValue("ParticleIdNumber", 0, 0, 0)
    from orbit.core.bunch import Bunch

    lostbunch = Bunch(); bunch.copyEmptyBunchTo(lostbunch)
    lostbunch.addPartAttr("ParticlePhaseAttributes"); lostbunch.addPartAttr("LostParticleAttributes")
    parameters = {"bunch": bunch, "lostbunch": lostbunch, "length": lattice.getLength() / lattice.nHarm}
    records, first_lost_turn = [_record(-1, bunch)], -1
    for turn in range(turns):
        lattice.trackBunch(bunch, parameters)
        _apply_restoring_force(bunch, config.restoring_force)
        records.append(_record(turn, bunch))
        if bunch.getSize() == 0 and first_lost_turn < 0:
            first_lost_turn = turn
    return np.asarray(records), {"nodes": lattice.nNodes, "length_m": lattice.getLength(), "sc_nodes": len(sc_nodes), "survivors": bunch.getSize(), "first_lost_turn": first_lost_turn}


def _normalised_action(records: np.ndarray) -> np.ndarray:
    action = horizontal_action(records[:, 1], records[:, 2])
    finite_positive = action[np.isfinite(action) & (action > 0.0)]
    return action / finite_positive[0] if len(finite_positive) else np.full(len(action), np.nan)


def _plot_action(path: Path, records: np.ndarray, *, public: bool) -> Path:
    plotted = records[(records[:, 0] >= 0) & (records[:, 0] < 1000)] if public else records
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.plot(plotted[:, 0], _normalised_action(plotted), color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER, markersize=CURRENT_LINE_MARKER_SIZE, linewidth=1.0)
    axis.set(xlabel="turns", ylabel=r"$\epsilon_x / \epsilon_{x0}$")
    if public:
        xlim, ylim = public_action_plot_limits(); axis.set(xlim=xlim, ylim=ylim)
    axis.set_box_aspect(1); axis.grid(True, alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _plot_series(path: Path, records: np.ndarray) -> Path:
    figure, axis = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    axis.plot(records[:, 0], records[:, 5], color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER, markersize=CURRENT_LINE_MARKER_SIZE, linewidth=1.0)
    axis.set(xlabel="turn [-]", ylabel="z [m]"); axis.grid(True, alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _plot_phase_space(path: Path, records: np.ndarray, *, longitudinal: bool) -> Path:
    x_index, y_index = (5, 6) if longitudinal else (1, 2)
    x_scale, y_scale = (1.0, 1.0) if longitudinal else (1000.0, 1000.0)
    xlabel, ylabel = ("z [m]", "dE [GeV]") if longitudinal else ("x [mm]", "xp [mrad]")
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.scatter(records[:, x_index] * x_scale, records[:, y_index] * y_scale, color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER, s=8.0)
    axis.set(xlabel=xlabel, ylabel=ylabel); axis.set_box_aspect(1); axis.grid(True, alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _write_records(path: Path, records: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    action, normalised = horizontal_action(records[:, 1], records[:, 2]), _normalised_action(records)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(("turn", "x_m", "xp_rad", "y_m", "yp_rad", "z_m", "dE_GeV", "action_x", "action_x_normalised"))
        for row, action_value, normalised_value in zip(records, action, normalised): writer.writerow((*row, action_value, normalised_value))
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "reference"), default="smoke"); parser.add_argument("--turns", type=int)
    parser.add_argument("--output-dir", type=Path, default=STEP_DIR / "output"); parser.add_argument("--reference-root", type=Path)
    parser.add_argument("--skip-reference-comparison", action="store_true"); parser.add_argument("--madx", type=Path)
    args = parser.parse_args(argv); config = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=7, profile=args.profile); turns = args.turns or config.turns
    if turns < 1: raise ValueError("Step 7 requires at least one turn")
    output, inputs = args.output_dir.resolve(), STEP_DIR / "input" / "generated" / args.profile / "madx"
    paths = resolve_runtime_paths(madx=args.madx or Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00"))
    staged = stage_packaged_inputs(source=STEP_DIR / "legacy_input", destination=inputs / "Input")
    flat = generate_flat_file(madx=paths.madx, workdir=inputs, madx_input=inputs / "Input" / "SIS18.madx")
    prepare_pyorbit3_runtime(paths, Path("/tmp/sis18_ptc_runtime"))
    records, summary = _run(flat=flat, inputs=inputs, config=config, turns=turns)
    plots, tables, trajectories = output / "plots", output / "tables", output / "trajectories"; trajectories.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(trajectories / "single_particle_turn_records.npz", records=records)
    diagnostics = _write_records(tables / "turn_diagnostics.csv", records)
    current = {"action": _plot_action(plots / "action_x_vs_turn.png", records, public=False), "public_action": _plot_action(plots / "action_x_vs_first_synchrotron_oscillation.png", records, public=True), "z": _plot_series(plots / "z_vs_turn.png", records), "x_xp": _plot_phase_space(plots / "poincare_x_xp.png", records, longitudinal=False), "z_dE": _plot_phase_space(plots / "poincare_z_dE.png", records, longitudinal=True)}
    reference = maybe_reference_root(args.reference_root, comparison_enabled=not args.skip_reference_comparison)
    reference_artifacts: dict[str, str] = {}; generated_plots = [str(path) for path in current.values()]
    comparison = {"mode": "visual_only", "expected_regime": "fast synchrotron scattering; no adiabatic trapping"}
    if reference is not None:
        reference_output = reference / "Step7" / "output"
        legacy_images = {"action": reference_output / "Particle_trapping_1000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png", "z": reference_output / "Particle_trapping_z_1000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png", "x_xp": reference_output / "Poincare_x_xp_1000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png", "z_dE": reference_output / "Poincare_z_dE_1000synch_F=-4.38975e-09_5.0.5mm_1E5turns_SC_Manual.png"}
        for observable, legacy_image in legacy_images.items(): generated_plots.append(str(plot_legacy_comparison(legacy_image, current[observable], plots / f"legacy_vs_current_{observable}_side_by_side.png", title=f"SIS18 Step 7 {observable}")))
        reference_artifacts = {str(path): sha256_file(path) for path in legacy_images.values()}
        website_manifest = json.loads((WEBSITE_REFERENCE_DIR / "reference_manifest.json").read_text(encoding="utf-8"))
        website_references = [(entry["label"], WEBSITE_REFERENCE_DIR / entry["file"]) for entry in website_manifest["plots"]] + [("PTC-PyORBIT2", legacy_images["action"])]
        generated_plots.append(str(plot_same_axes_references(current=current["public_action"], references=website_references, output=plots / "website_vs_current_action_same_axes.png")))
        reference_artifacts.update({entry["file"]: sha256_file(WEBSITE_REFERENCE_DIR / entry["file"]) for entry in website_manifest["plots"]})
    (output / "comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "comparison.md").write_text("# Step 7 comparison\n\n- Visual-only: the GSI reference identifies fast synchrotron scattering, not adiabatic trapping.\n- The legacy archive has no numeric trajectory table.\n", encoding="utf-8")
    (output / "tracking_summary.json").write_text(json.dumps({**summary, "turns": turns, "launch_x_m": LAUNCH_X_M}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = write_run_manifest(output / "manifest.json", {"step": 7, "profile": args.profile, "command": sys.argv, "turns": turns, "mpi_size": 1, "seed": config.seed, "flat_file": str(flat), "flat_file_sha256": sha256_file(flat), "packaged_inputs": {path.name: sha256_file(path) for path in staged}, "reference_artifacts": reference_artifacts, "comparison_enabled": reference is not None, "comparison": comparison, "lattice": summary, "space_charge": "analytical_frozen_gaussian", "sextupole_enabled": True, "code_revisions": {"benchmark": _revision(ROOT), "pyorbit3": _revision(paths.pyorbit3_root), "ptc": _revision(paths.pyorbit3_root.parent / "PTC")}, "plots": generated_plots, "diagnostics": str(diagnostics)})
    print(f"Step 7 {args.profile} complete: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
