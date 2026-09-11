# SIS18 PTC-PyORBIT3 Benchmark Agent Instructions

## Purpose

This repository reproduces the nine-step SIS18 PTC-PyORBIT benchmark using the
current PTC-enabled PyORBIT3 stack. The scientific objective is to validate
space-charge-induced trapping, tune behaviour, and long-term emittance
evolution against the historical benchmark, not to preserve Python-2 code.

Read `README.md`, `BENCHMARK_PLAN.md`, and the detailed Superpowers documents
under `docs/superpowers/` before non-trivial work.

## Authoritative sibling repositories

- `../PyORBIT3`, branch `PTC`: runtime and PTC integration source of truth.
- `../PTC`: PTC source of truth. Do not edit PTC Fortran sources for this
  benchmark unless the user explicitly requests it.
- `../ptc_pyorbit3_examples`: the required reference for Python structure,
  configuration, MPI, PTC tracking, diagnostics, plotting, and output
  conventions. Do not import it at runtime or alter its unrelated worktree.
- `/home/hr/Repositories/PTC_PyORBIT_SIS18_Benchmark`: read-only historical
  result artifacts only. Resolve it through `SIS18_REFERENCE_ROOT`; never
  write to it or copy its outputs into this repository.
- `/home/hr/Repositories/superpowers`: required development methodology.

## Required development method

- Before plan changes, read and follow
  `skills/writing-plans/SKILL.md` in the Superpowers repository.
- For implementation, use `skills/executing-plans/SKILL.md` task by task.
- Before production Python changes, follow
  `skills/test-driven-development/SKILL.md`: add one focused test, run it and
  observe the expected failure, then implement the smallest passing change.
- For every test/build/runtime/physics failure, follow
  `skills/systematic-debugging/SKILL.md` before attempting a fix.
- Before claiming a milestone or committing a completed task, follow
  `skills/verification-before-completion/SKILL.md` and retain fresh command
  evidence.
- This repository uses **one working branch only: `main`**. Do not create,
  switch to, or ask the user to use feature branches or Git worktrees unless
  the user explicitly changes this rule. Keep commits small and logical on
  `main`, and leave the default checkout directly runnable.

## Repository rules

- `shared_inputs/` contains shared configuration and non-generated common
  inputs. Generic helpers live in `common/`; step-specific policy belongs in
  the individual step configuration/runner.
- Every `step_XX_*` directory is independently runnable and contains a local
  `example_config.json`, zero-argument `run_example.sh`, readable Python
  runner, tracked `legacy_input/`, tracked `input/generated/`, and ignored
  `output/`. Generated artifacts must stay beneath that step directory.
- Each `legacy_input/` contains the exact historical MAD-X/PTC inputs needed
  by its step. Copy its files only into that step's tracked
  `input/generated/<profile>/madx/Input/` workspace; commit both directories
  after verified generation, including the MAD-X log and PTC flat file.
- Do not vendor the 155 MB legacy repository or copy/write its outputs. Read
  historical output data and plots in place through `SIS18_REFERENCE_ROOT`
  solely to make comparisons, and hash every referenced artifact in the run
  manifest.
- Public original-code reference plots may be versioned under
  `shared_inputs/reference_plots/` only with their source URL and SHA-256
  digest recorded beside them; do not treat a raster image as numeric data.
- Design generic helpers so they can be moved to
  `ptc_pyorbit3_examples/common/` unchanged or with a thin adapter: accept
  explicit paths/configuration, use public docstrings/types, and contain no
  SIS18 absolute paths or step-number assumptions.
- Mirror the Examples repository’s sampled-line marker policy and its MPI
  global-count semantics. Keep PTC dispersion/unit conversions explicit.
- From Step 2 onward, the user runs example commands to conserve agent-token
  budget. Do not launch a Step 2–9 runtime command unless the user explicitly
  requests it; wait for the user to report runtime results and request
  debugging before investigating a runtime failure.
- Comparison plots must use identical axis limits and axis ratios for matching
  observables, with distinct colours and marker styles for each implementation.
  When a legacy output has numeric data, write both a labelled side-by-side
  comparison and a separate same-axis data overlay for inspection. Do not
  digitize a legacy raster image and represent it as numeric data.
- Step 1's retained historical output has no `.mat` particle data. Keep its
  comparison as labelled side-by-side PNG panels; do not rerun the legacy
  Python 2.7 PTC-PyORBIT stack to reconstruct data.
- Update the root README and `BENCHMARK_PLAN.md` after every verified smoke,
  reference, comparison, or blocking discovery.

## Required reproducibility evidence

Each run must record resolved configuration, command, profile, seed, MPI size,
MAD-X path/version, PyORBIT3 and PTC commit IDs, packaged/generated
input hashes, reference-artifact hashes when compared, PTC lattice summary,
structured diagnostics, plots, and comparison outcome.

## Benchmark scope

Implement all legacy Steps 1–9. Run deterministic smoke profiles before
historical reference profiles. Compare stored tune/particle/MAT data
numerically where available, and use documented qualitative/derived-boundary
comparisons for plots without tabular source data. Full Steps 8 and 9 are
gated by passing smoke results and prior reference review.
