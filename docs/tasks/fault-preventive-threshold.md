# Task card — maintenance-threshold selection

- **Task ID:** `factory.fault.preventive-threshold.v1`
- **Version:** 0.1.0
- **Status:** P1 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in faults
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

Per-step maintenance decisions are hard for tabular Q because the benefit of
resetting wear arrives long after the immediate production loss. The actual
policy knob is a wear threshold. Choose the threshold once per episode and a
scripted policy applies it.

## Contract

- **Observation:** none; one decision per episode.
- **Actions:** choose a maintenance threshold from
  `0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0` of the wear threshold.
- **Inner policy:** maintain the most worn machine when maximum wear reaches
  `threshold × 20`.
- **Reward:** final production score.
- **Success:** ≥ 240.
- **Episode:** 500 ticks.

## Metrics

- mean score;
- success rate;
- maintenance count;
- fault count;
- selected threshold.

## Baselines

| Baseline | Rule |
|---|---|
| fixed arms | every threshold |
| UCB | 50 training episodes |
| epsilon-greedy | 50 training episodes |
| per-step Q | 0037 reference |

## Results (0038)

Seeds 700–704; 50 training episodes from 9000+.

| policy | threshold | score | success |
|---|---:|---:|---:|
| fixed best | 0.7/0.8/0.9 | 250.0 | 1.00 |
| UCB | 0.7 | **250.0** | 1.00 |
| epsilon-greedy | 0.8 | **250.0** | 1.00 |
| per-step Q (0037) | — | 178.0 | 0.40 |

All gates pass: the threshold meta-action gains +72 over per-step Q. See
[`experiments/0038-preventive-threshold`](../experiments/0038-preventive-threshold/summary.md).

## Known pitfalls

- **Deterministic arms.** Every seed has the same arm returns; the bandit is a
  representation check, not a sample-efficiency challenge.
- **One decision per episode.** This is not sequential maintenance control.
- **Threshold 1.0 is not exactly noop.** It can maintain at wear 20 before a
  fault; its score matches noop at 200.
- **Most-worn target only.**
- **Not part of `factory-v0.1`.**

## Changelog

- 2026-11-22 — card created; threshold-selection task and gates preregistered.
- 2026-11-22 — formal run: UCB 0.7 and epsilon 0.8 both score 250; all gates pass.
