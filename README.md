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
| Steps 1–5 smoke/reference comparisons | pending |
| Steps 6–8 smoke/reference comparisons | pending |
| Step 9 smoke/reference comparison | pending |
| Promotion audit for `ptc_pyorbit3_examples/common` | pending |

## Layout

- `shared_inputs/`: shared profiles, artifact manifest, MAD-X/PTC templates.
- `common/`: portable helpers designed against the active examples suite.
- `step_01_*` through `step_09_*`: independently runnable benchmark cases;
  each owns its `input/` staging and `output/` artifacts.
- `BENCHMARK_PLAN.md`: live execution/checklist status.
- `docs/superpowers/`: approved design and detailed implementation plan.

## Runtime policy

The legacy checkout is read only. Set `SIS18_LEGACY_ROOT` to override the
default `/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark`. The default MAD-X
binary is `../ptc_pyorbit3_examples/tools/madx/madx-linux64_v5_02_00`; it can
be overridden in an example configuration. Every run writes its configuration,
input hashes, command, MPI size, seed, and code revisions to its step-local
manifest.

The normal interface, once the runners exist, is:

```bash
cd step_01_phase_space_stability
./run_example.sh --profile smoke
./run_example.sh --profile reference --mpi-procs 2
```

Use smoke profiles before reference profiles. Steps 8 and 9 remain gated until
their prior steps have verified reference outputs.
