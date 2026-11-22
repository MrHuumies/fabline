# Task card — twin-line crew assignment

- **Task ID:** `factory.power.crew-layouts.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

Two repair crews are assigned in parallel to a loop and two bridges on a
32×16 map with two gear lines. The lines occupy independent rows and random
horizontal offsets, share one generator, and crew B starts on a random empty
cell at least eight cells from crew A. The layout makes the nearest pair
non-optimal on some seeds and exposes a real assignment gap.

## Contract

- **Observation:** tick, score, crew positions, and per-role outage, state,
  deadline, and distance to each crew. Same as the two-crew task.
- **Actions:** 16 pairs (noop/loop/small/large for each crew); same-wire
  positive assignments masked.
- **Crews:** A at the first depot; B on a seeded random empty cell at least
  eight Manhattan cells from A.
- **Layout:** two gear lines, independent rows, random x offsets, one generator,
  capacity 24.
- **Warnings:** tick 40; failures at 90 (loop), 110 (small), 130 (large).
- **Travel:** 2 × Manhattan; service 40 ticks.
- **Assignment:** one-shot; each crew one job.
- **Reward:** final production score; success ≥ 400.

## Metrics

- mean score and success rate;
- prevented and restored outage;
- aborted jobs;
- travel ticks;
- oracle pair and nearest/greedy pair.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| parallel_nearest | nearest target per crew |
| parallel_greedy | outage per service time |
| random | uniform legal pair |
| oracle | best pair by simulation |
| tabular Q | role/position state; 500 training layouts per evaluation seed |

## Gates

| Gate | Threshold |
|---|---|
| H1 layout gap | oracle mean ≥ best scripted two-crew mean + 10 |
| H2 coordination gain | best scripted two-crew mean ≥ single_edf + 10 |
| H3 nearest sensitivity | report nearest/greedy success and oracle-pair variety |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 |
| H5 budget | 500 training episodes per evaluation seed |

## Results (0046)

Seeds 6000–6009; one episode each.

| policy | mean score | success | prevented | travel |
|---|---:|---:|---:|---:|
| noop | 113.0 | 0.00 | 0.00 | 0.0 |
| single_edf | 139.0 | 0.00 | 0.80 | 16.8 |
| parallel_nearest | 361.0 | 0.50 | 1.40 | 54.0 |
| **parallel_greedy** | **419.0** | **0.60** | 1.50 | 50.4 |
| tabular Q | 217.0 | 0.00 | 0.60 | 42.6 |
| oracle | **441.0** | **0.70** | 1.60 | 32.6 |

H1, H2, H3, and H5 pass; H4 fails (Q 49.2% of oracle, 0.00 success). The
oracle pair varies across seeds; nearest succeeds on 5/10 and greedy on 6/10 at
the 400 threshold. See
[`experiments/0046-crew-layouts`](../experiments/0046-crew-layouts/summary.md).

## Learned baseline (0048)

Seeds 8000–8009; three compact-Q policies × 2000 layouts and three old policies
× 500.

| policy | mean score | success |
|---|---:|---:|
| old tabular Q | 233.3 | 0.07 |
| **compact Q** | **422.0** | **0.50** |
| oracle | 442.0 | 0.60 |

Compact Q is 95.5% of oracle and +188.7 over old Q, but misses the 0.60 success
gate. One Q seed matches oracle exactly; the other two score 424/0.50 and
400/0.40. The representation is a large win but not a reliable H4 closure. A margin-aware
state was a negative pilot (0049): slack bins fragment the table and drop to
340–384. A compact-Q ensemble (0050) removes Q-seed variance: single mean
415.7/0.47, ensemble 430.0/0.50, oracle 448.0/0.60. It still misses the 0.60
success gate; seed 9002 is 340 for every compact policy and the oracle 520. See
[`experiments/0048-crew-layout-q`](../experiments/0048-crew-layout-q/summary.md)
and
[`experiments/0050-crew-layout-ensemble`](../experiments/0050-crew-layout-ensemble/summary.md).

## Known pitfalls

- **Two lines, one generator.** This is a shared-resource layout, not independent
  factories.
- **East-facing lines.** Orientation is fixed; rotation is future work.
- **Random B base.** Some layouts put B far from every bridge; the oracle can
  still choose the loop/noop and accept the loss.
- **Score scale doubles.** Success 400 is not comparable to the 16×8 task.
- **Q may fail.** Report it; do not tune on evaluation seeds.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-22 — card created; twin-line layout and gates preregistered.
- 2026-11-22 — formal run: oracle 441, greedy 419, nearest 361, Q 217
  fails H4.
- 2026-11-22 — compact layout-aware Q: 422 vs old Q 233, oracle 442; mean
  gate passes, success 0.50 misses 0.60.
- 2026-11-23 — compact-Q ensemble: 430 vs oracle 448; success 0.50 misses
  0.60; one aliased seed remains.
