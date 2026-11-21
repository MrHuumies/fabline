# Task card — brownout prediction

- **Task ID:** `factory.power.brownout.v1`
- **Version:** 0.1.0
- **Status:** debug task, opt-in power mechanic; not part of `factory-v0.1`
- **World:** factory-0.1.0 + PowerConfig
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Predict whether a new power brownout will start within the next 5 ticks. A
brownout happens when an active machine's power demand exceeds the generator
capacity that reaches it. The task tests whether the power view exposes
allocation problems before production loss becomes obvious.

## Contract

- **Observations:** `power` (12 features) or `vector` (18 features, no explicit
  power channels).
- **Action:** none; offline supervised projection.
- **Label:** `brownout_within_horizon` — 1 if a new `power_brownout` event
  occurs in the next 5 ticks, else 0.
- **Scenario:** fixed gear line; `PowerConfig` enabled.
- **Power config:** one generator, capacity 9, radius 8. A stochastic variant
  uses load jitter 60, capacity jitter 40, and a 10-tick variation period.
- **Demand:** activity-gated: miner 2 continuously; belts 1 while carrying;
  furnace 3 while crafting; assembler 4 while crafting; depot 0.
- **Sampling:** every 5 ticks after 100 warmup ticks; 500-tick episode.

## Data

`power-benchmark` debug run:

- 40 episodes, 3,200 samples per view.
- Positive rate 0.366.
- Splits by seed: 70% train / 20% val / 10% test.
- Replays validated with the power config.
- Dataset card: [`power-debug-v0.1`](../datasets/power-debug-v0.1.md).

## Metrics

Accuracy, balanced accuracy, macro F1, with 95% bootstrap CIs.

## Baselines

| Baseline | Notes |
|---|---|
| majority | Predict the training majority class |
| GBDT | Histogram gradient boosting |
| MLP | One hidden layer, 64 units |

## Debug results

Test split:

| view | method | accuracy | balanced | macro F1 |
|---|---|---:|---:|---:|
| vector | majority | 0.625 | 0.500 | 0.385 |
| vector | GBDT | **1.000** | **1.000** | **1.000** |
| vector | MLP | 0.763 | 0.743 | 0.745 |
| power | majority | 0.625 | 0.500 | 0.385 |
| power | GBDT | **1.000** | **1.000** | **1.000** |
| power | MLP | **0.825** | **0.773** | **0.792** |

## View-arrival results

- **0017 (vector + line base):** base AP 1.0000; power adds 0.0000. The line
  buffers determine the label. A ceiling, not a redundancy result.
- **0018 (vector + context base, no line buffers):** base AP 0.6652; residual
  power 0.9150 (+0.2499) with exact retention; full 0.9451 (+0.2799) and old
  AP +0.0436. H3 fails because the residual underfits full by 0.0301.
- **0019 (stochastic power, no line buffers):** base AP 0.2362; residual power
  0.3204 (+0.0842) with exact retention; full 0.3179 (+0.0817). All gates pass.

## Calibration

The power benchmark now reports Brier score, negative log-likelihood, and ECE
(10 bins) for GBDT and MLP. On the stochastic 60/40/10 regime:

| view | method | balanced | Brier | NLL | ECE |
|---|---|---:|---:|---:|---:|
| vector | GBDT | 0.538 | 0.164 | 0.517 | 0.042 |
| vector | MLP | 0.500 | 0.167 | 0.517 | 0.016 |
| power | GBDT | 0.551 | 0.159 | 0.486 | 0.035 |
| power | MLP | 0.510 | 0.161 | 0.495 | 0.020 |

The MLP is better calibrated but close to the majority classifier; calibration
is not skill. See
[`experiments/0022-calibration-stochastic-power`](../experiments/0022-calibration-stochastic-power/summary.md).

## Known pitfalls

- **Too easy for GBDT.** The vector view's tick and production history expose
  the load cycle; GBDT solves both views. Do not present this as a hard
  benchmark.
- **The power MLP is the view comparison.** It reaches 0.825 versus 0.763 for
  the vector MLP.
- **One fixed line, generator layout, and budget.** No held-out layouts or
  capacity regimes yet.
- **Generators are pre-placed.** They are not buildable in phase 1.
- **The label is event-based.** It predicts a new brownout transition, not a
  sustained unpowered state.
- **Line buffers saturate the task.** With vector + line, AP is 1.0. Hide the
  line buffers to measure the power view.
- **GBDT saturates the hidden-line task.** The neural residual is the view
  comparison; do not overread GBDT at 1.0.
- **Small debug budget.** CIs are wide; test episodes are few.

## Negative controls

- Majority should be weak on balanced accuracy.
- The vector view has no explicit power channels; a model that cannot beat
  majority on the power view is not using the grid data.

## Changelog

- 2026-11-21 — card created; power-grid debug benchmark added.
- 2026-11-21 — power view-arrival results added (0017 ceiling, 0018 +0.2499,
  0019 +0.0842 under stochastic power).
- 2026-11-21 — calibration metrics added (Brier, NLL, ECE).
