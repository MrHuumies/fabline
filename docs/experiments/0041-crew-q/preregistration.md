# Experiment 0041 — Deadline-aware Q for crew scheduling

- **Status:** complete (all gates pass; see [`summary.md`](summary.md))
- **Date:** 2026-11-22
- **Type:** P1 learned-baseline experiment; follow-up to
  [`0040`](../0040-crew-schedule/summary.md)
- **Task:** `factory.power.crew-schedule.v1` (debug/P1, not in `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a deadline/role state with episodic Q close the learned gap in crew
scheduling?

In 0040, earliest-deadline-first scored 260 and the oracle 260, but tabular Q
scored 156.4 with 0.52 success. The Q state lacked distances and deadlines, and
discounted multi-tick service returns. This experiment keeps the mechanic and
changes only the learned baseline:

- state: budget, tick bucket, role states, small/large distance buckets, and
  small/large deadline buckets;
- episodic update: `gamma = 1.0`;
- 500 training layouts.

## Data and seeds

- Evaluation: seeds 900–904, 5 episodes each.
- Training: 500 layouts from 20000 + 1500 × Q seed.
- Pilot: seeds 800–804 were used by 0040; formal seeds are fresh.
- No dataset artifact.

## Conditions

| Condition | State / update |
|---|---|
| tabular_q (0040) | budget, tick, role states, distance; gamma 0.95 |
| deadline_q | adds deadline buckets; gamma 1.0 |
| earliest_deadline | scripted |
| oracle | best two-wire order |

## Gates

| Gate | Threshold |
|---|---|
| H1 deadline Q quality | deadline_q ≥ 0.85 × EDF; success ≥ 0.80 |
| H2 learned gain | deadline_q ≥ tabular_q + 30 |
| H3 learned success | deadline_q success ≥ 0.80 |
| H4 per-seed | report per-seed scores and chosen sequences |
| H5 budget | 500 training episodes |

## Predictions

- tabular_q remains near 156 and 0.52 success.
- deadline_q scores 240–255 and succeeds on every seed.
- EDF and the oracle remain 260.
- If deadline_q fails, stop the P1 learned-repair line and move to P2.

## Kill criteria

- deadline_q is below 0.85 × EDF or succeeds below 0.8.
- deadline_q does not beat tabular_q by 30.
- The result is dominated by one seed.
- The task requires post-hoc changes to the state, discount, or gates.

## Analysis plan

- Report all conditions with score, CI, prevented, travel, and success.
- Report deadline_q per-seed scores.
- Keep the crew mechanic, failures, and budgets fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Env: `src/fabline/env/crew_schedule.py`
- Harness: `src/fabline/harness/crew_schedule.py`
- CLI: `python -m fabline crew-schedule`
- Task card: `docs/tasks/crew-scheduling.md`
- Raw results: `results/crew_schedule_q/` (ignored)
- Summary: `docs/experiments/0041-crew-q/summary.md`
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
