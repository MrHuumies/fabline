# `factory-v0.4` freeze review

- **Status:** frozen as `factory-v0.4`
- **Version:** 0.4.0
- **Package line:** 0.5.0 (tag pending)
- **Date:** 2026-11-27
- **Scope:** 0.5.0 coverage release
- **Related:** [card](card.md), [spec](spec.md), 0.5.0 roadmap,
  coverage analysis, experiments 0024/0031/0032/0035/0038/0040/0041/0055/0070
- **Predecessor:** `factory-v0.3` remains immutable

## Decision summary

`factory-v0.4` freezes an **eight-task coverage suite**:

1. reliability-contract
2. partial-throughput
3. wired-cascade (diagnostic)
4. crew-schedule
5. crew-triage
6. preventive-wire
7. recipe-choice
8. maintenance-threshold

Seven tasks pass their gates; wired-cascade is a public reproduction diagnostic.
No frozen v0.3 asset is changed.

## Evidence

Full suite, `--skip-sequence`, 2026-11-27:

| Task | Status | Key result |
|---|---|---|
| reliability-contract | pass | CVaR +17.62 [13.90, 21.68] |
| partial-throughput | pass | window GBDT R² 0.897 |
| wired-cascade | diagnostic | graph_mp R² 0.124 (+0.018 vs vector) |
| crew-schedule | pass | deadline Q 256.4/1.00 vs EDF 260 |
| crew-triage | pass | oracle 456 vs greedy 378 |
| preventive-wire | pass | preventive 260 vs reactive 195.3 |
| recipe-choice | pass | buffer-aware 318 vs fast 278 |
| maintenance-threshold | pass | best fixed 0.7; learner 250 |

Expected-summary check: **zero mismatches** on a fresh full run.

## What 0.5.0 established

- The positive backlog can be published without a new world mechanic.
- Public CNN/MPNN/GRU/Transformer baselines exist in `harness/models`; the
  structured-model paths are optional and unit-tested.
- Reliability contract reproduces the 0031 result publicly.
- Partial throughput reproduces the 0024 ordering publicly.
- Crew scheduling and three-bridge triage publish the P1/P2 spatial and
  multi-agent results.
- Preventive wire, recipe choice, and threshold selection fill temporal,
  production, and bandit coverage.
- Wired cascade is a public reproduction gap: the private 0032 feature encoding
  is not public, and the public graph gain is below the +0.05 gate.

## Limitations

- No layout split or private holdout yet.
- Bootstrap intervals are task-local, not uniformly episode-cluster.
- Challenge tasks have cards but no integrated expected summaries.
- No OR/CP-SAT baseline is integrated yet.
- Wired-cascade remains a diagnostic and is not a headline score.
- The suite is a research sandbox, not a public leaderboard.

## Freeze gates

- [x] Eight coverage tasks have cards, splits, and public harnesses.
- [x] Expected summary is checked in.
- [x] Full expected-summary check reports zero mismatches.
- [x] `factory-v0.3` assets and expected summaries are unchanged.
- [x] Public baseline code and tests are present.
- [x] Freeze review and known limitations are documented.
- [x] CI workflow for the full check exists.

## Next steps

1. Keep `factory-v0.4` immutable.
2. Treat layout split/private holdout/challenge summaries as a new benchmark
   version, not an edit.
3. Move to the 0.6.0 assembly family and 0.7.0 sequential-crew work.
