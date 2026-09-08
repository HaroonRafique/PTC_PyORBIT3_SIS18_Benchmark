# SIS18 Benchmark Live Checklist

The detailed, task-level implementation plan is
`docs/superpowers/plans/2026-09-08-sis18-benchmark.md`; the accepted design is
`docs/superpowers/specs/2026-09-08-sis18-benchmark-design.md`.

## Live status

- [x] Repository governance and directory layout.
- [x] Shared profiles, legacy staging, and manifests.
- [x] PTC-enabled runtime/lattice smoke check: MAD-X 5.02 generated and PTC
  loaded the Step 1 lattice (504 nodes, 216.7199934718 m, gamma 1.01215003).
- [ ] Step 1: phase-space stability.
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
