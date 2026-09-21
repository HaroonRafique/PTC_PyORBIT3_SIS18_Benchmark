# SIS18 Benchmark Live Checklist

The detailed, task-level implementation plan is
`docs/superpowers/plans/2026-09-08-sis18-benchmark.md`; the accepted design is
`docs/superpowers/specs/2026-09-08-sis18-benchmark-design.md`.

## Live status

- [x] Repository governance and directory layout.
- [x] Shared profiles, legacy staging, and manifests.
- [x] Migrate Steps 8--9 to standalone local `config.json`; Steps 1--7 use local configs.
- [x] PTC-enabled runtime/lattice smoke check: MAD-X 5.02 generated and PTC
  loaded the Step 1 lattice (504 nodes, 216.7199934718 m, gamma 1.01215003).
- [x] Step 1: phase-space stability (smoke and 20-particle/1,024-turn reference run).
- [ ] Step 2: frozen-space-charge tunes without sextupole (smoke complete;
  reference run and review pending).
- [ ] Step 3: tunes with sextupole (smoke complete; reference run and review pending).
- [ ] Step 4: resonance-crossing tunes (smoke complete; reference run and review pending).
- [ ] Step 5: phase-space island (smoke complete; reference run and visual review pending).
- [ ] Step 6: slow trapping (smoke complete; reference and legacy-artifact runs pending).
- [ ] Step 7: fast trapping (smoke complete; reference run and visual review pending).
- [ ] Step 8: long-term trapping (smoke complete; reference and legacy-artifact runs pending).
- [ ] Step 9: bunch emittance evolution (smoke complete; reference and legacy-artifact runs pending).
- [ ] Reference campaign and examples-helper promotion audit.

## Completion rule

A step is complete only after its test-first implementation, smoke run,
required plots, reference comparison, manifest, and README status update have
fresh verification evidence. Its available numeric data must agree with the
external legacy artifacts and its matching plots must agree with the original
GSI website references; otherwise record the discrepancy here as a blocker.
Do not treat a successful runtime as benchmark completion. Record blockers and
physics discrepancies here before changing the next step.

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
respectively. The 8-particle/32-turn smoke profile completed on 2026-09-12:
both planes used a 504-node, 216.7199934718 m PTC lattice with 504 frozen-SC
nodes and no losses. Its short-window numeric residuals are diagnostic only;
the 100-particle/1,024-turn reference run numerically agrees with the external
tables (horizontal maximum residual `1.18e-4`; vertical `3.36e-5`). The
current/GSI comparison plot previously used launch rather than effective
amplitude on its x axis; that display defect is fixed, but the reference plot
must be regenerated and visually reviewed before Step 3 can be completed.

Step 4 uses the sextupole-on lattice matched to `(Qx, Qy) = (4.3504, 3.2)` and
the same frozen analytical-Gaussian SC, `z=dE=0`, 10 m aperture, and restoring
force as Step 3. Both scans launch through 4 sigma. Its 8-particle/32-turn
smoke profile completed on 2026-09-12 with a 504-node, 216.7199934718 m PTC
lattice, 504 frozen-SC nodes per plane, and no losses. Its short-window
numeric residuals are diagnostic only; the historical 1,024-turn reference
run and review remain pending.

Step 5 preserves the historical horizontal `i/N × 4 sigma_x` 16-particle
Poincare launch at `(Qx, Qy) = (4.3504, 3.2)`, with frozen analytical-Gaussian
space charge, a 10 m aperture, and the historical restoring force. The
8-particle/32-turn smoke profile completed on 2026-09-12 with a 504-node,
216.7199934718 m PTC lattice, 504 frozen-SC nodes, and no losses. It records
particle-ID-indexed Poincare trajectories and fixed `[-50, 50] mm × [-5, 5]
mrad` views, plus external legacy PTC-PyORBIT2 and original GSI MICROMAP,
SIMPSONS, and Synergia visual references. The legacy Step 5 artifacts contain
only plots, not a usable numeric particle table: reference completion therefore
requires a visual review that confirms the physical extent, central orbit, and
three resonance islands.

