# Task card — fault prediction

- **Task ID:** `factory.fault.predict.v1`
- **Version:** 0.2.0
- **Status:** debug task, opt-in fault mechanic; not part of `factory-v0.1`
- **World:** factory-0.1.0 + FaultConfig
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Predict whether any machine will fault within the next 50 ticks. The task tests
whether diagnostic channels expose wear before production loss becomes obvious.

## Contract

- **Observations:** `diagnostics` (13 features, sensor model 0.2.0) or `vector`
  (18 features, no explicit wear/fault channels).
- **Action:** none; offline supervised projection.
- **Label:** `fault_within_horizon` — 1 if a new `fault_started` event occurs in
  the next 50 ticks, else 0.
- **Scenario:** fixed gear line; `FaultConfig` enabled.
- **Fault config:** wear per craft 1, threshold 20, repair 30 ticks.
- **Sampling:** every 10 ticks after 100 warmup ticks; 500-tick episode.

## Data

`fault-benchmark` debug run:

- 40 episodes, 1,440 samples per view.
- Positive rate 0.306.
- Splits by seed: 70% train / 20% val / 10% test.
- Replays validated with the fault config.
- Dataset card: [`fault-debug-v0.2`](../datasets/fault-debug-v0.2.md).

## Metrics

Accuracy, balanced accuracy, macro F1, with 95% bootstrap CIs.

## Baselines

| Baseline | Notes |
|---|---|
| majority | Predict the training majority class |
| GBDT | Histogram gradient boosting |
| MLP | One hidden layer, 64 units |

## Debug results

Test split, dynamic sensor model 0.2.0:

| view | method | accuracy | balanced | macro F1 |
|---|---|---:|---:|---:|
| vector | majority | 0.694 | 0.500 | 0.410 |
| vector | GBDT | **1.000** | **1.000** | **1.000** |
| vector | MLP | 0.750 | 0.667 | 0.678 |
| diagnostics | majority | 0.694 | 0.500 | 0.410 |
| diagnostics | GBDT | **1.000** | **1.000** | **1.000** |
| diagnostics | MLP | **1.000** | **1.000** | **1.000** |

Historical note: the first version of this card (sensor model 0.1.0, static
channels) reported the same table. The dynamic channels changed the data path,
not the conclusion that this task is easy for GBDT.

## Known pitfalls

- **Too easy for GBDT.** The vector view already contains enough production and
  entity-count signal; GBDT solves both views. Do not present this as a hard
  benchmark.
- **The diagnostics MLP is the real view comparison.** It reaches 1.0 versus
  0.75 for the vector MLP, which is the sensor-channel signal.
- **One fixed gear line and one fault threshold.** No held-out layouts or fault
  severities yet.
- **Prediction, not recovery.** Repair is a separate action and a separate
  two-action task.
- **Small debug budgets.** CIs are wide; test episodes are few.

## Negative controls

- Majority should be weak on balanced accuracy.
- The vector view has no explicit wear/fault channels; a model that cannot beat
  majority on diagnostics is not using the sensor data.

## Changelog

- 2026-11-21 — card created; fault debug benchmark added.
- 2026-11-21 — task version 0.2.0; diagnostics sensor model 0.2.0
  (dynamic channels). Results table rerun and unchanged.
