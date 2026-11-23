# Task card — asymmetric repair-cost triage

- **Task ID:** `factory.power.crew-triage-costs.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run negative (greedy matches oracle); not
  in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Three bridges fail on a staggered schedule. Loop, small, and large repairs take
20, 40, and 100 ticks; travel is 2 × Manhattan. A two-crew initial assignment is
followed by a job failure and B recall at tick 100, then A gets two survivor
jobs. The task tests whether repair-cost asymmetry makes the triage order matter
beyond the outage-per-service greedy rule.

## Contract

- **Observation:** 31 features. The 25 crew-replan features plus six normalized
  service times (`loop/small/large × crew A/B`) when `role_repair_ticks` is set.
- **Actions:** initial 16 A/B pairs; replan 16 A pairs (one crew, two sequential
  jobs).
- **Crews:** A at depot; B on a seeded random base at least eight cells away.
- **Warnings/failures:** 40; 90/110/130; failure and recall 100.
- **Repair:** loop 20, small 40, large 100; travel 2 × Manhattan.
- **Reward:** final production score; success ≥ 300.

## Metrics

- mean score and success;
- oracle gap vs best scripted;
- coordination gain vs single/noop;
- per-seed oracle sequences;
- `prevented`, `aborted`, `b_aborted`, and travel.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only, earliest deadline |
| nearest | nearest distinct initial pair; nearest survivor |
| greedy | outage per service time, initial and survivor |
| aware | earliest deadline initial; outage survivor |
| no-replan | initial only |
| oracle | exhaustive 16×4×4 sequence |

## Gates

| Gate | Threshold |
|---|---|
| H1 oracle gap | oracle ≥ best scripted + 10 |
| H2 coordination | best scripted ≥ single/noop + 10 |
| H3 cost sensitivity | best scripted below oracle; report both greedy and aware |
| H4 oracle success | ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Known pitfalls

- One survivor, two jobs, three bridges; one bridge can remain unresolved.
- Repair costs are a fixed role tuple, not a continuous distribution.
- The pilot reused 0055 seeds; the formal run uses fresh seeds 25000–25004.
- Not part of `factory-v0.1`.

## Results (0066)

Seeds 25000–25004.

| policy | mean score | success |
|---|---:|---:|
| noop | 84.0 | 0.00 |
| single_edf | 100.0 | 0.00 |
| nearest | 352.0 | 1.00 |
| **greedy** | **386.0** | **1.00** |
| aware | 346.0 | 0.80 |
| no-replan | 102.0 | 0.00 |
| **oracle** | **386.0** | **1.00** |

H1 fails: oracle gap 0. Greedy matches oracle on every seed. See
[`experiments/0066-crew-costs`](../experiments/0066-crew-costs/summary.md).

## Changelog

- 2026-11-23 — task card created; cost asymmetry and gates defined.
- 2026-11-23 — formal run negative; greedy equals oracle; cost axis retired.
