# Task card — three-crew recall and recovery

- **Task ID:** `factory.power.crew-three-replan.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; positive but shallow; not in
  `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Three crews and three positive bridges. The initial 64-action dispatch assigns
A/B/C. B is recalled at tick 100; its unfinished job aborts. The remaining A/C
pair makes a 16-action recovery assignment. The task tests whether a third crew
helps both initial coverage and post-loss recovery.

## Contract

- **Observation:** three-role crew observation plus phase, B availability, and
  recall countdown.
- **Actions:** initial 64 (noop/loop/small/large for A/B/C); recovery 16 (A/C),
  duplicate positive targets masked.
- **Crews:** A at depot; B and C on seeded random bases at least eight cells
  apart.
- **Warnings/failures:** 40; 100/130/160; recall 100.
- **Travel:** 2 × Manhattan; service 40 ticks.
- **Reward:** final production score; success ≥ 400.

## Metrics

- mean score and success;
- recovery gain vs no-replan;
- three-crew gain vs single/noop;
- oracle gap.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| three nearest | nearest distinct initial targets; nearest A/C recovery |
| three greedy | outage per service time; greedy A/C recovery |
| three aware | earliest deadline; aware A/C recovery |
| three no-replan | initial dispatch only |
| oracle | best 64 initial and 16 recovery actions |

## Gates

| Gate | Threshold |
|---|---|
| H1 recovery gain | three best ≥ no-replan + 10 |
| H2 coordination | three best ≥ single/noop + 10 |
| H3 oracle gap | report oracle vs three best; may be shallow |
| H4 oracle success | oracle success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Known pitfalls

- One recall and one recovery pair; no sequential survivor work.
- The initial job may complete before recall, making the loss harmless.
- Three greedy is near the oracle ceiling.
- Not part of `factory-v0.1`.

## Results (0063)

Seeds 24000–24004.

| policy | mean score | success |
|---|---:|---:|
| noop | 110.0 | 0.00 |
| single_edf | 122.0 | 0.00 |
| three nearest | 500.0 | 1.00 |
| **three greedy** | **516.0** | **1.00** |
| three aware | 490.0 | 1.00 |
| three no-replan | 360.0 | 0.40 |
| **oracle** | **520.0** | **1.00** |

H1 +156, H2 +394, H4 1.00; H3 is shallow (+4). See
[`experiments/0063-crew-three-replan`](../experiments/0063-crew-three-replan/summary.md).

## Changelog

- 2026-11-23 — card created; three-crew recall contract and gates defined.
- 2026-11-23 — formal run: recovery +156; oracle gap +4; positive but shallow.
