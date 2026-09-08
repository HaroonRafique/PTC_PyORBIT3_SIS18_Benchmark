# SIS18 PTC-PyORBIT3 Benchmark Implementation Plan

> **For agentic workers:** Follow the Superpowers `executing-plans` workflow.
> Use test-driven development for every production-code change, systematic
> debugging for every failure, and verification-before-completion before any
> milestone claim or commit.

**Goal:** Implement a standalone, all-nine-step SIS18 benchmark suite with
portable helpers and external historical comparisons.

**Architecture:** `common/` supplies reusable, path-configured utilities;
each `step_XX_*` directory supplies a config, runner, local input staging, and
local output. The implementation follows the active Benchmarking Ladder
patterns in `../ptc_pyorbit3_examples` without importing its code at runtime.

**Task order:**

1. Governance/layout and package baseline.
2. Immutable profile configuration, external legacy staging, hashing, and run
   manifests.
3. Current PyORBIT3/PTC environment resolution, MAD-X 5.02 staging, lattice
   load, and smoke check.
4. Portable distributions, diagnostics, plotting, and comparison APIs.
5. Independent Step 1–5 runners and smoke comparisons.
6. Independent Step 6–8 trapping runners and smoke comparisons.
7. Step 9 frozen-Gaussian bunch runner and smoke comparison.
8. Sequential reference campaign, output verifier, and examples promotion
   audit.

For every task: write one minimal failing pytest, run it, implement the
smallest passing behavior, rerun targeted tests, run the appropriate real
smoke command, update `README.md` and `BENCHMARK_PLAN.md`, and commit the
verified logical change. Reference runs may begin only after their smoke
manifest and prerequisite step gates pass.
