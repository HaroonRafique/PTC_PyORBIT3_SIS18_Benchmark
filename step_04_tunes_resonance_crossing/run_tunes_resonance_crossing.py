#!/usr/bin/env python
"""Run SIS18 Step 4: sextupole-on resonance-crossing tune scan."""

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
from common.legacy_plot_comparison import plot_labeled_comparison, plot_legacy_comparison
from common.madx import generate_flat_file
from common.manifest import write_run_manifest
from common.poincare_distribution import amplitude_scan_coordinates, dominant_fft_tune
from common.reference_artifacts import maybe_reference_root, sha256_file, stage_packaged_inputs
from common.sis18_comparison import compare_tune_tables
from common.sis18_config import load_step_config
from common.sis18_lattice import in_workdir, load_sis18_lattice
from common.sis18_plots import BENCHMARK_COLORS, layered_overlay_style, plt

STEP_DIR = Path(__file__).resolve().parent
WEBSITE_REFERENCE_DIR = ROOT / "shared_inputs" / "reference_plots" / "step_04"
EPSN_X, EPSN_Y = 4.91e-7, 3.635e-7
DPP_RMS, BUNCH_LENGTH_RMS_M = 2.5e-4 / 3.0, 40.206868
RESTORING_FORCE, SC_PATH_LENGTH_MIN_M = -1.951e-11, 1.0e-8


def scan_sigma_limit(plane: str) -> float:
    """Return the archival Step 4 transverse launch limit."""

    if plane not in {"x", "y"}:
        raise ValueError(f"unknown transverse plane: {plane}")
    return 4.0


