# Task card — fault onset detection

- **Task ID:** `factory.fault.onset.v1`
- **Version:** 0.3.0
- **Status:** debug/experiment task; opt-in fault mechanic; not in `factory-v0.1`
- **World:** factory-0.1.0 + FaultConfig
- **Sensor model:** `sensors` / `diagnostics` 0.2.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Detect that a machine fault has just started from diagnostic channels. The task
samples every tick and asks whether a `fault_started` event occurred in the last
10 ticks. It tests event detection at the timescale of the acoustic channel,
rather than prediction of a future fault or a sustained fault state.

## Contract

- **Observations:** `context` (7 layout counts), `thermal` (2), `vibration` (2),
  `acoustic` (2), `entity_sensors_top4` (32: top four entities by acoustic,
  each with mask/acoustic/vibration/temperature/wear/faulted/crafting/type),
  or control views: aggregate acoustic (2), order4 (4), order4_type (8),
  top4_true (32), top4_noisy (32). Each sensor view has independent Gaussian
  noise `sigma = 0.30`, clipped to [0, 1].
- **Action:** none; offline supervised projection.
- **Label:** `fault_recent` — 1 if a `fault_started` event occurred in the last
  10 ticks, including the current tick.
- **Scenario:** fixed gear line; `FaultConfig` enabled.
- **Fault config:** wear per craft 1, threshold 20, repair 30 ticks.
- **Sampling:** every 1 tick after 100 warmup ticks; 500-tick episode.
- **Episodes:** 40.
- **Splits:** by episode seed, 70% train / 20% val / 10% test.

## Data

- 15,640 samples; 10,948 / 3,128 / 1,564 train / val / test.
- Positive rate 0.0767; 120 positive test rows across 4 test episodes.
- Dataset card: [`fault-onset-debug-v0.1`](../datasets/fault-onset-debug-v0.1.md).

## Metrics

Average precision (primary). Accuracy and balanced accuracy are reported by the
neural conditions. 95% bootstrap CIs over five model seeds.

## Baselines

| Baseline | Notes |
|---|---|
| majority | Predict the training majority class |
| GBDT | Histogram gradient boosting on context + thermal, with acoustic and/or vibration |
| neural base | context + thermal, or context + thermal + vibration |
| residual | frozen base + zero-gated acoustic head |
| full | all views fine-tuned |

## Debug results

Recent-onset AP, five seeds:

| base | method | all AP | gain | retention |
|---|---|---:|---:|---:|
| context + thermal (0.1497) | residual | 0.1636 | +0.0139 | 0.0000 |
| context + thermal (0.1497) | full | 0.1645 | +0.0148 | +0.0014 |
| context + thermal + vibration (0.1592) | residual | 0.1650 | +0.0058 | 0.0000 |
| context + thermal + vibration (0.1592) | full | 0.1672 | +0.0080 | +0.0020 |

GBDT: context + thermal 0.1410; + acoustic 0.1495; + vibration 0.1422; + both
0.1438.

Per-entity view (experiment 0013), same task:

| new view | method | all AP | gain | retention |
|---|---|---:|---:|---:|
| aggregate acoustic (2) | residual | 0.1262 | +0.0025 | 0.0000 |
| top-4 entity sensors (32) | residual | 0.7313 | +0.6075 | 0.0000 |
| top-4 entity sensors (32) | full | 0.8504 | +0.7267 | −0.0641 |

An acoustic-only top-4 ablation still gains +0.3946, so the pooling effect is
not only the per-entity fault flag. Full fine-tuning fits the new view better
but forgets old-view AP.

Control results (experiment 0014), noisy-selection and capacity:

| new view | dims | residual AP | gain | retention |
|---|---:|---:|---:|---:|
| aggregate noisy mean/max | 2 | 0.2957 | +0.1534 | 0.0000 |
| order4 noisy values | 4 | 0.3151 | +0.1729 | 0.0000 |
| order4_type | 8 | 0.3429 | +0.2006 | 0.0000 |
| top4_true | 32 | 0.7169 | +0.5746 | 0.0000 |
| top4_noisy | 32 | 0.7056 | +0.5633 | 0.0000 |
| top4_noisy, full | 32 | 0.7341 | +0.5919 | −0.0234 |

Noisy selection costs only 0.0113 AP. The post-hoc equal-capacity order2 view
gains only +0.0194, versus +0.1534 for mean/max, so pure rank pooling is not
supported. Noisy selection halves the acoustic-only gain (+0.3946 → +0.1884).

The prediction control (`future_fault`, next 10 ticks) does not gain from
aggregate acoustic: 0.0839 with acoustic vs 0.0859 without. The top-4 view does
gain on future fault (+0.1257), driven mainly by per-entity wear; the noisy
top-4 control adds +0.1219 in GBDT, while order statistics add ~0.

## Known pitfalls

- **Temporally correlated samples.** 1-tick sampling means the effective sample
  size is much lower than the row count. Do not treat 15,640 rows as independent.
- **Aggregate views.** Mean/max over the grid dilutes a per-entity onset spike.
  A per-entity view is a different task.
- **Weak absolute signal.** AP 0.15 against a 0.077 positive rate; the task is
  hard, and gains are relative to a weak base.
- **One fixed line and threshold.** No held-out layouts or fault severities.
- **Event detection, not prediction.** The label is post-onset; do not compare
  its AP to the 50-tick prediction task.
- **Acoustic is not uniquely useful.** Vibration already captures most of the
  detection signal once it is in the base.
- **Top-4 uses pre-noise selection.** The slots are chosen from true acoustic
  values before dataset noise. A noisy-selection view is a different
  representation.
- **Top-4 has 32 features vs 2 for aggregate.** The acoustic-only ablation
  (12 features) still gains, but some of the gap may be capacity, not pooling.
- **Equal-capacity rank pooling is not supported.** In the control, order2 gains
  +0.0194 versus +0.1534 for mean/max. The top-4 advantage is per-entity detail
  and joint state, not an order-statistic pooling rule.
- **Noisy selection halves the acoustic-only gain.** The full joint view is
  robust, but acoustic-only is selection-sensitive.

## Negative controls

- Acoustic should not add AP on `future_fault`; the observed GBDT change is
  −0.0020.
- A majority baseline should be weak on balanced accuracy.

## Changelog

- 2026-11-21 — card created; event-aligned acoustic experiment added.
- 2026-11-21 — task version 0.2.0; top-4 entity sensor view and 0013 results
  added.
- 2026-11-21 — task version 0.3.0; noisy-selection and capacity controls added.