Step 6 tracks one particle for one 15,000-turn synchrotron oscillation with
the sextupole-on `(Qx, Qy) = (4.3504, 3.2)` lattice, frozen analytical-Gaussian
SC, 10 m aperture, and restoring force `-1.951e-11`. Its published GSI launch
is `x=5 mm`, `xp=y=yp=dE=0`, `z=2.5 sigma_z`; the 64-turn smoke completed on
2026-09-15 with a 504-node, 216.7199934718 m PTC lattice, 504 frozen-SC nodes,
and no loss. The external `Particles_all.dat` instead starts at `x=0` due to
the historical generator's one-particle range bug, and its plot filenames also
retain stale fast-regime text. The `legacy_artifact` profile reproduces that
zero-launch trajectory for six-decimal numeric comparison; the `reference`
profile remains authoritative for the GSI action plot. Step completion requires
both successful artifact numeric comparison and published-plot agreement, with
the provenance conflict retained in the manifest and comparison report.

Step 7 is the fast-synchrotron case: the sextupole-on `(Qx, Qy) = (4.3504,
3.2)` lattice, frozen analytical-Gaussian SC, 10 m aperture, and restoring
force `-4.38975e-09` track a single particle from `x=5.1 mm`,
`xp=y=yp=dE=0`, `z=2.5 sigma_z`. The 64-turn smoke completed on 2026-09-16
with a 504-node, 216.7199934718 m PTC lattice, 504 frozen-SC nodes, and no
loss. The scientific profile retains the historical 2,000-turn duration; its
published action view is deliberately restricted to turns 0--1,000 with the
GSI `0.9--1.6` normalized-action limits. The external Step 7 artifacts have
only visual PNGs, not a particle table, so reference completion requires visual
agreement with the GSI SIMPSONS/MICROMAP and legacy PTC-PyORBIT2 plots, showing
the expected fast-regime scattering rather than adiabatic trapping.

Step 8 is the website-authoritative 100,000-turn long-term scattering/trapping
case at `Qs=1e-3`, with the Step 7 published launch `x=5 mm`,
`xp=y=yp=dE=0`, `z=2.5 sigma_z`, and `(Qx, Qy) = (4.3504, 3.2)`. Its
128-turn smoke completed on 2026-09-20 with a 504-node,
216.7199934718 m PTC lattice, 504 frozen analytical-Gaussian SC nodes, and no
particle loss. The archived `Particle_0.dat` trajectory has 200,000 tracked
turns plus its pre-tracking record; the `reference` profile compares the
matching 100,000-turn prefix, while `legacy_artifact` performs the full run.
The smoke-prefix residual is diagnostic only (maximum absolute residuals:
`x=1.6e-5 m`, `xp=2e-6 rad`, `z=3e-6 m`); reference disagreement must remain
a blocker. The full official GSI Step 8 slide is versioned with source and
digest provenance, without digitizing it as numeric data; its heading states
100,000 turns but its plotted x-axis reaches 200,000, so that source conflict
is retained in the comparison report.

Step 9 uses a local `config.json` and a seeded matched six-dimensional
Gaussian bunch because the historical tomoscope file cannot be recovered. Its
64-turn / 32-particle smoke completed on 2026-09-21 with a 504-node,
216.7199934718 m PTC lattice, 504 frozen analytical-Gaussian SC nodes, and no
losses. It records sampled `BunchTwissAnalysis` diagnostics, external
read-only `output.mat` comparison hashes, labelled side-by-side and numeric
overlay plots, and full official GSI Step 9 slides. The scientific reference
is 1,000 particles at `(Qx, Qy) = (4.3504, 3.2)` for 100,000 turns; its
published final horizontal-emittance estimate is 2.08 and is deliberately
report-only pending manual review. The archival MAT curve is a distinct
10,000-particle `(Qx, Qy) = (4.3604, 3.2)` tomoscope ensemble (final archived
ratio 1.96456), so it must remain a diagnostic rather than a turn-by-turn
equivalence criterion.
