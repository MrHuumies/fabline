# Experiment 0035 — Preventive wire maintenance

- **Status:** complete (all gates pass; see [`summary.md`](summary.md))
- **Date:** 2026-11-22
- **Type:** P1 phase 1C predictive-maintenance experiment
- **Mechanic:** degraded-wire warning and early repair (RFC 0008, ADR 0018)
- **Task:** `factory.power.wire-maintenance.v1` (debug/P1, not in
  `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a warning/degraded state make a failure prediction actionable? Can a policy
start repair before the wire fails, and does that beat waiting for the failure?

Current wire repair only accepts failed wires. This experiment adds a warning
window: the target wire becomes degraded at tick 60, fails at tick 220, and a
repair takes 140 ticks. A preventive repair started at the warning completes
before failure. A late start aborts when the wire fails mid-job, spending the
budget with no restoration.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Target: the wire with the largest positive outage, chosen deterministically.
- Warning tick 60; failure tick 220; repair 140 ticks.
- Repair budget 1; one atomic repair action.
- Actions: noop or repair the watched wire.
- Reward:
  - preventive completion: `outage * 15 - 1`;
  - reactive completion: `outage * 10 * remaining/episode - 1`;
  - aborted: 0, budget spent.
- Outcome: final production score; success ≥ 150.
- Observation: 8 features — tick, score, outage, degraded, failed,
  time-to-failure, budget, repaired.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never repair |
| preventive | repair at the warning |
| reactive | repair after failure |
| late | repair 40 ticks after the warning; fails mid-job |
| random | uniform legal action |
| tabular Q | 200 training layouts from seed 6000 + 500 × Q seed |

Layouts without a single-wire bridge are skipped in Q training; they have no
preventive task.

## Data and seeds

- Evaluation: seeds 300–304, 5 episodes each = 25 episodes.
- Q training: 200 layouts from 6000 + 500 × Q seed.
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 prevention gain | preventive ≥ noop + 100 |
| H2 prediction value | preventive ≥ reactive + 30 |
| H3 timing value | preventive ≥ late + 100 |
| H4 Q quality | Q ≥ 0.85 × preventive; Q success ≥ 0.90 |
| H5 budget discipline | report prevented and aborted counts; Q prevented ≥ 0.90 |

## Predictions

- Noop and late score about 110; both fail.
- Preventive scores 260 and prevents the failure on every seed.
- Reactive scores about 195; it restores the wire but loses the repair window.
- Random sometimes starts early and scores between reactive and preventive.
- Q learns to repair at the warning and matches preventive.

## Kill criteria

- Preventive does not beat noop by 100.
- Preventive does not beat reactive by 30.
- Late and preventive are within 20 points (prediction timing not actionable).
- Q is below 0.75 × preventive or succeeds below 0.8.
- The result is dominated by one seed.
- The task requires post-hoc changes to the warning, failure, repair time, or
  gates.

## Analysis plan

- Report score, bootstrap CI, control reward, prevention count, abort count,
  and success for every policy.
- Report Q per-seed scores.
- Do not tune the warning/failure/repair timings after the formal run.
- Keep `factory-v0.1` frozen.

## Artifacts

- Env: `src/fabline/env/preventive_wire.py`
- Harness: `src/fabline/harness/preventive_wire.py`
- CLI: `python -m fabline wire-maintenance`
- Task card: `docs/tasks/power-wire-maintenance.md`
- Raw results: `results/wire_maintenance/` (ignored)
- Summary: `docs/experiments/0035-wire-maintenance/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
