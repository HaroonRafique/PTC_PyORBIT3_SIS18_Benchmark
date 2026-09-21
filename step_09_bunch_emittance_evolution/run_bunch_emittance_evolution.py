#!/usr/bin/env python
"""Run SIS18 Step 9: full-bunch horizontal emittance evolution."""

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

from common.bunch_distribution import matched_gaussian_coordinates
from common.environment import prepare_pyorbit3_runtime, resolve_runtime_paths
from common.legacy_plot_comparison import plot_labeled_comparison, plot_same_axes_references
from common.madx import generate_flat_file, set_madx_bare_tunes
from common.manifest import write_run_manifest
from common.reference_artifacts import maybe_reference_root, sha256_file, stage_packaged_inputs
from common.sis18_config import format_resolved_config, load_profile_payload, load_step_config
from common.sis18_lattice import in_workdir, load_sis18_lattice
from common.sis18_plots import BENCHMARK_COLORS, layered_overlay_style, plt

STEP_DIR = Path(__file__).resolve().parent
WEBSITE_REFERENCE_DIR = ROOT / "shared_inputs" / "reference_plots" / "step_09"


def resolved_payload(*, profile: str) -> dict[str, object]:
    """Return Step 9 global settings plus its selected profile override."""

    config_path = STEP_DIR / "config.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["resolved_profile"] = load_profile_payload(config_path, step=9, profile=profile)
    return payload


def sampled_turns(*, turns: int, stride: int) -> np.ndarray:
    """Return turn zero, regular diagnostic samples, and the final turn."""

    if turns < 1 or stride < 1:
        raise ValueError("turns and stride must be positive")
    return np.unique(np.append(np.arange(0, turns + 1, stride, dtype=int), turns))


def normalised_emittance_history(values: np.ndarray) -> np.ndarray:
    """Normalise an emittance history to its finite positive first value."""

    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values) & (values > 0.0)]
    if not len(finite):
        raise ValueError("emittance history has no finite positive initial value")
    return values / finite[0]


