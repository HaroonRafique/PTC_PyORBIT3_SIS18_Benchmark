# SIS18 PTC-PyORBIT3 Benchmark Design

## Goal

Reproduce the full nine-step historical SIS18 benchmark using current
PTC-PyORBIT3 and compare each new result to the original checkout without
copying the legacy repository into this project.

## Architecture

Shared configuration, runtime staging, PTC tracking, diagnostics, plotting,
and comparison utilities live in `common/`. Each step is a self-contained
example directory with its own config, runner, staged inputs, and outputs.
The public shape mirrors `ptc_pyorbit3_examples`; helpers remain independent
so generic components can be promoted to that suite's `common/` package.

## Data flow

1. Resolve external legacy source and current runtime paths.
2. Stage and hash only the requested legacy input files in the chosen step.
3. Generate/load the local PTC flat file and validate the PTC runtime.
4. Generate the specified bunch/particle distribution and track it.
5. Store structured diagnostics and generated plots in the step output.
6. Load external legacy artifacts, calculate numerical or qualitative metrics,
   and write a side-by-side comparison plus manifest.

## Benchmark cases

Steps 1/5 are Poincare stability/island studies; Steps 2–4 are transverse
tune-versus-amplitude studies; Steps 6–8 are slow/fast/long-term
single-particle trapping studies; Step 9 is frozen-space-charge 3D Gaussian
bunch emittance evolution. Smoke profiles preserve the physical switch set but
reduce cost; reference profiles retain legacy particle/turn settings.

## Acceptance

All runner outputs must be step-local and include manifest, diagnostics,
required plot set, comparison summary, and reproducibility identifiers.
Numerical comparison is mandatory for stored tune and usable particle/MAT data;
visual/derived-boundary comparison is recorded for image-only references.
