#!/usr/bin/env python
"""Run SIS18 Step 5: sextupole-on frozen-space-charge phase-space island."""

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
from common.poincare_distribution import horizontal_poincare_coordinates
from common.poincare_plots import plot_poincare_views
from common.reference_artifacts import maybe_reference_root, sha256_file, stage_packaged_inputs
from common.sis18_config import load_step_config
from common.sis18_lattice import in_workdir, load_sis18_lattice

STEP_DIR = Path(__file__).resolve().parent
WEBSITE_REFERENCE_DIR = ROOT / "shared_inputs" / "reference_plots" / "step_05"
EPSN_X, EPSN_Y = 4.91e-7, 3.635e-7
DPP_RMS, BUNCH_LENGTH_RMS_M = 2.5e-4 / 3.0, 40.206868
RESTORING_FORCE, SC_PATH_LENGTH_MIN_M = -1.951e-11, 1.0e-8


def phase_space_limits() -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the Step 5 horizontal physical window in mm and mrad."""

    return ((-50.0, 50.0), (-5.0, 5.0))


def reference_launch_extent_sigma(*, particles: int) -> float:
    """Return the largest legacy ``i/N`` launch amplitude in sigma."""

    if particles < 1:
        raise ValueError("particles must be positive")
    return 4.0 * (particles - 1) / particles


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


def _snapshot_by_id(bunch, particles: int) -> np.ndarray:
    snapshot = np.full((particles, 6), np.nan)
    for index in range(bunch.getSize()):
        particle_id = int(round(bunch.partAttrValue("ParticleIdNumber", index, 0)))
        if 0 <= particle_id < particles:
            snapshot[particle_id] = (bunch.x(index), bunch.xp(index), bunch.y(index), bunch.yp(index), bunch.z(index), bunch.dE(index))
    return snapshot


def _surviving_ids(snapshot: np.ndarray) -> set[int]:
    return set(np.flatnonzero(np.isfinite(snapshot[:, 0])))


def _run(*, flat: Path, inputs: Path, config, particles: int, turns: int):
    lattice, bunch = load_sis18_lattice(flat)
    from ext.ptc_orbit.ptc_orbit import readScriptPTC
    with in_workdir(inputs / "Input"):
        readScriptPTC("time.ptc")
    sc_nodes = _install_historical_model(lattice, config)
    coordinates = horizontal_poincare_coordinates(n_particles=particles, n_sigma=4.0, betax=lattice.betax0, epsn_x=EPSN_X, beta_rel=bunch.getSyncParticle().beta(), gamma_rel=bunch.getSyncParticle().gamma())
    bunch.addPartAttr("macrosize"); bunch.addPartAttr("ParticleIdNumber")
    for coordinate in coordinates:
        bunch.addParticle(*coordinate)
    for index in range(bunch.getSize()):
        bunch.partAttrValue("macrosize", index, 0, config.intensity / particles); bunch.partAttrValue("ParticleIdNumber", index, 0, index)
    from orbit.core.bunch import Bunch
    lostbunch = Bunch(); bunch.copyEmptyBunchTo(lostbunch); lostbunch.addPartAttr("ParticlePhaseAttributes"); lostbunch.addPartAttr("LostParticleAttributes")
    snapshots, first_lost = [_snapshot_by_id(bunch, particles)], np.full(particles, -1, dtype=int)
    parameters = {"bunch": bunch, "lostbunch": lostbunch, "length": lattice.getLength() / lattice.nHarm}; previous_ids = _surviving_ids(snapshots[-1])
    for turn in range(1, turns + 1):
        lattice.trackBunch(bunch, parameters); _apply_restoring_force(bunch); snapshot = _snapshot_by_id(bunch, particles); current_ids = _surviving_ids(snapshot)
        for particle_id in previous_ids - current_ids:
            first_lost[particle_id] = turn
        snapshots.append(snapshot); previous_ids = current_ids
    return np.asarray(snapshots), coordinates, first_lost, {"nodes": lattice.nNodes, "length_m": lattice.getLength(), "sc_nodes": len(sc_nodes), "survivors": len(previous_ids)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "reference"), default="smoke"); parser.add_argument("--output-dir", type=Path, default=STEP_DIR / "output"); parser.add_argument("--reference-root", type=Path); parser.add_argument("--skip-reference-comparison", action="store_true"); parser.add_argument("--madx", type=Path)
    args = parser.parse_args(argv); config = load_step_config(STEP_DIR / "config.json", step=5, profile=args.profile); particles, turns = config.n_macroparticles, config.turns
    if particles < 1 or turns < 1: raise ValueError("Step 5 requires at least one particle and one turn")
    output, inputs = args.output_dir.resolve(), STEP_DIR / "input" / "generated" / args.profile / "madx"; paths = resolve_runtime_paths(madx=args.madx or Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00"))
    staged = stage_packaged_inputs(source=STEP_DIR / "legacy_input", destination=inputs / "Input"); flat = generate_flat_file(madx=paths.madx, workdir=inputs, madx_input=inputs / "Input" / "SIS18.madx"); prepare_pyorbit3_runtime(paths, Path("/tmp/sis18_ptc_runtime"))
    snapshots, coordinates, first_lost, summary = _run(flat=flat, inputs=inputs, config=config, particles=particles, turns=turns)
    trajectories_dir, tables, plots = output / "trajectories", output / "tables", output / "plots"; trajectories_dir.mkdir(parents=True, exist_ok=True); tables.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(trajectories_dir / "poincare_turn_by_particle.npz", coordinates=snapshots, turns=np.arange(turns + 1), launch_coordinates=coordinates)
    with (tables / "lost_particles.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(("particle_id", "launch_x_m", "first_lost_turn")); [writer.writerow((particle_id, coordinates[particle_id, 0], first_lost[particle_id])) for particle_id in np.flatnonzero(first_lost >= 0)]
    full, zoom = plot_poincare_views(snapshots[1:], plots, horizontal_limits=phase_space_limits()); reference = maybe_reference_root(args.reference_root, comparison_enabled=not args.skip_reference_comparison)
    reference_artifacts: dict[str, str] = {}; plot_paths = [str(full), str(zoom)]; comparison_text = "# Step 5 comparison\n\n- Visual-only topology comparison: central orbit, three islands, and physical extent.\n"
    if reference is not None:
        reference_output = reference / "Step5" / "output"; full_reference = reference_output / "Poincare_Dist_SIS18_Step5.png"; zoom_reference = reference_output / "Poincare_Dist_SIS18_Step5_zoom.png"; full_comparison = plot_legacy_comparison(full_reference, full, plots / "legacy_vs_current_full.png", title="SIS18 Step 5 phase space"); zoom_comparison = plot_legacy_comparison(zoom_reference, zoom, plots / "legacy_vs_current_zoom.png", title="SIS18 Step 5 horizontal phase space")
        website_manifest = json.loads((WEBSITE_REFERENCE_DIR / "reference_manifest.json").read_text(encoding="utf-8")); website_references = [*((entry["label"], WEBSITE_REFERENCE_DIR / entry["file"]) for entry in website_manifest["plots"]), ("PTC-PyORBIT2", zoom_reference)]; website_comparison = plot_same_axes_references(current=zoom, references=website_references, output=plots / "website_vs_current_horizontal_phase_space.png")
        reference_artifacts = {path.name: sha256_file(path) for path in (full_reference, zoom_reference, *(path for _, path in website_references))}; plot_paths.extend((str(full_comparison), str(zoom_comparison), str(website_comparison))); comparison_text += "- Public source: " + website_manifest["source_page"] + "\n- Synergia is contextual only because its source notes non-frozen longitudinal motion.\n"
    (output / "comparison.md").write_text(comparison_text, encoding="utf-8"); (output / "tracking_summary.json").write_text(json.dumps({**summary, "lost_particles": int((first_lost >= 0).sum()), "launch_extent_sigma": reference_launch_extent_sigma(particles=particles)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = write_run_manifest(output / "manifest.json", {"step": 5, "profile": args.profile, "command": sys.argv, "particles": particles, "turns": turns, "mpi_size": 1, "seed": config.seed, "flat_file": str(flat), "flat_file_sha256": sha256_file(flat), "packaged_inputs": {path.name: sha256_file(path) for path in staged}, "reference_artifacts": reference_artifacts, "comparison_enabled": reference is not None, "comparison": "visual_topology_only", "lattice": summary, "space_charge": "analytical_frozen_gaussian", "sextupole_enabled": True, "code_revisions": {"benchmark": _revision(ROOT), "pyorbit3": _revision(paths.pyorbit3_root), "ptc": _revision(paths.pyorbit3_root.parent / "PTC")}, "plots": plot_paths})
    print(f"Step 5 {args.profile} complete: {manifest}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
