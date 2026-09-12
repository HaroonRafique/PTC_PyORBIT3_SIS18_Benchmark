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
| Steps 2, 4–5 smoke/reference comparisons | pending |
| Steps 6–8 smoke/reference comparisons | pending |
| Step 9 smoke/reference comparison | pending |
| Promotion audit for `ptc_pyorbit3_examples/common` | pending |

## Layout

- `shared_inputs/`: shared profiles, artifact manifest, MAD-X/PTC templates.
- `common/`: portable helpers designed against the active examples suite.
- `step_01_*` through `step_09_*`: independently runnable benchmark cases;
  each owns versioned `legacy_input/`, versioned generated `input/`, and
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
