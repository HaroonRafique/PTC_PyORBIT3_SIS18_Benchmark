#!/usr/bin/env python
"""Run SIS18 Step 8: long-term single-particle scattering and trapping."""

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
from common.legacy_plot_comparison import plot_labeled_comparison
from common.madx import generate_flat_file
from common.manifest import write_run_manifest
from common.reference_artifacts import maybe_reference_root, sha256_file, stage_packaged_inputs
from common.sis18_config import format_resolved_config, load_step_config
from common.sis18_lattice import in_workdir, load_sis18_lattice
from common.sis18_plots import BENCHMARK_COLORS, CURRENT_LINE_MARKER_SIZE, CURRENT_MARKER, layered_overlay_style, plt
from common.trapping_diagnostics import horizontal_action, legacy_particle_records, trajectory_comparison

STEP_DIR = Path(__file__).resolve().parent
WEBSITE_REFERENCE_DIR = ROOT / "shared_inputs" / "reference_plots" / "step_08"


def observation_turns(*, turns: int) -> np.ndarray:
    """Return the pre-tracking record followed by every tracked turn."""

    if turns < 1:
        raise ValueError("turns must be positive")
    return np.arange(-1, turns, dtype=int)


def comparison_records(records: np.ndarray, *, turns: int) -> np.ndarray:
    """Return the legacy record prefix corresponding to a configured run."""

    required = turns + 1
    if len(records) < required:
        raise ValueError(f"legacy trajectory has {len(records)} records; {required} required")
    selected = np.asarray(records[:required])
    if not np.array_equal(selected[:, 0], observation_turns(turns=turns)):
        raise ValueError("legacy trajectory does not contain the expected initial/turn grid")
    return selected


