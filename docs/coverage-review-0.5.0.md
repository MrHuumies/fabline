# Coverage review — FABLINE 0.5.0

- **Status:** complete; benchmark freeze review. Package release tag pending.
- **Date:** 2026-11-27
- **Scope:** `factory-v0.4`, the eight-task coverage suite, and the public
  structured-baseline slice
- **Related:** [coverage map](coverage-map.md), frozen
  [`factory-v0.4` card](../benchmarks/factory-v0.4/card.md),
  [`factory-v0.4` freeze review](../benchmarks/factory-v0.4/freeze-review.md),
  and the [0.5.0–0.8.0 roadmap](roadmap-0.5.0-0.8.0.md)

## Verdict

0.5.0 is a **publication release, not a new mechanic**. It freezes
`factory-v0.4` with eight coverage tasks, public structured baselines, a compact
expected summary, and a CI check. Seven tasks pass; wired-cascade is a public
reproduction diagnostic.

`factory-v0.4` is frozen. The package release is not tagged yet; see
[Release state](#release-state).

## Suite result

Full suite, `--skip-sequence`, 2026-11-27:

| Task | Status | Key result |
|---|---|---|
| reliability-contract | pass | CVaR +17.62 [13.90, 21.68] |
| partial-throughput | pass | window GBDT R² 0.897 |
| wired-cascade | diagnostic | graph_mp R² 0.124, +0.018 vs vector |
| crew-schedule | pass | deadline Q 256.4/1.00 vs EDF 260.0 |
| crew-triage | pass | oracle 456.0 vs greedy 378.0 |
| preventive-wire | pass | preventive 260.0 vs reactive 195.3 |
| recipe-choice | pass | buffer-aware 318.0 vs fast 278.0 |
| maintenance-threshold | pass | best fixed 0.7; learner 250.0 |

The expected-summary check reports **zero mismatches** on a fresh full run.

## What 0.5.0 established

### Coverage

- Risk-sensitive selection is public and reproducible: the reliability contract
  separates mean and CVaR objectives.
- Partial throughput recovers the masked-window result: the 4-frame window GBDT
  reaches R² 0.897.
- Crew scheduling and three-bridge triage publish the P1/P2 spatial and
  multi-agent results.
- Preventive wire, recipe choice, and maintenance-threshold selection fill the
  temporal, production, and bandit/context gaps.
- Wired-cascade is public but remains a diagnostic: the private 0032 feature
  encoding is not reproduced, and the public graph gain is +0.018, below the
  +0.05 gate. The gate was not lowered.

### Baselines and method

- Public CNN, MPNN, GRU, and Transformer model code lives in
  `src/fabline/harness/models/` with unit tests.
- The expected summary is compact and deterministic; the full check is wired
  into `.github/workflows/benchmark-v04.yml`.
- `factory-v0.1` through `factory-v0.3` remain frozen and unchanged.

## Negative and saturated results

- **Wired cascade:** diagnostic. Graph message passing does not reproduce the
  private encoding gain; do not treat it as a headline score.
- **Coverage task-local intervals:** bootstrap intervals are task-local
  (row/episode/block), not uniformly episode-cluster. The freeze review records
  this as a limitation.
- **Challenge tasks:** the five challenge cards are not integrated into the
  expected summary. They remain a follow-up list, not a frozen tier.

## Remaining gaps

1. **Layout split and private holdout.** `factory-v0.4` has neither. It is a
   research sandbox, not a public leaderboard.
2. **Challenge-tier summaries.** Cards exist for twin-line assignment,
   decentralized triage, replacement handoff, recall+twin-line, and maintenance
   calibration; expected summaries do not.
3. **OR/CP-SAT baseline.** No public OR baseline is integrated.
4. **Episode-cluster bootstrap.** Only some tasks use episode-aware resampling.
5. **Wired-cascade encoding.** The public graph gain remains below the gate.

These are next-version work, not hidden requirements for the 0.5.0 freeze.

## Recommended next slice

The next mechanic is the **assembly edge**: per-assembler recipes, a shared
component, and `INGOT + COMPONENT -> 2 GEAR`. It changes the production
constraint structure rather than adding another order-table knob.

That slice is already implemented in the 0.6.0 work on `main` and frozen as
`factory-v0.5`; it is referenced here for release ordering, not re-opened.

## Release state

- [x] `factory-v0.4` is frozen and merged to `main`.
- [x] Expected summary is checked in.
- [x] Full expected-summary check reports zero mismatches.
- [x] `factory-v0.1`–`factory-v0.3` assets are unchanged.
- [x] Card, spec, freeze review, and this review are checked in.
- [x] CI workflow for the full check exists.
- [ ] Package version is not yet `0.5.0` (`pyproject.toml` and
      `src/fabline/__init__.py` still say `0.4.0`).
- [ ] No `v0.5.0` git tag or GitHub release exists yet.
- [ ] The changelog still lists the coverage freeze under `[Unreleased]`.

The benchmark is publishable. The package release is a release-engineering
step: bump the version, add the `[0.5.0]` changelog section, tag the freeze
commit (or the chosen release commit), and publish the GitHub release.

## Map maintenance

Update the [coverage map](coverage-map.md) and the roadmap when a task or
benchmark status changes. Do not edit frozen `factory-v0.4` assets; open a new
benchmark version instead.