def plot_window(plane: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return legacy Step 4 effective-amplitude/fractional-tune plot limits."""

    windows = {"x": ((0.0, 6.0), (0.2325, 0.3505)), "y": ((0.0, 4.62), (0.05, 0.205))}
    try:
        return windows[plane]
    except KeyError as error:
        raise ValueError(f"unknown transverse plane: {plane}") from error


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


def _apply_restoring_force(bunch) -> None:
    for index in range(bunch.getSize()):
        bunch.dE(index, bunch.dE(index) + bunch.z(index) * RESTORING_FORCE)


def _plane_values(lattice, bunch, plane: str, particles: int) -> tuple[np.ndarray, np.ndarray, float]:
    beta, alpha, epsn = (lattice.betax0, lattice.alphax0, EPSN_X) if plane == "x" else (lattice.betay0, lattice.alphay0, EPSN_Y)
    sigma = np.sqrt(beta * epsn / (bunch.getSyncParticle().beta() * bunch.getSyncParticle().gamma()))
    coordinates = amplitude_scan_coordinates(plane=plane, n_particles=particles, n_sigma=scan_sigma_limit(plane), betax=lattice.betax0, betay=lattice.betay0, epsn_x=EPSN_X, epsn_y=EPSN_Y, beta_rel=bunch.getSyncParticle().beta(), gamma_rel=bunch.getSyncParticle().gamma())
    coordinate = coordinates[:, 0 if plane == "x" else 2]
    return coordinates, np.column_stack((coordinate / sigma, np.sqrt(1.0 + alpha * alpha) * coordinate / sigma)), sigma


def _snapshot_by_id(bunch, particles: int) -> np.ndarray:
    snapshot = np.full((particles, 6), np.nan)
    for index in range(bunch.getSize()):
        particle_id = int(round(bunch.partAttrValue("ParticleIdNumber", index, 0)))
        if 0 <= particle_id < particles:
            snapshot[particle_id] = (bunch.x(index), bunch.xp(index), bunch.y(index), bunch.yp(index), bunch.z(index), bunch.dE(index))
    return snapshot


def surviving_particle_ids(snapshot: np.ndarray) -> set[int]:
    """Return IDs present in an ID-indexed coordinate snapshot."""

    return set(np.flatnonzero(np.isfinite(snapshot[:, 0])))


def _extract_tunes(trajectories: np.ndarray, *, plane: str, analysis_turns: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    try:
        from PyNAFF import naff
    except ImportError as error:
        raise RuntimeError("Step 4 requires PyNAFF; install it with `python -m pip install PyNAFF`.") from error
    coordinate = 0 if plane == "x" else 2
    ids, pynaff, fft = [], [], []
    for particle in range(1, trajectories.shape[1]):
        signal = trajectories[:, particle, coordinate]
        if np.isfinite(signal).all():
            ids.append(particle); pynaff.append(float(naff(data=signal, turns=analysis_turns, nterms=1, warnings=False)[0][1])); fft.append(dominant_fft_tune(signal[1:]))
    return np.asarray(ids), np.asarray(pynaff), np.asarray(fft)


def _absolute_tunes(bare_tune: float, fractional_tunes: np.ndarray) -> np.ndarray:
    return np.floor(bare_tune) + np.asarray(fractional_tunes, dtype=float)


def _write_table(path: Path, ids: np.ndarray, amplitudes: np.ndarray, pynaff: np.ndarray, fft: np.ndarray, bare_tune: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for method, values in (("pynaff", pynaff), ("fft", fft)):
        with path.with_name(f"{path.stem}_{method}{path.suffix}").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream); writer.writerow(("particle_id", "launch_coordinate_sigma", "effective_amplitude_sigma", "tune_fractional", "tune_absolute"))
            for particle, tune in zip(ids, values):
                writer.writerow((particle, f"{amplitudes[particle, 0]:.12g}", f"{amplitudes[particle, 1]:.12g}", f"{tune:.12g}", f"{_absolute_tunes(bare_tune, tune):.12g}"))


def _current_plot(path: Path, *, plane: str, amplitudes: np.ndarray, ids: np.ndarray, pynaff: np.ndarray, fft: np.ndarray, bare_tune: float) -> Path:
    xlim, fractional_ylim = plot_window(plane)
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.scatter(amplitudes[ids, 1], _absolute_tunes(bare_tune, pynaff), color=BENCHMARK_COLORS["current"], label="PTC-PyORBIT3 PyNAFF", **layered_overlay_style(0))
    axis.scatter(amplitudes[ids, 1], _absolute_tunes(bare_tune, fft), color="#D55E00", label="PTC-PyORBIT3 FFT", **layered_overlay_style(1))
    axis.set(xlabel=rf"effective {plane} amplitude [$\sigma_{plane}$]", ylabel=rf"$Q_{plane}$", xlim=xlim, ylim=tuple(value + np.floor(bare_tune) for value in fractional_ylim))
    axis.set_box_aspect(1); axis.grid(True, alpha=0.3); axis.legend(markerscale=2)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _overlay_plot(path: Path, *, plane: str, legacy: np.ndarray, amplitudes: np.ndarray, ids: np.ndarray, pynaff: np.ndarray, fft: np.ndarray) -> Path:
    xlim, ylim = plot_window(plane)
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.scatter(legacy[:, 0], legacy[:, 1], color=BENCHMARK_COLORS["legacy"], label="Legacy PTC-PyORBIT", **layered_overlay_style(0))
    axis.scatter(amplitudes[ids, 1], pynaff, color=BENCHMARK_COLORS["current"], label="PTC-PyORBIT3 PyNAFF", **layered_overlay_style(1))
    axis.scatter(amplitudes[ids, 1], fft, color="#D55E00", label="PTC-PyORBIT3 FFT", **layered_overlay_style(2))
    axis.set(xlabel=rf"effective {plane} amplitude [$\sigma_{plane}$]", ylabel=rf"fractional $Q_{plane}$", xlim=xlim, ylim=ylim)
    axis.set_box_aspect(1); axis.grid(True, alpha=0.3); axis.legend(markerscale=2)
    path.parent.mkdir(parents=True, exist_ok=True); figure.savefig(path, dpi=160); plt.close(figure)
    return path


def _run_plane(*, flat: Path, inputs: Path, config, plane: str, particles: int, turns: int):
    lattice, bunch = load_sis18_lattice(flat)
    from ext.ptc_orbit.ptc_orbit import readScriptPTC
    with in_workdir(inputs / "Input"): readScriptPTC("time.ptc")
    sc_nodes = _install_historical_model(lattice, config)
    coordinates, amplitudes, sigma = _plane_values(lattice, bunch, plane, particles)
    bunch.addPartAttr("macrosize"); bunch.addPartAttr("ParticleIdNumber")
    for coordinate in coordinates: bunch.addParticle(*coordinate)
    for index in range(bunch.getSize()):
        bunch.partAttrValue("macrosize", index, 0, config.intensity / particles); bunch.partAttrValue("ParticleIdNumber", index, 0, index)
    from orbit.core.bunch import Bunch
    lostbunch = Bunch(); bunch.copyEmptyBunchTo(lostbunch); lostbunch.addPartAttr("ParticlePhaseAttributes"); lostbunch.addPartAttr("LostParticleAttributes")
    trajectories, first_lost = [_snapshot_by_id(bunch, particles)], np.full(particles, -1, dtype=int)
    parameters = {"bunch": bunch, "lostbunch": lostbunch, "length": lattice.getLength() / lattice.nHarm}; previous_ids = surviving_particle_ids(trajectories[-1])
    for turn in range(1, turns + 1):
        lattice.trackBunch(bunch, parameters); _apply_restoring_force(bunch); snapshot = _snapshot_by_id(bunch, particles); current_ids = surviving_particle_ids(snapshot)
        for particle_id in previous_ids - current_ids: first_lost[particle_id] = turn
        trajectories.append(snapshot); previous_ids = current_ids
    return np.asarray(trajectories), amplitudes, first_lost, {"nodes": lattice.nNodes, "length_m": lattice.getLength(), "sc_nodes": len(sc_nodes), "sigma_m": sigma}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "reference"), default="smoke"); parser.add_argument("--output-dir", type=Path, default=STEP_DIR / "output"); parser.add_argument("--reference-root", type=Path); parser.add_argument("--skip-reference-comparison", action="store_true"); parser.add_argument("--madx", type=Path)
    args = parser.parse_args(argv); config = load_step_config(STEP_DIR / "config.json", step=4, profile=args.profile); particles, turns = config.n_macroparticles, config.turns
    if particles < 2 or turns < 4: raise ValueError("Step 4 requires at least 2 particles and 4 turns")
    output, inputs = args.output_dir.resolve(), STEP_DIR / "input" / "generated" / args.profile / "madx"; paths = resolve_runtime_paths(madx=args.madx or Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00"))
    staged = stage_packaged_inputs(source=STEP_DIR / "legacy_input", destination=inputs / "Input"); flat = generate_flat_file(madx=paths.madx, workdir=inputs, madx_input=inputs / "Input" / "SIS18.madx"); prepare_pyorbit3_runtime(paths, Path("/tmp/sis18_ptc_runtime"))
    plots, tables, trajectories_dir = output / "plots", output / "tables", output / "trajectories"; trajectories_dir.mkdir(parents=True, exist_ok=True); reference = maybe_reference_root(args.reference_root, comparison_enabled=not args.skip_reference_comparison)
    summaries, comparison_payload, reference_artifacts, generated_plots, current_plots = {}, {}, {}, [], {}
    for plane, bare_tune in (("x", config.qx), ("y", config.qy)):
        trajectories, amplitudes, first_lost, summary = _run_plane(flat=flat, inputs=inputs, config=config, plane=plane, particles=particles, turns=turns); np.savez_compressed(trajectories_dir / f"{plane}_turn_by_particle.npz", coordinates=trajectories, turns=np.arange(turns + 1))
        ids, pynaff, fft = _extract_tunes(trajectories, plane=plane, analysis_turns=max(2, turns // 2 - 2)); _write_table(tables / f"tunes_{plane}.csv", ids, amplitudes, pynaff, fft, bare_tune)
        with (tables / f"lost_particles_{plane}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream); writer.writerow(("particle_id", "launch_coordinate_sigma", "effective_amplitude_sigma", "first_lost_turn")); [writer.writerow((particle_id, *amplitudes[particle_id], first_lost[particle_id])) for particle_id in np.flatnonzero(first_lost >= 0)]
        current = _current_plot(plots / f"{plane}_tune_vs_effective_amplitude.png", plane=plane, amplitudes=amplitudes, ids=ids, pynaff=pynaff, fft=fft, bare_tune=bare_tune); current_plots[plane] = current; generated_plots.append(str(current)); summaries[plane] = {**summary, "surviving_tune_particles": len(ids), "lost_particles": int((first_lost >= 0).sum())}
        if reference is not None:
            reference_output = reference / "Step4" / "output"; legacy_table = reference_output / f"SIS18_Step4_{plane}_I=2.95e10_Tunes_OnData.txt"; legacy_plot = reference_output / f"SIS18_Step4_{plane}_I=2.95e10_Q{'x' if plane == 'x' else 'y'}.png"; legacy = np.loadtxt(legacy_table); comparison_payload[plane] = compare_tune_tables(legacy, np.column_stack((amplitudes[ids, 1], pynaff))).__dict__
            generated_plots.extend((str(_overlay_plot(plots / f"legacy_vs_current_{plane}_numeric_overlay.png", plane=plane, legacy=legacy, amplitudes=amplitudes, ids=ids, pynaff=pynaff, fft=fft)), str(plot_legacy_comparison(legacy_plot, current, plots / f"legacy_vs_current_{plane}_side_by_side.png", title=f"SIS18 Step 4 {plane}-plane tunes")))); reference_artifacts.update({str(legacy_table): sha256_file(legacy_table), str(legacy_plot): sha256_file(legacy_plot)})
    website_manifest = json.loads((WEBSITE_REFERENCE_DIR / "reference_manifest.json").read_text(encoding="utf-8"))
    for plane, entry in zip(("x", "y"), website_manifest["plots"]):
        reference_artifacts[entry["file"]] = sha256_file(WEBSITE_REFERENCE_DIR / entry["file"]); generated_plots.append(str(plot_labeled_comparison(WEBSITE_REFERENCE_DIR / entry["file"], current_plots[plane], plots / f"website_vs_current_{plane}_same_axes.png", title=f"SIS18 Step 4 {plane}-plane tunes", left_label="Original GSI reference", right_label="PTC-PyORBIT3")))
    (output / "comparison.json").write_text(json.dumps(comparison_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"); (output / "comparison.md").write_text("# Step 4 comparison\n\n- Historical tune tables use PyNAFF comparison on surviving IDs.\n- FFT is a diagnostic cross-check.\n- Public source: " + website_manifest["source_page"] + "\n", encoding="utf-8"); (output / "tracking_summary.json").write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = write_run_manifest(output / "manifest.json", {"step": 4, "profile": args.profile, "command": sys.argv, "particles_per_plane": particles, "turns": turns, "mpi_size": 1, "seed": config.seed, "flat_file": str(flat), "flat_file_sha256": sha256_file(flat), "packaged_inputs": {path.name: sha256_file(path) for path in staged}, "reference_artifacts": reference_artifacts, "comparison_enabled": reference is not None, "comparison": comparison_payload, "lattice": summaries, "space_charge": "analytical_frozen_gaussian", "sextupole_enabled": True, "code_revisions": {"benchmark": _revision(ROOT), "pyorbit3": _revision(paths.pyorbit3_root), "ptc": _revision(paths.pyorbit3_root.parent / "PTC")}, "plots": generated_plots})
    print(f"Step 4 {args.profile} complete: {manifest}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
