# Experiment 0046 — Twin-line crew layouts

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-22
- **Type:** P2 larger/random-layout experiment
- **Mechanic:** two crew assignment on twin-line randomized layouts (RFC 0013,
  ADR 0023)
- **Task:** `factory.power.crew-layouts.v1` (debug/P2, not in `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a larger, twin-line layout make the two-crew assignment non-trivial, and
does the oracle beat the best scripted policy by at least 10 points?

The 16×8 task saturates: nearest is 255.5 over 40 seeds and the oracle pair is
almost always small A / large B. Larger empty maps also saturated. Twin lines
create nonlocal distances and a real crew-target matching problem.

## Environment

- 32×16 map, two gear lines at independent rows and random x offsets.
- One generator, capacity 24, wired topology; both lines share it.
- Crew A at the first depot; crew B on a random empty cell at least eight
  Manhattan cells from A.
- Targets: zero-outage loop, smallest positive bridge, largest positive bridge.
- Warning 40; failures at 90 (loop), 110 (small), 130 (large).
- One-shot pair assignment; same-wire positive pairs masked.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 0–19 (all valid).
- Formal: seeds 6000–6009 (10 contiguous, all valid by reset-only check).
- Q training: 500 layouts per evaluation seed, starting at
  `55000 + 1000 × evaluation_seed` (the existing `multi-crew` protocol).
- Train and evaluation layouts are disjoint.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only, earliest positive deadline |
| parallel_nearest | each crew takes its nearest target |
| parallel_greedy | maximize summed outage per service time, no duplicates |
| random | uniform legal pair |
| oracle | best pair by simulation |
| tabular Q | role/position state; 500 training layouts per evaluation seed |

## Gates

| Gate | Threshold |
|---|---|
| H1 layout gap | oracle mean ≥ best two-crew scripted + 10 |
| H2 coordination gain | best two-crew scripted ≥ single_edf + 10 |
| H3 nearest sensitivity | diagnostic: nearest/greedy success at 400 and oracle-pair variety; the layout is non-trivial if nearest success < oracle success |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 |
| H5 budget | 500 training episodes per evaluation seed |

## Predictions

- Single-crew EDF scores about 130.
- Nearest averages 350–400 and fails the 400 success threshold on several seeds.
- Greedy averages 420–450; the oracle averages 440–480.
- The oracle-best scripted gap is 10–25 points.
- Oracle pairs vary across seeds; small A / large B is no longer universal.
- Q scores below 0.85 × oracle; the larger state is harder than the 16×8 task.

## Kill criteria

- Oracle does not beat the best scripted two-crew policy by 10.
- The best scripted two-crew policy does not beat single-crew by 10.
- The task requires post-hoc changes to the map, seeds, thresholds, or gates.

## Analysis plan

- Report all conditions with score, CI, min, max, success, prevented, aborted,
  and travel.
- Report oracle pairs and per-seed scores.
- Report Q per-seed scores and the gap to oracle.
- Keep the layout, bases, deadlines, and gates fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0013, ADR 0023
- Env: `src/fabline/env/multi_crew.py`
- Harness: `src/fabline/harness/multi_crew.py`
- CLI: `python -m fabline crew-layouts`
- Task card: `docs/tasks/crew-layouts.md`
- Raw results: `results/crew-layouts/` (ignored)
- Summary: `docs/experiments/0046-crew-layouts/summary.md`
- Prior: [`../0044-crew-robustness/summary.md`](../0044-crew-robustness/summary.md)