def legacy_emittance_history(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read the external historical Step 9 MAT history without copying it."""

    from scipy.io import loadmat

    payload = loadmat(path, squeeze_me=True)
    return np.asarray(payload["turn"], dtype=int).reshape(-1), np.asarray(payload["epsn_x"], dtype=float).reshape(-1)


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
    calculator = SpaceChargeCalcAnalyticGaussian(config.intensity, beam["epsn_x"], beam["epsn_y"], beam["dpp_rms"], GaussianLineDensityProfile(longitudinal["bunch_length_rms_m"]))
    return len(setSCanalyticalAccNodes(lattice, physics["sc_path_length_min_m"], calculator))


def _apply_restoring_force(bunch, force: float) -> None:
    for index in range(bunch.getSize()):
        bunch.dE(index, bunch.dE(index) + bunch.z(index) * force)


def _diagnostic_row(turn: int, bunch, analysis) -> tuple[float, ...]:
    analysis.analyzeBunch(bunch)
    return (
        float(turn),
        float(analysis.getGlobalCount()),
        float(analysis.getGlobalMacrosize()),
        float(analysis.getEmittanceNormalized(0)),
        float(analysis.getEmittanceNormalized(1)),
        float(analysis.getEmittance(2)),
        float(analysis.getAverage(0)),
        float(analysis.getAverage(2)),
        float(analysis.getAverage(4)),
    )


def _run(*, flat: Path, inputs: Path, config, payload: dict[str, object]) -> tuple[np.ndarray, dict[str, object]]:
    lattice, bunch = load_sis18_lattice(flat)
    from ext.ptc_orbit.ptc_orbit import readScriptPTC
    from orbit.core.bunch import Bunch, BunchTwissAnalysis

    with in_workdir(inputs / "Input"):
        readScriptPTC("time.ptc")
    beam, distribution, diagnostics = payload["beam"], payload["distribution"], payload["diagnostics"]
    coordinates = matched_gaussian_coordinates(
        n_particles=config.n_macroparticles, seed=config.seed, betax=lattice.betax0, alphax=lattice.alphax0,
        betay=lattice.betay0, alphay=lattice.alphay0, etax=lattice.etax0, etapx=lattice.etapx0,
        epsn_x=beam["epsn_x"], epsn_y=beam["epsn_y"], beta_rel=bunch.getSyncParticle().beta(),
        gamma_rel=bunch.getSyncParticle().gamma(), dpp_rms=beam["dpp_rms"],
        bunch_length_rms_m=payload["longitudinal"]["bunch_length_rms_m"], particle_mass_GeV=bunch.mass(),
        transverse_cut_sigma=distribution["transverse_cut_sigma"],
    )
    sc_nodes = _install_historical_model(lattice, config, payload)
    bunch.addPartAttr("macrosize"); bunch.addPartAttr("ParticleIdNumber")
    for particle_id, coordinate in enumerate(coordinates):
        bunch.addParticle(*coordinate)
        bunch.partAttrValue("macrosize", particle_id, 0, config.intensity / config.n_macroparticles)
        bunch.partAttrValue("ParticleIdNumber", particle_id, 0, particle_id)
    lostbunch = Bunch(); bunch.copyEmptyBunchTo(lostbunch); lostbunch.addPartAttr("ParticlePhaseAttributes"); lostbunch.addPartAttr("LostParticleAttributes")
    analysis, samples = BunchTwissAnalysis(), []
    observed = set(sampled_turns(turns=config.turns, stride=diagnostics["sample_stride_turns"]).tolist())
    parameters = {"bunch": bunch, "lostbunch": lostbunch, "length": lattice.getLength() / lattice.nHarm}
    samples.append(_diagnostic_row(0, bunch, analysis))
    for turn in range(1, config.turns + 1):
        lattice.trackBunch(bunch, parameters)
        _apply_restoring_force(bunch, config.restoring_force)
        if turn in observed:
            samples.append(_diagnostic_row(turn, bunch, analysis))
    return np.asarray(samples), {"nodes": lattice.nNodes, "length_m": lattice.getLength(), "sc_nodes": sc_nodes, "survivors": bunch.getSize(), "launch_coordinate_statistics": {"x_rms_m": float(np.std(coordinates[:, 0])), "z_rms_m": float(np.std(coordinates[:, 4]))}}


def _write_diagnostics(path: Path, records: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ("turn", "n_macroparticles", "intensity", "epsn_x", "epsn_y", "eps_z", "mean_x_m", "mean_y_m", "mean_z_m")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(header); writer.writerows(records)
    return path


def _plot_history(path: Path, turns: np.ndarray, epsn_x: np.ndarray, *, label: str = "PTC-PyORBIT3") -> Path:
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.plot(turns / 1000.0, normalised_emittance_history(epsn_x), color=BENCHMARK_COLORS["current"], marker="x", markersize=1.75, linewidth=1.0, label=label)
    axis.set(xlabel="synchrotron oscillations", ylabel=r"$\epsilon_x / \epsilon_{x0}$", xlim=(0.0, 100.0), ylim=(1.0, 2.2))
    axis.set_box_aspect(1); axis.grid(True, alpha=0.3); axis.legend()
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _overlay(path: Path, *, legacy_turns: np.ndarray, legacy_epsn_x: np.ndarray, current: np.ndarray) -> Path:
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.scatter(legacy_turns / 1000.0, normalised_emittance_history(legacy_epsn_x), color=BENCHMARK_COLORS["legacy"], label="Legacy PTC-PyORBIT2 artifact", **layered_overlay_style(0))
    axis.scatter(current[:, 0] / 1000.0, normalised_emittance_history(current[:, 3]), color=BENCHMARK_COLORS["current"], label="PTC-PyORBIT3", **layered_overlay_style(1))
    axis.set(xlabel="synchrotron oscillations", ylabel=r"$\epsilon_x / \epsilon_{x0}$", xlim=(0.0, 100.0), ylim=(1.0, 2.2))
    axis.set_box_aspect(1); axis.grid(True, alpha=0.3); axis.legend(markerscale=1.5)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "reference", "legacy_artifact"), default="smoke")
    parser.add_argument("--output-dir", type=Path, default=STEP_DIR / "output")
    parser.add_argument("--reference-root", type=Path); parser.add_argument("--skip-reference-comparison", action="store_true"); parser.add_argument("--madx", type=Path)
    args = parser.parse_args(argv)
    config_path = STEP_DIR / "config.json"; config = load_step_config(config_path, step=9, profile=args.profile); payload = resolved_payload(profile=args.profile)
    print(format_resolved_config(config_path, step=9, profile=args.profile), flush=True)
    output, inputs = args.output_dir.resolve(), STEP_DIR / "input" / "generated" / args.profile / "madx"
    paths = resolve_runtime_paths(madx=args.madx or Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00"))
    staged = stage_packaged_inputs(source=STEP_DIR / "legacy_input", destination=inputs / "Input")
    set_madx_bare_tunes(inputs / "Input" / "SIS18.madx", qx=config.qx, qy=config.qy)
    flat = generate_flat_file(madx=paths.madx, workdir=inputs, madx_input=inputs / "Input" / "SIS18.madx")
    prepare_pyorbit3_runtime(paths, Path("/tmp/sis18_ptc_runtime"))
    records, summary = _run(flat=flat, inputs=inputs, config=config, payload=payload)
    plots, tables = output / "plots", output / "tables"
    diagnostics_path = _write_diagnostics(tables / "bunch_diagnostics.csv", records)
    current_plot = _plot_history(plots / "epsn_x_vs_synchrotron_oscillations.png", records[:, 0], records[:, 3])
    reference = maybe_reference_root(args.reference_root, comparison_enabled=not args.skip_reference_comparison)
    reference_artifacts: dict[str, str] = {}; plot_paths = [str(current_plot)]
    comparison: dict[str, object] = {"website_target": payload["comparison"]["website_expected_final_epsn_x_ratio"], "automated_acceptance": "report_only_manual_scientific_review", "legacy_case": payload["comparison"]["legacy_case"]}
    if reference is not None:
        legacy_path = reference / payload["comparison"]["legacy_output_mat"]
        legacy_turns, legacy_epsn_x = legacy_emittance_history(legacy_path)
        legacy_plot = _plot_history(plots / "legacy_epsn_x_vs_synchrotron_oscillations.png", legacy_turns, legacy_epsn_x, label="Legacy PTC-PyORBIT2 artifact")
        plot_paths.extend((str(legacy_plot), str(plot_labeled_comparison(legacy_plot, current_plot, plots / "legacy_vs_current_epsn_x_side_by_side.png", title="SIS18 Step 9 normalized horizontal emittance", left_label="Legacy PTC-PyORBIT2 artifact", right_label="PTC-PyORBIT3")), str(_overlay(plots / "legacy_vs_current_epsn_x_numeric_overlay.png", legacy_turns=legacy_turns, legacy_epsn_x=legacy_epsn_x, current=records))))
        slides = [(name, WEBSITE_REFERENCE_DIR / name) for name in payload["comparison"]["website_slide_files"]]
        plot_paths.append(str(plot_same_axes_references(current=current_plot, references=slides, output=plots / "website_slides_and_current_grid.png")))
        reference_artifacts = {str(path): sha256_file(path) for path in (legacy_path, *(path for _, path in slides))}
        comparison["legacy_final_epsn_x_ratio"] = float(normalised_emittance_history(legacy_epsn_x)[-1])
    comparison["current_final_epsn_x_ratio"] = float(normalised_emittance_history(records[:, 3])[-1])
    (output / "comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "comparison.md").write_text("# Step 9 comparison\n\n- Website-authoritative case: 1,000 macroparticles, Qx=4.3504, Qs=1e-3, 100,000 turns; published final estimate is epsilon_x/epsilon_x0 approximately 2.08.\n- Acceptance is report-only and requires manual scientific review.\n- The archived numeric artifact is a distinct 10,000-macroparticle Qx=4.3604 tomoscope-based ensemble, so its overlay is diagnostic rather than turn-by-turn equivalence.\n", encoding="utf-8")
    (output / "tracking_summary.json").write_text(json.dumps({**summary, "turns": config.turns, "n_macroparticles": config.n_macroparticles}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = write_run_manifest(output / "manifest.json", {"step": 9, "profile": args.profile, "config_path": str(config_path), "config_sha256": sha256_file(config_path), "command": sys.argv, "turns": config.turns, "mpi_size": 1, "seed": config.seed, "flat_file": str(flat), "flat_file_sha256": sha256_file(flat), "packaged_inputs": {path.name: sha256_file(path) for path in staged}, "reference_artifacts": reference_artifacts, "comparison_enabled": reference is not None, "comparison": comparison, "lattice": summary, "space_charge": payload["physics"]["space_charge"], "sextupole_enabled": config.sextupole_enabled, "code_revisions": {"benchmark": _revision(ROOT), "pyorbit3": _revision(paths.pyorbit3_root), "ptc": _revision(paths.pyorbit3_root.parent / "PTC")}, "plots": plot_paths, "diagnostics": str(diagnostics_path)})
    print(f"Step 9 {args.profile} complete: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
