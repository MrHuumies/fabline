# Task card — random-topology triage

- **Task ID:** `factory.power.crew-topology.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run negative (random gap +4 vs spread
  +18); not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and a random three-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Three production lines are placed at random y rows and full-width random x
starts on a 48×24 map. Three bridges fail on a staggered schedule; two crews
make an initial pair assignment, one crew is recalled at tick 100, and the
survivor gets two jobs. The task tests whether random topology creates a harder
triage order than the controlled twin-line and spread layouts.

## Contract

- **Observation:** the 25 crew-replan features; no shape change.
- **Actions:** initial 16 A/B pairs; replan 16 A-only actions.
- **Layout:** 48×24, three lines, one extra belt per line, random y and x.
- **Crews:** A at depot; B on a seeded random base at least eight cells away.
- **Warnings/failures:** 40; 90/110/130; failure and recall 100.
- **Repair:** 40 ticks; travel 2 × Manhattan.
- **Reward:** final production score; success ≥ 300.

## Metrics

- mean score and success;
- per-seed oracle gap over the best scripted policy;
- paired gap difference versus the spread control;
- oracle sequences;
- `prevented`, `aborted`, `b_aborted`, and travel.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| nearest | nearest distinct initial pair; nearest survivor |
| greedy | outage per service time |
| aware | earliest deadline initial; outage survivor |
| no-replan | initial only |
| oracle | exhaustive 16×4×4 sequence |

## Gates

| Gate | Threshold |
|---|---|
| H1 random gap | per-seed oracle ≥ best scripted + 10 on average |
| H2 coordination | best scripted ≥ single/noop + 10 |
| H3 layout effect | random gap ≥ spread gap + 10 |
| H4 oracle success | ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Known pitfalls

- The random layout has lower absolute scores; use the gap, not raw score.
- The pilot used seeds 27,000–27,004 and had one negative paired seed.
- The formal run uses fresh seeds 28,000–28,004 and a spread control.
- Not part of `factory-v0.1`.

## Results (0067)

Seeds 28000–28004; per-seed oracle gap over the best scripted policy.

| Layout | Oracle | Best scripted | Mean gap |
|---|---:|---:|---:|
| **random** | 464.0 | 460.0 | **+4.0** |
| spread | 536.0 | 518.0 | **+18.0** |

H1 and H3 fail. Random topology is harder in absolute score but does not add a
new assignment decision. See
[`experiments/0067-crew-topology`](../experiments/0067-crew-topology/summary.md).

## Changelog

- 2026-11-23 — task card created; random layout and gates defined.
- 2026-11-24 — formal run negative; random gap +4 vs spread +18; topology axis
  retired.
