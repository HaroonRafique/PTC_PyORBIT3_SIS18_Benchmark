# SIS18 PTC-PyORBIT3 Benchmark

This repository reproduces Giuliano Franchetti's SIS18 space-charge trapping
benchmark with current PTC-PyORBIT3. It modernises the historical Python-2
workflow while retaining its physics cases, run settings, and comparison
intent.

Primary historical references:

- [Giuliano Franchetti's SIS18 benchmark documentation](https://web-docs.gsi.de/~giuliano/research_activity/trapping_benchmarking/main.html)
- [Original PTC-PyORBIT SIS18 benchmark implementation](https://github.com/HaroonRafique/PTC_PyORBIT_SIS18_Benchmark)

## Status

| Milestone | Status |
| --- | --- |
| Governance, plan, and repository layout | complete |
| Shared configuration and legacy manifests | complete |
| PTC runtime and lattice smoke check | complete |
| Step 1 smoke/reference comparison | complete |
| Step 2 frozen-space-charge tune scan | smoke complete; reference pending |
| Step 3 sextupole-on tune scan | smoke complete; reference pending |
| Step 4 resonance-crossing tune scan | smoke complete; reference pending |
| Step 5 phase-space island | smoke complete; reference pending |
| Step 6 slow trapping | smoke complete; reference and legacy-artifact runs pending |
| Step 7 fast trapping | smoke complete; reference and visual review pending |
| Step 8 long-term trapping | pending |
| Step 9 smoke/reference comparison | pending |
| Promotion audit for `ptc_pyorbit3_examples/common` | pending |

## Layout

- `shared_inputs/`: artifact manifest, MAD-X/PTC templates, and public plot references.
- `common/`: portable helpers designed against the active examples suite.
- `step_01_*` through `step_09_*`: independently runnable benchmark cases;
  each owns authoritative `config.json`, versioned `legacy_input/`, versioned generated `input/`, and
  ignored `output/` artifacts.
- `BENCHMARK_PLAN.md`: live execution/checklist status.
- `docs/superpowers/`: approved design and detailed implementation plan.

## Runtime and reference policy

Each step tracks its historical MAD-X/PTC sources in `legacy_input/` and the
verified generated MAD-X/PTC workspace in `input/generated/`; no historical
input checkout is required to run it. Historical output artifacts remain
read-only and external. Set `SIS18_REFERENCE_ROOT` to override the default
`/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark` when generating comparison
plots. The default MAD-X binary is
`../ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00`; it can be
overridden in an example configuration. Every run writes its configuration,
input hashes, command, MPI size, seed, code revisions, and reference hashes
when used to its step-local manifest.

The normal interface, once the runners exist, is:

```bash
cd step_01_phase_space_stability
./run_example.sh --profile smoke
./run_example.sh --profile reference
./run_example.sh --profile smoke --skip-reference-comparison

cd ../step_02_tunes_no_sextupole
SIS18_REFERENCE_ROOT=/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark ./run_example.sh --profile smoke
SIS18_REFERENCE_ROOT=/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark ./run_example.sh --profile reference
```

Use smoke profiles before reference profiles. Steps 8 and 9 remain gated until
their prior steps have verified reference outputs.

Step 2 requires the declared `PyNAFF` dependency. It tracks the horizontal and
vertical frozen-space-charge scans sequentially, writes PyNAFF-compatible
numeric comparisons plus an FFT cross-check, and packages original GSI plot
references with source URLs and SHA-256 digests.

Step 3 is ready to run. It uses the sextupole-on historical lattice, frozen
analytical Gaussian space charge, and public bare tunes `(Qx, Qy) = (4.338,
3.2)`. Its horizontal scan launches through `3.3 sigma`; its vertical scan
launches through `4.0 sigma`. It records aperture losses by particle ID rather
than silently changing a tune table, compares surviving PyNAFF values to the
external legacy tables, and packages the two original GSI plots.

```bash
cd step_03_tunes_with_sextupole
SIS18_REFERENCE_ROOT=/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark ./run_example.sh --profile smoke
```

Step 4 uses the same frozen-space-charge and sextupole-on model at bare tunes
`(Qx, Qy) = (4.3504, 3.2)`, near the horizontal third-order resonance. Both
planes launch through `4.0 sigma`; comparison plots retain the historical
resonance windows and use the external numeric tune tables plus packaged GSI
rasters.

Step 5 is a horizontal 16-particle Poincare study at `(Qx, Qy) = (4.3504,
3.2)`. It preserves the historical `i/N × 4 sigma_x` launch, frozen
space-charge model, 10 m aperture, and restoring force. Its plots use mm and
mrad over the historical `[-50, 50] mm × [-5, 5] mrad` window, alongside the
legacy PTC-PyORBIT2 plots and original GSI MICROMAP, SIMPSONS, and Synergia
rasters. There is no usable historical particle table, so reference completion
requires visual agreement of the physical extent, central orbit, and the three
resonance islands.

Step 6 follows one particle for one 15,000-turn synchrotron oscillation with
the frozen-Gaussian slow-trapping model. Its published reference launch is
`x=5 mm`, `z=2.5 sigma_z` at `(Qx, Qy) = (4.3504, 3.2)`. The historical stored
trajectory instead launches at `x=0`, so `--profile legacy_artifact` reproduces
that incompatible artifact for numeric diagnostics while `--profile reference`
remains the scientific benchmark. The original GSI action raster is packaged
with URL and SHA-256 provenance.

Step 7 is the fast-synchrotron counterpart: one particle launches at
`x=5.1 mm`, `z=2.5 sigma_z` in the frozen-Gaussian model at `(Qx, Qy) =
(4.3504, 3.2)` and restoring force `-4.38975e-09`. It tracks 2,000 turns,
while its public comparison action plot shows the first 1,000 turns at the
published axes. The historical artifacts contain only PNGs, so comparison is
visual: a compact panel packages the original GSI SIMPSONS and MICROMAP
rasters with the legacy PTC-PyORBIT2 and current plots. The expected fast
regime is scattering rather than adiabatic trapping.
