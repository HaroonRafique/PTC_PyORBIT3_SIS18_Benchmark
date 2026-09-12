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
- [ ] Step 2: frozen-space-charge tunes without sextupole (smoke complete;
  reference run and review pending).
- [ ] Step 3: tunes with sextupole (implementation ready; user smoke run pending).
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

Step 1's external reference retains PNG plots but no `.mat` particle data, so
its comparison remains side-by-side visual panels. The legacy Python 2.7
PTC-PyORBIT environment is not rerun to reconstruct those artifacts.

Step 2 uses frozen analytical Gaussian space charge at `z=dE=0`, with the
sextupole disabled and public bare tunes `(Qx, Qy) = (4.338, 3.2)`. Its
historical numeric `Tunes_OnData.txt` tables remain external and are read via
`SIS18_REFERENCE_ROOT`; the two original GSI raster plots are versioned with
their URLs and SHA-256 digests. A verified run must stage and commit its local
`input/generated/<profile>/madx/` workspace before this checklist item can be
completed.

The Step 2 smoke profile completed on 2026-09-11 with 8 particles per plane
for 32 turns, a 504-node / 216.7199934718 m PTC lattice, and 504 frozen-SC
nodes per plane. It writes both PyNAFF and FFT tune tables plus the required
numeric and visual comparisons; its reference-profile run remains pending.

Step 3 is prepared from the versioned sextupole-on local inputs and does not
load `chrom.ptc`. It preserves the historical frozen analytical-Gaussian
model, `z=dE=0` launch, 10 m transverse apertures, and restoration force. The
asymmetric historical scan limits are 3.3 sigma horizontally and 4.0 sigma
vertically. A run writes ID-indexed trajectories and `lost_particles_<plane>.csv`;
only fully tracked IDs are eligible for its PyNAFF/FFT numeric tables. The
external Step 3 tune tables and original GSI plots are read through
`SIS18_REFERENCE_ROOT` and `shared_inputs/reference_plots/step_03`,
respectively. Smoke execution and review remain user-owned.
