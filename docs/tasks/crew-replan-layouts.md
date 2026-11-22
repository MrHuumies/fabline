# Task card — crew recall/replanning on twin-line layouts

- **Task ID:** `factory.power.crew-replan-layouts.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; not promoted (H3/H4 fail); not
  in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

Two crews are assigned on a 32×16 map with two gear lines and a random crew-B
base. Crew B is recalled at tick 100; if it is still working, its bridge is
orphaned. After crew A finishes its first job, it can recover the abandoned
bridge. The task combines a nonlocal assignment with crew loss and recovery.

## Contract

- **Observation:** tick, score, crew positions, per-wire outage/state/deadline,
  distances to each crew, phase, B availability, recall countdown, and orphan
  role.
- **Actions:** 16 initial pairs; second decision is noop or the abandoned
  positive bridge. A loop orphan grants no useful dispatch.
- **Layout:** 32×16, two gear lines, random x offsets, one generator capacity 24.
- **Crews:** A at the first depot; B on a seeded random empty cell at least
  eight Manhattan cells from A.
- **Warnings:** 40; failures 90 (loop), 110 (small), 130 (large).
- **Recall:** 100; B's unfinished job aborts.
- **Travel:** 2 × Manhattan; service 40 ticks.
- **Reward:** final production score; success ≥ 400.

## Metrics

- mean score and success rate;
- B jobs aborted at recall;
- prevented repairs and total aborts;
- travel ticks;
- second-dispatch choices.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| parallel_nearest | nearest positive pair; nearest unresolved at replan |
| parallel_greedy | outage per service time |
| recall_aware | A earliest bridge, B the other; recover the orphan |
| recall_aware_no_replan | same first assignment, no second dispatch |
| random | uniform legal action |
| oracle | best initial pair and replan by simulation |
| tabular Q | role/recall/orphan state, 500 training layouts |

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 |
| H2 replan gain | recall_aware ≥ recall_aware_no_replan + 10 |
| H3 layout gap | oracle ≥ best two-crew scripted + 10 |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 |
| H5 budget | 500 episodes per Q policy; 3 policies |

## Results (0047)

Seeds 7000–7009; one episode each; three Q policies × 500 layouts.

| policy | mean score | success | B aborted |
|---|---:|---:|---:|
| noop | 110.0 | 0.00 | 0.0 |
| single_edf | 120.0 | 0.00 | 0.0 |
| parallel_nearest | 486.0 | 1.00 | 0.6 |
| **parallel_greedy** | **496.0** | **1.00** | 0.4 |
| recall_aware | 480.0 | 1.00 | 0.7 |
| recall_aware_no_replan | 240.0 | 0.30 | 0.7 |
| tabular Q | 210.0 | 0.23 | 0.2 |
| oracle | 505.0 | 1.00 | 0.3 |

H1 and H2 pass (+376 and +240); H3 fails by one point (oracle 505 vs greedy
496, +9 [0, 21]); H4 fails (Q 41.6% of oracle, 0.23 success). The recovery
dispatch is robust, but the twin-line assignment gap does not survive it. Not
promoted. See
[`experiments/0047-crew-replan-layouts`](../experiments/0047-crew-replan-layouts/summary.md).

## Known pitfalls

- Known recall, one orphan, one second dispatch.
- Random B can be far from both lines; some layouts cap below 400.
- Twin lines share one generator; orientation is fixed.
- Q may fail on the larger state; report it.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-22 — card created; combined layout/recall contract and gates
  preregistered.
- 2026-11-22 — formal run: replan +240, greedy +376, but oracle-greedy +9
  misses H3; Q fails H4; not promoted.
