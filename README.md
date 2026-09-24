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
| Step 2 frozen-space-charge tune scan | reference run and numeric comparison recorded; plot/scientific review pending |
| Step 3 sextupole-on tune scan | reference run numerically agrees; plot regeneration/visual review pending |
| Step 4 resonance-crossing tune scan | reference run recorded; horizontal residual requires scientific review |
| Step 5 phase-space island | reference run recorded; visual-topology review pending |
| Step 6 slow trapping | published reference run recorded; legacy-artifact numeric run and visual review pending |
| Step 7 fast trapping | 5.15-mm reference rerun recorded; first-oscillation action reaches 1.5006; visual scientific review pending |
| Step 8 long-term trapping | reference run recorded; **blocked** by numeric disagreement and source-duration conflict |
| Step 9 full-bunch emittance evolution | reference run recorded; report-only/manual scientific review pending |
| Promotion audit for `ptc_pyorbit3_examples/common` | pending |

## Layout

- `shared_inputs/`: artifact manifest, MAD-X/PTC templates, and public plot references.
- `common/`: portable helpers designed against the active examples suite.
- `step_01_*` through `step_09_*`: independently runnable benchmark cases;
  each owns authoritative `config.json`, versioned `legacy_input/`, versioned generated `input/`, and
  step-local `output/` artifacts (normally ignored, with benchmark evidence retained when tracked).
- `BENCHMARK_PLAN.md`: live execution/checklist status and documented blockers.
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

All nine step directories provide this normal interface:

```bash
cd step_01_phase_space_stability
./run_example.sh --profile smoke
./run_example.sh --profile reference
./run_example.sh --profile smoke --skip-reference-comparison

cd ../step_02_tunes_no_sextupole
SIS18_REFERENCE_ROOT=/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark ./run_example.sh --profile smoke
SIS18_REFERENCE_ROOT=/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark ./run_example.sh --profile reference
```

Use smoke profiles before reference profiles. Reference output does not itself
complete a benchmark step: the required numeric or visual review must also be
recorded, and disagreements remain blockers. The current detailed evidence and
open review items are maintained in `BENCHMARK_PLAN.md` and each step's tracked
`output/` manifest and comparison files.

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
resonance islands. Rebuild those plots from the saved reference trajectory
without tracking via `./step_05_phase_space_island/run_example.sh --profile
reference --plot-only` (with `SIS18_REFERENCE_ROOT` set for legacy panels).

Step 6 follows one particle for one 15,000-turn synchrotron oscillation with
the frozen-Gaussian slow-trapping model. Its published reference launch is
`x=5 mm`, `z=2.5 sigma_z` at `(Qx, Qy) = (4.3504, 3.2)`. The historical stored
trajectory instead launches at `x=0`, so `--profile legacy_artifact` reproduces
that incompatible artifact for numeric diagnostics while `--profile reference`
remains the scientific benchmark. The original GSI action raster is packaged
with URL and SHA-256 provenance. The complete 22-page official GSI THBW01
deck is versioned under `shared_inputs/reference_slides/THBW01/`; its uncropped
page 15 is compared alongside the Step 6 action plot. Rebuild all Step 6 plots
from the saved reference records, without tracking, via
`./step_06_slow_trapping/run_example.sh --profile reference --plot-only` (with
`SIS18_REFERENCE_ROOT` set for legacy panels).

Step 7 is the fast-synchrotron counterpart: one particle launches at
`x=5.15 mm`, `z=2.5 sigma_z` in the frozen-Gaussian model at `(Qx, Qy) =
(4.3504, 3.2)` and restoring force `-4.38975e-09`. It tracks 2,000 turns,
while its public comparison action plot shows the first 1,000 turns at the
published axes. The archived Step 7 script uses `x=5.1 mm`; the current
5.15-mm launch is a documented exploratory retune. The rerun reaches a
first-oscillation normalized-action maximum of `1.5006` without particle loss.
The historical artifacts contain only PNGs, so comparison is visual: a compact
panel packages the original GSI SIMPSONS and MICROMAP rasters with the legacy
PTC-PyORBIT2 and current plots. The expected fast regime is scattering rather
than adiabatic trapping.

Step 8 extends the scattering/trapping study to the published 100,000-turn
case at `Qs=1e-3`, using the published Step 7 launch `x=5 mm`,
`z=2.5 sigma_z` and `(Qx, Qy) = (4.3504, 3.2)`. Its archived legacy trajectory
is instead 200,000 turns long, so `reference` compares the matching
100,000-turn prefix while `legacy_artifact` runs all 200,000 turns. The full
official GSI Step 8 slide labels 100,000 turns but its plotted x-axis reaches
200,000 turns; this source conflict is retained in the comparison report.
Numeric trajectory data remains external and read-only.

Step 9 is the full-bunch emittance-evolution case. Its website-authoritative
`reference` profile tracks 1,000 seeded matched-Gaussian macroparticles for
100,000 turns at `(Qx, Qy) = (4.3604, 3.2)`, with the historical frozen
analytical space-charge and restoring-force model. It uses the examples-style
MPI launcher (four ranks by default), balanced local particle shares, and a
global-count macrosize. The original tomoscope input is unavailable, so this
deterministic replacement is explicitly recorded rather than presented as a
replay. The archived external `.mat` artifact used 10,000 particles at the
same tune and remains a numeric diagnostic only. The separate official GSI
final-emittance estimate of 2.08 applies to an analytical estimate at
`Qx=4.3504`, not to the empirical 1,000-particle website plot; the reference
result is report-only pending scientific review. Each comparison also includes
the archived PyORBIT2.7 multi-code overlay (MICROMAP, SIMPSONS, and
MADX+fsc3d) beside a same-axis reconstruction that draws PyORBIT2.7 in blue
and the current result in thick magenta over the raw historical raster. The
external source PNGs are hashed in the run manifest.
