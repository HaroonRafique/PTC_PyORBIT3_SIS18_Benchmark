#!/usr/bin/env python
"""Run SIS18 Step 2: frozen-space-charge tunes without sextupole."""

from __future__ import annotations

import argparse
import csv
import json
import os
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
WEBSITE_REFERENCE_DIR = ROOT / "shared_inputs" / "reference_plots" / "step_02"
EPSN_X = 4.91e-7
EPSN_Y = 3.635e-7
DPP_RMS = 2.5e-4 / 3.0
BUNCH_LENGTH_RMS_M = 40.206868
RESTORING_FORCE = -1.951e-11
SC_PATH_LENGTH_MIN_M = 1.0e-8


def _revision(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _snapshot(bunch) -> np.ndarray:
    return np.asarray([[bunch.x(i), bunch.xp(i), bunch.y(i), bunch.yp(i), bunch.z(i), bunch.dE(i)] for i in range(bunch.getSize())])


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
    calculator = SpaceChargeCalcAnalyticGaussian(
        config.intensity, EPSN_X, EPSN_Y, DPP_RMS, GaussianLineDensityProfile(BUNCH_LENGTH_RMS_M)
    )
    return setSCanalyticalAccNodes(lattice, SC_PATH_LENGTH_MIN_M, calculator)


def _apply_restoring_force(bunch) -> None:
    for index in range(bunch.getSize()):
        bunch.dE(index, bunch.dE(index) + bunch.z(index) * RESTORING_FORCE)


def tracking_parameters(*, bunch, lostbunch, length_m: float) -> dict:
    """Return the PTC tracking context required by lattice and aperture nodes."""

    return {"bunch": bunch, "lostbunch": lostbunch, "length": length_m}


def effective_amplitude_sigma(*, coordinate_m: np.ndarray | float, sigma_m: float, beta_twiss: float, alpha_twiss: float) -> np.ndarray:
    """Return the legacy Step 2 effective amplitude in transverse sigma."""

    gamma_twiss = (1.0 + alpha_twiss * alpha_twiss) / beta_twiss
    return np.sqrt(beta_twiss * gamma_twiss) * np.asarray(coordinate_m, dtype=float) / sigma_m


def _plane_values(lattice, bunch, plane: str, particles: int) -> tuple[np.ndarray, np.ndarray, float]:
    beta = lattice.betax0 if plane == "x" else lattice.betay0
    alpha = lattice.alphax0 if plane == "x" else lattice.alphay0
    epsn = EPSN_X if plane == "x" else EPSN_Y
    sigma = np.sqrt(beta * epsn / (bunch.getSyncParticle().beta() * bunch.getSyncParticle().gamma()))
    coordinates = amplitude_scan_coordinates(
        plane=plane,
        n_particles=particles,
        n_sigma=4.0,
        betax=lattice.betax0,
        betay=lattice.betay0,
        epsn_x=EPSN_X,
        epsn_y=EPSN_Y,
        beta_rel=bunch.getSyncParticle().beta(),
        gamma_rel=bunch.getSyncParticle().gamma(),
    )
    launch_sigma = coordinates[:, 0 if plane == "x" else 2] / sigma
    effective_sigma = effective_amplitude_sigma(
        coordinate_m=coordinates[:, 0 if plane == "x" else 2], sigma_m=sigma, beta_twiss=beta, alpha_twiss=alpha
    )
    return coordinates, np.column_stack((launch_sigma, effective_sigma)), sigma


def _extract_tunes(trajectories: np.ndarray, *, plane: str, analysis_turns: int) -> tuple[np.ndarray, np.ndarray]:
    try:
        from PyNAFF import naff
    except ImportError as exc:
        raise RuntimeError("Step 2 requires PyNAFF; install it with `python -m pip install PyNAFF`.") from exc
    coordinate = 0 if plane == "x" else 2
    pynaff = []
    fft = []
    for particle in range(1, trajectories.shape[1]):
        signal = trajectories[:, particle, coordinate]
        pynaff.append(float(naff(data=signal, turns=analysis_turns, nterms=1, warnings=False)[0][1]))
        fft.append(dominant_fft_tune(signal[1:]))
    return np.asarray(pynaff), np.asarray(fft)


def absolute_tunes(bare_tune: float, fractional_tunes: np.ndarray) -> np.ndarray:
    """Convert fractional spectral tunes to the configured SIS18 tune branch."""

    return np.floor(bare_tune) + np.asarray(fractional_tunes, dtype=float)


def _write_table(path: Path, amplitudes: np.ndarray, pynaff: np.ndarray, fft: np.ndarray, bare_tune: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("particle_id", "launch_coordinate_sigma", "effective_amplitude_sigma", "tune_fractional", "tune_absolute"))
        for method, values in (("pynaff", pynaff), ("fft", fft)):
            method_path = path.with_name(f"{path.stem}_{method}{path.suffix}")
            with method_path.open("w", newline="", encoding="utf-8") as method_stream:
                method_writer = csv.writer(method_stream)
                method_writer.writerow(("particle_id", "launch_coordinate_sigma", "effective_amplitude_sigma", "tune_fractional", "tune_absolute"))
                for particle, ((launch, effective), tune) in enumerate(zip(amplitudes[1:], values), start=1):
                    method_writer.writerow((particle, f"{launch:.12g}", f"{effective:.12g}", f"{tune:.12g}", f"{absolute_tunes(bare_tune, tune):.12g}"))
        for particle, ((launch, effective), tune) in enumerate(zip(amplitudes[1:], pynaff), start=1):
            writer.writerow((particle, f"{launch:.12g}", f"{effective:.12g}", f"{tune:.12g}", f"{absolute_tunes(bare_tune, tune):.12g}"))
    return path


def _current_plot(path: Path, *, plane: str, amplitudes: np.ndarray, pynaff: np.ndarray, fft: np.ndarray, bare_tune: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.scatter(amplitudes[1:, 0], absolute_tunes(bare_tune, pynaff), color=BENCHMARK_COLORS["current"], label="PTC-PyORBIT3 PyNAFF", **layered_overlay_style(0))
    axis.scatter(amplitudes[1:, 0], absolute_tunes(bare_tune, fft), color="#D55E00", label="PTC-PyORBIT3 FFT", **layered_overlay_style(1))
    axis.set(xlabel=rf"${plane}_0/\sigma_{plane}$", ylabel=rf"$Q_{plane}$", xlim=(0.0, 5.0), ylim=(4.235, 4.340) if plane == "x" else (3.050, 3.205))
    axis.set_box_aspect(1)
    axis.grid(True, alpha=0.3)
    axis.legend(markerscale=2)
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def _overlay_plot(path: Path, *, plane: str, legacy: np.ndarray, amplitudes: np.ndarray, pynaff: np.ndarray, fft: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(6, 6), constrained_layout=True)
    axis.scatter(legacy[:, 0], legacy[:, 1], color=BENCHMARK_COLORS["legacy"], label="Legacy PTC-PyORBIT", **layered_overlay_style(0))
    axis.scatter(amplitudes[1:, 1], pynaff, color=BENCHMARK_COLORS["current"], label="PTC-PyORBIT3 PyNAFF", **layered_overlay_style(1))
    axis.scatter(amplitudes[1:, 1], fft, color="#D55E00", label="PTC-PyORBIT3 FFT", **layered_overlay_style(2))
    axis.set(xlabel=rf"effective {plane} amplitude [$\sigma_{plane}$]", ylabel=rf"fractional $Q_{plane}$", xlim=(0.0, 6.5) if plane == "x" else (0.0, 4.5), ylim=(0.2325, 0.3375) if plane == "x" else (0.05, 0.20625))
    axis.set_box_aspect(1)
    axis.grid(True, alpha=0.3)
    axis.legend(markerscale=2)
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def _run_plane(*, flat: Path, inputs: Path, config, plane: str, particles: int, turns: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    lattice, bunch = load_sis18_lattice(flat)
    from ext.ptc_orbit.ptc_orbit import readScriptPTC

    with in_workdir(inputs / "Input"):
        readScriptPTC("time.ptc")
        readScriptPTC("chrom.ptc")
    sc_nodes = _install_historical_model(lattice, config)
    coordinates, amplitudes, sigma = _plane_values(lattice, bunch, plane, particles)
    bunch.addPartAttr("macrosize")
    for coordinate in coordinates:
        bunch.addParticle(*coordinate)
    for index in range(bunch.getSize()):
        bunch.partAttrValue("macrosize", index, 0, config.intensity / particles)
    from orbit.core.bunch import Bunch

    lostbunch = Bunch()
    bunch.copyEmptyBunchTo(lostbunch)
    lostbunch.addPartAttr("ParticlePhaseAttributes")
    lostbunch.addPartAttr("LostParticleAttributes")
    trajectories = [_snapshot(bunch)]
    parameters = tracking_parameters(bunch=bunch, lostbunch=lostbunch, length_m=lattice.getLength() / lattice.nHarm)
    for _ in range(turns):
        lattice.trackBunch(bunch, parameters)
        _apply_restoring_force(bunch)
        if bunch.getSize() != particles:
            raise RuntimeError(f"Step 2 {plane}-plane scan lost particles")
        trajectories.append(_snapshot(bunch))
    return np.asarray(trajectories), amplitudes, np.asarray(sc_nodes), {"nodes": lattice.nNodes, "length_m": lattice.getLength(), "sc_nodes": len(sc_nodes), "sigma_m": sigma}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "reference"), default="smoke")
    parser.add_argument("--particles", type=int)
    parser.add_argument("--turns", type=int)
    parser.add_argument("--output-dir", type=Path, default=STEP_DIR / "output")
    parser.add_argument("--reference-root", type=Path)
    parser.add_argument("--skip-reference-comparison", action="store_true")
    parser.add_argument("--madx", type=Path)
    args = parser.parse_args(argv)
    config = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=2, profile=args.profile)
    particles = args.particles if args.particles is not None else config.n_macroparticles
    turns = args.turns if args.turns is not None else config.turns
    if turns < 4 or particles < 2:
        raise ValueError("Step 2 requires at least 2 particles and 4 turns")
    output = args.output_dir.resolve()
    inputs = STEP_DIR / "input" / "generated" / args.profile / "madx"
    paths = resolve_runtime_paths(madx=args.madx or Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00"))
    staged = stage_packaged_inputs(source=STEP_DIR / "legacy_input", destination=inputs / "Input")
    flat = generate_flat_file(madx=paths.madx, workdir=inputs, madx_input=inputs / "Input" / "SIS18.madx")
    prepare_pyorbit3_runtime(paths, Path("/tmp/sis18_ptc_runtime"))
    plots = output / "plots"
    tables = output / "tables"
    summaries = {}
    generated_plots: list[str] = []
    current_plots: dict[str, Path] = {}
    comparison_payload: dict[str, dict] = {}
    reference = maybe_reference_root(args.reference_root, comparison_enabled=not args.skip_reference_comparison)
    reference_artifacts: dict[str, str] = {}
    for plane, bare_tune in (("x", config.qx), ("y", config.qy)):
        trajectories, amplitudes, _, summary = _run_plane(flat=flat, inputs=inputs, config=config, plane=plane, particles=particles, turns=turns)
        trajectories_dir = output / "trajectories"
        trajectories_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(trajectories_dir / f"{plane}_turn_by_particle.npz", coordinates=trajectories, turns=np.arange(-1, turns))
        analysis_turns = max(2, turns // 2 - 2)
        pynaff, fft = _extract_tunes(trajectories, plane=plane, analysis_turns=analysis_turns)
        _write_table(tables / f"tunes_{plane}.csv", amplitudes, pynaff, fft, bare_tune)
        current = _current_plot(plots / f"{plane}_tune_vs_launch_amplitude.png", plane=plane, amplitudes=amplitudes, pynaff=pynaff, fft=fft, bare_tune=bare_tune)
        generated_plots.append(str(current))
        current_plots[plane] = current
        summaries[plane] = {**summary, "analysis_turns": analysis_turns, "pynaff_particles": len(pynaff)}
        if reference is not None:
            reference_output = reference / "Step2" / "output"
            legacy_table = reference_output / f"SIS18_Step2_{plane}_I=2.95e10_Tunes_OnData.txt"
            legacy_plot = reference_output / f"SIS18_Step2_{plane}_I=2.95e10_Q{'x' if plane == 'x' else 'y'}.png"
            legacy = np.loadtxt(legacy_table)
            candidate = np.column_stack((amplitudes[1:, 1], pynaff))
            comparison = compare_tune_tables(legacy, candidate)
            overlay = _overlay_plot(plots / f"legacy_vs_current_{plane}_numeric_overlay.png", plane=plane, legacy=legacy, amplitudes=amplitudes, pynaff=pynaff, fft=fft)
            side_by_side = plot_legacy_comparison(legacy_plot, current, plots / f"legacy_vs_current_{plane}_side_by_side.png", title=f"SIS18 Step 2 {plane}-plane tunes")
            generated_plots.extend((str(overlay), str(side_by_side)))
            comparison_payload[plane] = comparison.__dict__
            reference_artifacts.update({str(legacy_table): sha256_file(legacy_table), str(legacy_plot): sha256_file(legacy_plot)})
    website_manifest = json.loads((WEBSITE_REFERENCE_DIR / "reference_manifest.json").read_text(encoding="utf-8"))
    for entry in website_manifest["plots"]:
        reference_artifacts[entry["file"]] = sha256_file(WEBSITE_REFERENCE_DIR / entry["file"])
    for plane, entry in zip(("x", "y"), website_manifest["plots"]):
        public_comparison = plot_labeled_comparison(
            WEBSITE_REFERENCE_DIR / entry["file"],
            current_plots[plane],
            plots / f"website_vs_current_{plane}_same_axes.png",
            title=f"SIS18 Step 2 {plane}-plane tunes",
            left_label="Original GSI reference",
            right_label="PTC-PyORBIT3",
        )
        generated_plots.append(str(public_comparison))
    (output / "comparison.json").write_text(json.dumps(comparison_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "comparison.md").write_text("# Step 2 comparison\n\n- Historical numeric tune tables are compared with PyNAFF.\n- FFT is a diagnostic cross-check only.\n- Public source: " + website_manifest["source_page"] + "\n", encoding="utf-8")
    (output / "tracking_summary.json").write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = write_run_manifest(output / "manifest.json", {"step": 2, "profile": args.profile, "command": sys.argv, "particles_per_plane": particles, "turns": turns, "mpi_size": 1, "seed": config.seed, "flat_file": str(flat), "flat_file_sha256": sha256_file(flat), "packaged_inputs": {str(path.name): sha256_file(path) for path in staged}, "reference_artifacts": reference_artifacts, "comparison_enabled": reference is not None, "comparison": comparison_payload, "lattice": summaries, "space_charge": "analytical_frozen_gaussian", "sextupole_enabled": False, "code_revisions": {"benchmark": _revision(ROOT), "pyorbit3": _revision(paths.pyorbit3_root), "ptc": _revision(paths.pyorbit3_root.parent / "PTC")}, "plots": generated_plots})
    print(f"Step 2 {args.profile} complete: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
