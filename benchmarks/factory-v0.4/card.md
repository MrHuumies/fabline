# Benchmark card — factory-v0.4

- **Status:** frozen
- **Version:** 0.4.0
- **Date:** 2026-11-27
- **World:** `factory-0.1.0`
- **Plan:** `coverage-v0.4`
- **Spec:** [`spec.md`](spec.md)
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Runner:** `python -m fabline coverage-suite --out results/factory-v0.4-coverage`
- **Check:** `python -m fabline coverage-suite --out results/factory-v0.4-coverage --skip-sequence --check-expected benchmarks/factory-v0.4/expected/summary.json`
- **Roadmap:** [`docs/roadmap-0.5.0-0.8.0.md`](../../docs/roadmap-0.5.0-0.8.0.md)
- **Analysis:** [`docs/coverage-analysis-2026-11-26.md`](../../docs/coverage-analysis-2026-11-26.md)

## What is frozen

`factory-v0.4` is a **coverage release**, not a new world. It keeps the frozen
v0.3 headline by reference and adds:

- an eight-task **coverage tier** for positive backlog tasks that were not in
  v0.3;
- public structured baselines (CNN, GNN/MPNN, GRU, Transformer);
- a compact expected summary and CI check;
- a challenge-task list for follow-up (not part of the frozen score);

The integrated slice contains eight tasks:

| Task | Kind | Observation | Status |
|---|---|---|---|
| reliability-contract | risk selection | stochastic power scores | pass |
| partial-throughput | regression | masked feature window | pass |
| wired-cascade | regression | wire graph + fault edge | diagnostic |
| crew-schedule | control | crew/wire state | pass |
| crew-triage | control | crew state | pass |
| preventive-wire | control | degraded wire | pass |
| recipe-choice | control | production view | pass |
| maintenance-threshold | bandit | diagnostics | pass |

The wired cascade is published as a diagnostic because the public
reimplementation does not reproduce the private 0032 graph gain (graph_mp
R² 0.124 vs vector 0.107, +0.018, below the +0.05 gate). Do not lower the gate.

## Coverage-suite result

Full suite, 2026-11-27, `--skip-sequence`:

| Task | Status | Key result |
|---|---|---|
| reliability-contract | pass | CVaR gain +17.62 [13.90, 21.68] |
| partial-throughput | pass | window GBDT R² 0.897 |
| wired-cascade | diagnostic | graph_mp R² 0.124 |
| crew-schedule | pass | deadline Q 256.4/1.00 vs EDF 260.0 |
| crew-triage | pass | oracle 456.0 vs greedy 378.0 |
| preventive-wire | pass | preventive 260.0 vs reactive 195.3 |
| recipe-choice | pass | buffer-aware 318.0 vs fast 278.0 |
| maintenance-threshold | pass | best fixed 0.7 vs learner 250.0 |

## Challenge tier (proposed)

These are valid tasks with negative or weak learned baselines. They are not
headline scores; they are open challenges.

- twin-line crew assignment (0046)
- decentralized triage (0077)
- replacement handoff (0060)
- recall + twin-line (0047)
- maintenance calibration (0084)

## Caveats

- The expected summary is checked in and the full check reports zero
  mismatches.
- There is no layout split or private holdout yet; that is next-version work.
- Bootstrap intervals are task-local, not uniformly episode-cluster.
- Challenge tasks have cards but no integrated expected summaries.
- Wired cascade is a reproduction gap, not a solved task.
- `factory-v0.3` remains frozen and unchanged.

## Changelog

- 2026-11-26 — draft card created with the three-task coverage slice.
- 2026-11-27 — expanded to eight tasks: crew schedule/triage, preventive wire,
  recipe choice, and maintenance threshold added.
