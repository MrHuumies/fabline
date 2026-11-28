# Benchmark card — factory-v0.6

- **Status:** frozen; **challenge tier**
- **Version:** 0.6.0
- **Package release:** 0.7.0
- **Date:** 2026-11-28
- **World:** `factory-0.1.0` + wired power (task-layer crews)
- **Plan:** `sequential-v0.6`
- **Spec:** [`benchmark.toml`](benchmark.toml)
- **Freeze review:** [`freeze-review.md`](freeze-review.md)
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Runner:** `python -m fabline sequential-crew --out results/factory-v0.6`
- **Check:** `python -m fabline sequential-crew --out results/factory-v0.6 --check-expected benchmarks/factory-v0.6/expected/summary.json`
- **Predecessor:** `factory-v0.5` remains immutable

## What is frozen

One task on the opt-in wired-power layout:

| Task | Kind | Observation | Action | Status |
|---|---|---|---|---|
| crew-sequential | control | shared 20-feature task state | 6 actions per crew | **challenge** |

Contract:

- two crews, five failed target wires, 500 ticks, 10-tick decisions, 6 repair
  ticks;
- actions: north, east, south, west, wait, repair (6² = 36 joint actions);
- crew positions, repair progress, and targets are task-layer state;
- success is mission completion (all five targets repaired within 500 ticks);
  score is a continuous secondary metric;
- the default world hash and frozen v0.1–v0.5 assets are unchanged.

## Formal result (0095)

Seeds 110,150–110,154; five episodes per seed:

| Policy | Score | 95% CI | Success | Repairs |
|---|---:|---:|---:|---:|
| single_crew | 12.0 | [3.2, 29.6] | 0.28 | 3.48 |
| greedy | 32.4 | [20.6, 46.8] | 1.00 | 5.00 |
| assigned | **33.6** | [20.6, 49.4] | **1.00** | 5.00 |
| queue_oracle | 38.8 | [24.0, 55.2] | 1.00 | 5.00 |
| random | 0.0 | [0.0, 0.0] | 0.00 | 0.00 |
| independent_q | 0.0 | [0.0, 0.0] | 0.00 | 0.84 |
| bc | 9.2 | [1.6, 24.2] | 0.20 | 2.48 |

Gates:

| Gate | Result |
|---|---|
| H1 coordination (+10) | **pass**, +21.6 |
| H2 scripted success (≥0.60) | **pass**, 1.00 |
| H3 learned gap (+10) | **fail**, +9.2 (BC) |
| H4 learned success (≥0.60) | **fail**, 0.20 (BC) |
| H5 cost reported | **pass** |

Oracle gap (queue oracle − best scripted): **+5.2**, diagnostic only.

## Why challenge

The task is valid: two crews clearly beat one crew (+21.6 score, +0.72 success),
and the scripted policies complete all five targets. The learned baselines do
not solve it at the registered budget: Q stays at 0 and BC reaches 9.2/0.20.
H3 misses by 0.8 and H4 is far below the gate. The task is therefore frozen as a
**challenge task**; H4 is not lowered, and the learned baselines are not tuned
after the formal block.

## Baselines

- Scripted: single crew, greedy, assigned, queue oracle.
- Learned: independent tabular Q, behavior cloning.
- Random.
- Cost: Q table entries and BC model count; no message cost (Phase 1).

## Caveats

- Phase 1 is shared-observation, six-action control. Local views, `report`, and
  communication are Phase 2.
- Stochastic faults and POMDP maintenance are deferred to 0.8.0.
- Fixed 32×32 gear/wired-power layout; no layout split.
- The 0093 (3 targets) and 0094 (4 targets) formal blocks were negative on H1;
  only the 5-target condition is frozen.
- The queue oracle is a queue-plan upper bound, not a full joint-action oracle.
- A larger Q/BC budget is a new pre-registration, not a tune.

## Changelog

- 2026-11-28 — card created for the `factory-v0.6` challenge freeze.