def _revision(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _install_historical_model(lattice, config, payload: dict[str, object]) -> int:
    from orbit.aperture import TeapotApertureNode
    from orbit.core.spacecharge import GaussianLineDensityProfile, SpaceChargeCalcAnalyticGaussian
    from orbit.space_charge.analytical import setSCanalyticalAccNodes

    beam, physics, longitudinal = payload["beam"], payload["physics"], payload["longitudinal"]
    position = 0.0
    for node in lattice.getNodes():
        aperture = TeapotApertureNode(1, physics["aperture_m"], physics["aperture_m"], position)
        node.addChildNode(aperture, node.ENTRANCE)
        node.addChildNode(aperture, node.BODY)
        node.addChildNode(aperture, node.EXIT)
        position += node.getLength()
    calculator = SpaceChargeCalcAnalyticGaussian(
        config.intensity, beam["epsn_x"], beam["epsn_y"], beam["dpp_rms"], GaussianLineDensityProfile(longitudinal["bunch_length_rms_m"])
    )
    return len(setSCanalyticalAccNodes(lattice, physics["sc_path_length_min_m"], calculator))


def _apply_restoring_force(bunch, force: float) -> None:
    for index in range(bunch.getSize()):
        bunch.dE(index, bunch.dE(index) + bunch.z(index) * force)


def _record(turn: int, bunch) -> np.ndarray:
    if bunch.getSize() != 1:
        return np.asarray((turn, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan))
    return np.asarray((turn, bunch.x(0), bunch.xp(0), bunch.y(0), bunch.yp(0), bunch.z(0), bunch.dE(0)))


def _run(*, flat: Path, inputs: Path, config, payload: dict[str, object], coordinates: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    lattice, bunch = load_sis18_lattice(flat)
    from ext.ptc_orbit.ptc_orbit import readScriptPTC

    with in_workdir(inputs / "Input"):
        readScriptPTC("time.ptc")
    sc_nodes = _install_historical_model(lattice, config, payload)
    bunch.addPartAttr("macrosize")
    bunch.addPartAttr("ParticleIdNumber")
    bunch.addParticle(*coordinates)
    bunch.partAttrValue("macrosize", 0, 0, config.intensity)
    bunch.partAttrValue("ParticleIdNumber", 0, 0, 0)
    from orbit.core.bunch import Bunch

    lostbunch = Bunch()
    bunch.copyEmptyBunchTo(lostbunch)
    lostbunch.addPartAttr("ParticlePhaseAttributes")
    lostbunch.addPartAttr("LostParticleAttributes")
    parameters = {"bunch": bunch, "lostbunch": lostbunch, "length": lattice.getLength() / lattice.nHarm}
    records, first_lost_turn = [_record(-1, bunch)], -1
    for turn in range(config.turns):
        lattice.trackBunch(bunch, parameters)
        _apply_restoring_force(bunch, config.restoring_force)
        records.append(_record(turn, bunch))
        if bunch.getSize() == 0 and first_lost_turn < 0:
            first_lost_turn = turn
    return np.asarray(records), {"nodes": lattice.nNodes, "length_m": lattice.getLength(), "sc_nodes": sc_nodes, "survivors": bunch.getSize(), "first_lost_turn": first_lost_turn}


def _normalised_action(records: np.ndarray) -> np.ndarray:
    action = horizontal_action(records[:, 1], records[:, 2])
    finite_positive = action[np.isfinite(action) & (action > 0.0)]
    return action / finite_positive[0] if len(finite_positive) else np.full(len(action), np.nan)


def _sample_indices(length: int, stride: int) -> np.ndarray:
    return np.unique(np.append(np.arange(0, length, stride, dtype=int), length - 1))


def _plot_action(path: Path, records: np.ndarray, *, period_turns: int, stride: int) -> Path:
    indices = _sample_indices(len(records), stride)
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.plot(records[indices, 0] / period_turns, _normalised_action(records)[indices], color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER, markersize=CURRENT_LINE_MARKER_SIZE, linewidth=1.0)
    axis.set(xlabel="synchrotron oscillations", ylabel=r"$\epsilon_x / \epsilon_{x0}$")
    axis.set_box_aspect(1); axis.grid(True, alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _plot_series(path: Path, records: np.ndarray, *, stride: int) -> Path:
    indices = _sample_indices(len(records), stride)
    figure, axis = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    axis.plot(records[indices, 0], records[indices, 5], color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER, markersize=CURRENT_LINE_MARKER_SIZE, linewidth=1.0)
    axis.set(xlabel="turn [-]", ylabel="z [m]"); axis.grid(True, alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _plot_phase_space(path: Path, records: np.ndarray, *, longitudinal: bool, stride: int) -> Path:
    indices = _sample_indices(len(records), stride)
    x_index, y_index = (5, 6) if longitudinal else (1, 2)
    x_scale, y_scale = (1.0, 1.0) if longitudinal else (1000.0, 1000.0)
    xlabel, ylabel = ("z [m]", "dE [GeV]") if longitudinal else ("x [mm]", "xp [mrad]")
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.scatter(records[indices, x_index] * x_scale, records[indices, y_index] * y_scale, color=BENCHMARK_COLORS["current"], marker=CURRENT_MARKER, s=8.0)
    axis.set(xlabel=xlabel, ylabel=ylabel); axis.set_box_aspect(1); axis.grid(True, alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _overlay(path: Path, *, observable: str, legacy: np.ndarray, current: np.ndarray, period_turns: int, stride: int) -> Path:
    indices = _sample_indices(len(current), stride)
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    if observable == "action":
        legacy_x, current_x = legacy[:, 0] / period_turns, current[:, 0] / period_turns
        legacy_y, current_y = _normalised_action(legacy), _normalised_action(current)
        xlabel, ylabel = "synchrotron oscillations", r"$\epsilon_x / \epsilon_{x0}$"
    elif observable == "z":
        legacy_x, current_x, legacy_y, current_y, xlabel, ylabel = legacy[:, 0], current[:, 0], legacy[:, 5], current[:, 5], "turn [-]", "z [m]"
    elif observable == "x_xp":
        legacy_x, current_x, legacy_y, current_y, xlabel, ylabel = legacy[:, 1] * 1000.0, current[:, 1] * 1000.0, legacy[:, 2] * 1000.0, current[:, 2] * 1000.0, "x [mm]", "xp [mrad]"
    else:
        legacy_x, current_x, legacy_y, current_y, xlabel, ylabel = legacy[:, 5], current[:, 5], legacy[:, 6], current[:, 6], "z [m]", "dE [GeV]"
    axis.scatter(legacy_x[indices], legacy_y[indices], color=BENCHMARK_COLORS["legacy"], label="Legacy PTC-PyORBIT2", **layered_overlay_style(0))
    axis.scatter(current_x[indices], current_y[indices], color=BENCHMARK_COLORS["current"], label="PTC-PyORBIT3", **layered_overlay_style(1))
    axis.set(xlabel=xlabel, ylabel=ylabel); axis.set_box_aspect(1); axis.grid(True, alpha=0.3); axis.legend(markerscale=1.5)
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
    parser.add_argument("--profile", choices=("smoke", "reference", "legacy_artifact"), default="smoke")
    parser.add_argument("--output-dir", type=Path, default=STEP_DIR / "output")
    parser.add_argument("--reference-root", type=Path); parser.add_argument("--skip-reference-comparison", action="store_true"); parser.add_argument("--madx", type=Path)
    args = parser.parse_args(argv)
    config_path = STEP_DIR / "config.json"
    config = load_step_config(config_path, step=8, profile=args.profile)
    print(format_resolved_config(config_path, step=8, profile=args.profile), flush=True)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    launch, longitudinal, diagnostics = payload["launch"], payload["longitudinal"], payload["diagnostics"]
    coordinates = np.asarray((launch["x_m"], launch["xp_rad"], launch["y_m"], launch["yp_rad"], launch["z_sigma"] * longitudinal["bunch_length_rms_m"], launch["dE_GeV"]))
    output, inputs = args.output_dir.resolve(), STEP_DIR / "input" / "generated" / args.profile / "madx"
    paths = resolve_runtime_paths(madx=args.madx or Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00"))
    staged = stage_packaged_inputs(source=STEP_DIR / "legacy_input", destination=inputs / "Input")
    flat = generate_flat_file(madx=paths.madx, workdir=inputs, madx_input=inputs / "Input" / "SIS18.madx")
    prepare_pyorbit3_runtime(paths, Path("/tmp/sis18_ptc_runtime"))
    records, summary = _run(flat=flat, inputs=inputs, config=config, payload=payload, coordinates=coordinates)
    plots, tables, trajectories = output / "plots", output / "tables", output / "trajectories"; trajectories.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(trajectories / "single_particle_turn_records.npz", records=records)
    diagnostics_path = _write_records(tables / "turn_diagnostics.csv", records)
    stride, period_turns = diagnostics["plot_sample_stride"], longitudinal["synchrotron_period_turns"]
    current = {"action": _plot_action(plots / "action_x_vs_synchrotron_oscillations.png", records, period_turns=period_turns, stride=stride), "z": _plot_series(plots / "z_vs_turn.png", records, stride=stride), "x_xp": _plot_phase_space(plots / "poincare_x_xp.png", records, longitudinal=False, stride=stride), "z_dE": _plot_phase_space(plots / "poincare_z_dE.png", records, longitudinal=True, stride=stride)}
    reference = maybe_reference_root(args.reference_root, comparison_enabled=not args.skip_reference_comparison)
    reference_artifacts: dict[str, str] = {}; generated_plots = [str(path) for path in current.values()]
    comparison: dict[str, object] = {"published_case": args.profile == "reference", "website_case": "Qs=1e-3, 100000 turns, Step 7 launch", "legacy_duration_turns": payload["comparison"]["legacy_turns"], "website_slide_duration_discrepancy": "the slide heading says 100000 turns while its plotted horizontal axis reaches 200000 turns"}
    if reference is not None:
        reference_output = reference / "Step8" / "final_output"
        legacy_data = reference_output / "Particle_0.dat"
        legacy = comparison_records(legacy_particle_records(legacy_data), turns=config.turns)
        legacy_images = {"action": reference_output / "Particle_trapping_SIS18_Step_8.png", "z": reference_output / "Particle_trapping_z_SIS18_Step_8.png", "x_xp": reference_output / "Poincare_x_xp_SIS18_Step_8.png", "z_dE": reference_output / "Poincare_z_dE_SIS18_Step_8.png"}
        for observable, legacy_image in legacy_images.items():
            generated_plots.append(str(plot_labeled_comparison(legacy_image, current[observable], plots / f"legacy_vs_current_{observable}_side_by_side.png", title=f"SIS18 Step 8 {observable}", left_label="Legacy PTC-PyORBIT2", right_label="PTC-PyORBIT3")))
            generated_plots.append(str(_overlay(plots / f"legacy_vs_current_{observable}_numeric_overlay.png", observable=observable, legacy=legacy, current=records, period_turns=period_turns, stride=stride)))
        slide = WEBSITE_REFERENCE_DIR / payload["comparison"]["website_slide"]
        generated_plots.append(str(plot_labeled_comparison(slide, current["action"], plots / "website_slide_vs_current_action.png", title="SIS18 Step 8: official GSI slide and current action", left_label="Official GSI Step 8 slide", right_label="PTC-PyORBIT3")))
        reference_artifacts = {str(path): sha256_file(path) for path in (*legacy_images.values(), legacy_data, slide)}
        comparison["numeric"] = trajectory_comparison(legacy, records)
    (output / "comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "comparison.md").write_text("# Step 8 comparison\n\n- Published reference: Qs=1e-3, 100,000 turns, with the Step 7 launch.\n- The retained official slide labels the case as 100,000 turns but its plotted horizontal axis reaches 200,000 turns; this provenance conflict is retained in comparison.json.\n- Legacy artifact: 200,000 turns; the reference run compares its matching 100,000-turn prefix.\n- Any numeric disagreement is a benchmark blocker.\n", encoding="utf-8")
    (output / "tracking_summary.json").write_text(json.dumps({**summary, "turns": config.turns, "launch": launch}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = write_run_manifest(output / "manifest.json", {"step": 8, "profile": args.profile, "config_path": str(config_path), "config_sha256": sha256_file(config_path), "command": sys.argv, "turns": config.turns, "mpi_size": 1, "seed": config.seed, "flat_file": str(flat), "flat_file_sha256": sha256_file(flat), "packaged_inputs": {path.name: sha256_file(path) for path in staged}, "reference_artifacts": reference_artifacts, "comparison_enabled": reference is not None, "comparison": comparison, "lattice": summary, "space_charge": payload["physics"]["space_charge"], "sextupole_enabled": config.sextupole_enabled, "code_revisions": {"benchmark": _revision(ROOT), "pyorbit3": _revision(paths.pyorbit3_root), "ptc": _revision(paths.pyorbit3_root.parent / "PTC")}, "plots": generated_plots, "diagnostics": str(diagnostics_path)})
    print(f"Step 8 {args.profile} complete: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
