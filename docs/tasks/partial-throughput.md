# Task card — partial-observability throughput

- **Task ID:** `factory.throughput.partial.v1`
- **Version:** 0.1.0
- **Status:** debug/P0 task; not part of `factory-v0.1`
- **World:** factory-0.1.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Predict future depot score when the current observation is incomplete. A binary
mask says which features were observed. A short window of recent masked frames
may recover the hidden state.

## Contract

- **Observation:** 7 layout-context features + 6 line-buffer features (13).
- **Corruption:** 60% feature dropout, independent of tick; binary mask appended.
- **Views:**
  - `current` — full 13 features;
  - `single` — masked values + mask (26);
  - `window` — last 4 masked frames + masks (104).
- **Action:** none; offline supervised projection.
- **Label:** future depot score over 50 ticks.
- **Scenario:** fixed gear line.
- **Sampling:** every 10 ticks after 150 warmup ticks; 300-tick episode.
- **Episodes:** 100; splits 70% train / 20% val / 10% test.

## Data

- 800 samples; 560 / 160 / 80 train / val / test.
- Labels take two values (20 and 30) on this line.
- Dataset card: [`partial-window-debug-v0.1`](../datasets/partial-window-debug-v0.1.md).

## Metrics

Test R², with 95% bootstrap CIs over test rows.

## Baselines

| Baseline | Notes |
|---|---|
| mean | Predict the training mean |
| linear | Least squares |
| GBDT | Histogram gradient boosting |
| MLP | One hidden layer, 64 units, max 500 iterations |

## Results

| method | current | single masked | window |
|---|---:|---:|---:|
| linear | 0.752 | 0.164 | 0.578 |
| GBDT | 1.000 | 0.593 | 0.883 |
| MLP | 0.613 | −0.194 | 0.002 |

## Known pitfalls

- **Two label values.** GBDT on the full frame is at ceiling.
- **Mask leakage was a real risk.** The pilot's tick-seeded mask encoded phase;
  formal masks are seeded per sample, independent of tick.
- **Window is not a sequence representation.** Concatenation is a baseline, not
  an RNN/Transformer.
- **Small test set.** 80 rows; CIs are wide.
- **One fit per model.** No seed sweep.
- **Fixed periodic line.** The task tests missing features, not non-periodic
  dynamics.

## Negative controls

- Mean should be R² 0.
- Single masked should be below current for every learned baseline.
- The window should not exceed the full current view.

## Changelog

- 2026-11-21 — card created; P0 masked-window results added.
