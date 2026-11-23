# Task card — three-crew initial assignment

- **Task ID:** `factory.power.crew-three.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Three crews and three positive bridges on a 32×16 twin-line map. Each crew
chooses one bridge or noop in a single 64-action assignment; duplicate positive
targets are illegal. The task tests full three-agent coverage against a
two-crew baseline that forces the third crew to noop.

## Contract

- **Observation:** three-role crew observation plus crew C position and its
  distance to each role.
- **Actions:** 64 actions (noop/loop/small/large for A, B, C); duplicate positive
  targets masked.
- **Crews:** A at the depot; B and C on seeded random empty cells at least eight
  cells from A and each other.
- **Warnings/failures:** 40; 100/130/160.
- **Travel:** 2 × Manhattan; service 40 ticks; jobs run concurrently.
- **Reward:** final production score; success ≥ 400.

## Metrics

- mean score and success;
- three-crew vs two-crew gain;
- oracle gap;
- assignment quality.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| two nearest | A/B nearest; C noop |
| two greedy | A/B greedy; C noop |
| two oracle | best A/B pair; C noop |
| three nearest | nearest distinct target per crew |
| three greedy | outage per service time over all 64 actions |
| three aware | earliest deadline per crew |
| three oracle | best 64-action assignment |

## Gates

| Gate | Threshold |
|---|---|
| H1 third-crew gain | three best ≥ two best + 10 |
| H2 coordination | three best ≥ single/noop + 10 |
| H3 oracle gap | three oracle ≥ three best + 10 |
| H4 oracle success | three oracle success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Known pitfalls

- One-shot only; no recall or replanning.
- C's base and the widened deadlines are scope choices.
- Three scripted policies may saturate; the oracle gap is the non-saturated
  signal.
- Not part of `factory-v0.1`.

## Results (0062)

Seeds 22000–22004.

| policy | mean score | success |
|---|---:|---:|
| noop | 104.0 | 0.00 |
| single_edf | 110.0 | 0.00 |
| two nearest | 282.0 | 0.00 |
| two greedy / oracle | 320.0 | 0.00 |
| three nearest | 400.0 | 0.40 |
| **three greedy** | **476.0** | **0.80** |
| three aware | 390.0 | 0.40 |
| **three oracle** | **520.0** | **1.00** |

H1 +156, H2 +366, H3 +44, H4 1.00; all gates pass. See
[`experiments/0062-crew-three`](../experiments/0062-crew-three/summary.md).

## Changelog

- 2026-11-23 — card created; three-crew contract and gates defined.
- 2026-11-23 — formal run: three 476, oracle 520, two 320; all gates pass.
