# SIS18 Benchmark Live Checklist

The detailed, task-level implementation plan is
`docs/superpowers/plans/2026-09-08-sis18-benchmark.md`; the accepted design is
`docs/superpowers/specs/2026-09-08-sis18-benchmark-design.md`.

## Live status

- [x] Repository governance and directory layout.
- [x] Shared profiles, legacy staging, and manifests.
- [x] PTC-enabled runtime/lattice smoke check: MAD-X 5.02 generated and PTC
  loaded the Step 1 lattice (504 nodes, 216.7199934718 m, gamma 1.01215003).
- [x] Step 1: phase-space stability (smoke and 20-particle/1,024-turn reference run).
- [ ] Step 2: tunes without sextupole.
- [ ] Step 3: tunes with sextupole.
- [ ] Step 4: resonance-crossing tunes.
- [ ] Step 5: phase-space island.
- [ ] Step 6: slow trapping.
- [ ] Step 7: fast trapping.
- [ ] Step 8: long-term trapping.
- [ ] Step 9: bunch emittance evolution.
- [ ] Reference campaign and examples-helper promotion audit.

## Completion rule

A step is complete only after its test-first implementation, smoke run,
required plots, reference comparison, manifest, and README status update have
fresh verification evidence. Record blockers and physics discrepancies here
before changing the next step.

## Input and reference artifact policy

Each step versions its exact legacy MAD-X/PTC source files in `legacy_input/`
and its verified generated MAD-X/PTC workspace in `input/generated/`.
Historical result artifacts are not copied: comparisons read them in place from
`SIS18_REFERENCE_ROOT` and record their hashes in the run manifest.

Step 1's smoke and reference MAD-X/PTC workspaces were regenerated from its
versioned local inputs on 2026-09-11; both record the 504-node,
216.7199934718 m SIS18 PTC lattice.
