#!/usr/bin/env python
"""Run SIS18 Step 1: no-space-charge horizontal Poincare stability."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.environment import prepare_pyorbit3_runtime, resolve_runtime_paths
from common.reference_artifacts import maybe_reference_root, sha256_file, stage_packaged_inputs
from common.madx import generate_flat_file
from common.manifest import write_run_manifest
from common.legacy_plot_comparison import plot_legacy_comparison, plot_same_axes_references
from common.poincare_distribution import horizontal_poincare_coordinates
from common.poincare_plots import plot_poincare_views
from common.sis18_config import load_step_config
from common.sis18_lattice import load_sis18_lattice

STEP_DIR = Path(__file__).resolve().parent
WEBSITE_REFERENCE_DIR = ROOT / "shared_inputs" / "reference_plots" / "step_01"


@contextmanager
def workdir(path: Path):
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def snapshot(bunch) -> np.ndarray:
    return np.array([[bunch.x(i), bunch.xp(i), bunch.y(i), bunch.yp(i), bunch.z(i), bunch.dE(i)] for i in range(bunch.getSize())])


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

    config = load_step_config(ROOT / "shared_inputs" / "benchmark_profiles.json", step=1, profile=args.profile)
    particles = args.particles if args.particles is not None else config.n_macroparticles
    turns = args.turns if args.turns is not None else config.turns
    output = args.output_dir.resolve()
    inputs = STEP_DIR / "input" / "generated" / args.profile / "madx"
    paths = resolve_runtime_paths(madx=args.madx or Path("/home/hr/Codes/PTC_PyORBIT3_Codex_Merge_Jul26/ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00"))
    staged = stage_packaged_inputs(source=STEP_DIR / "legacy_input", destination=inputs / "Input")
    flat = generate_flat_file(madx=paths.madx, workdir=inputs, madx_input=inputs / "Input" / "SIS18.madx")
    prepare_pyorbit3_runtime(paths, Path("/tmp/sis18_ptc_runtime"))
    lattice, bunch = load_sis18_lattice(flat)
    from ext.ptc_orbit.ptc_orbit import readScriptPTC

    with workdir(inputs / "Input"):
        readScriptPTC("time.ptc")
    coords = horizontal_poincare_coordinates(n_particles=particles, n_sigma=6.42, betax=lattice.betax0, epsn_x=4.91e-7, beta_rel=bunch.getSyncParticle().beta(), gamma_rel=bunch.getSyncParticle().gamma())
    bunch.addPartAttr("macrosize")
    for row in coords:
        bunch.addParticle(*row)
    for index in range(bunch.getSize()):
        bunch.partAttrValue("macrosize", index, 0, config.intensity / particles)
    snapshots = [snapshot(bunch)]
    params = {"bunch": bunch, "length": lattice.getLength() / lattice.nHarm}
    for _ in range(turns):
        lattice.trackBunch(bunch, params)
        if bunch.getSize() != particles:
            raise RuntimeError("Step 1 lost particles despite its no-aperture baseline")
        snapshots.append(snapshot(bunch))
    data = np.asarray(snapshots)
    (output / "snapshots").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "snapshots" / "poincare_snapshots.npz", coordinates=data, turns=np.arange(-1, turns))
    plots = output / "plots"
    full, zoom = plot_poincare_views(data[1:], plots)
    reference = maybe_reference_root(args.reference_root, comparison_enabled=not args.skip_reference_comparison)
    reference_artifacts: dict[str, str] = {}
    plot_paths = [str(full), str(zoom)]
    if reference is not None:
        reference_output = reference / "Step1" / "output"
        full_reference = reference_output / "Poincare_Dist_SIS18_Step1.png"
        zoom_reference = reference_output / "Poincare_Dist_SIS18_Step1_zoom.png"
        full_comparison = plot_legacy_comparison(full_reference, full, plots / "legacy_vs_current_full.png", title="SIS18 Step 1 Poincare stability")
        zoom_comparison = plot_legacy_comparison(zoom_reference, zoom, plots / "legacy_vs_current_zoom.png", title="SIS18 Step 1 horizontal phase-space zoom")
        website_manifest = json.loads((WEBSITE_REFERENCE_DIR / "reference_manifest.json").read_text(encoding="utf-8"))
        website_references = [(entry["label"], WEBSITE_REFERENCE_DIR / entry["file"]) for entry in website_manifest["plots"]]
        website_comparison = plot_same_axes_references(current=zoom, references=website_references, output=plots / "website_vs_current_horizontal_phase_space.png")
        (output / "comparison.md").write_text(f"# Step 1 comparison\n\n- Legacy full plot: `{full_reference}`\n- Public original references: `{website_manifest['source_page']}`\n- Survivors: {bunch.getSize()}/{particles}\n- New/legacy panels: `{full_comparison.name}`, `{zoom_comparison.name}`, `{website_comparison.name}`\n- Assessment: no-space-charge baseline; inspect phase-space topology and confirm no losses.\n", encoding="utf-8")
        reference_artifacts = {str(path.name): sha256_file(path) for path in (full_reference, zoom_reference, *(path for _, path in website_references))}
        plot_paths.extend((str(full_comparison), str(zoom_comparison), str(website_comparison)))
    manifest = write_run_manifest(output / "manifest.json", {"step": 1, "profile": args.profile, "particles": particles, "turns": turns, "flat_file": str(flat), "flat_file_sha256": sha256_file(flat), "packaged_inputs": {str(path.name): sha256_file(path) for path in staged}, "reference_artifacts": reference_artifacts, "comparison_enabled": reference is not None, "lattice": {"nodes": lattice.nNodes, "length_m": lattice.getLength()}, "plots": plot_paths})
    (output / "tracking_summary.json").write_text(json.dumps({"survivors": bunch.getSize(), "turns": turns, "max_initial_x_m": float(coords[:, 0].max())}, indent=2) + "\n", encoding="utf-8")
    print(f"Step 1 {args.profile} complete: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
