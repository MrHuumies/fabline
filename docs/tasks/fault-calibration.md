# Task card — fault calibration

- **Task ID:** `factory.fault.calibration.v1`
- **Version:** 0.1.0
- **Status:** P3 calibration task; formal positive on top-4 view
- **World:** factory-0.1.0 + opt-in faults
- **Owner:** FABLINE
- **Date:** 2026-11-24

## Phenomenon

Fault probabilities should be calibrated, not just discriminative. On hard
event-aligned views (context + thermal/vibration), the base signal is weak; the
top-4 entity sensor view adds skill. The task checks Brier, NLL, and ECE on a
model that can actually predict.

## Contract

- **Labels:** fault starts within 10 ticks.
- **Views:** context 7 + thermal 2; + vibration 2; + top-4 entity sensors 32.
- **Data:** 16×8 gear line, faults enabled, noise 0.30, 5-tick sampling.
- **Splits:** episode-grouped 70/20/10.
- **Models:** GBDT and MLP probabilistic classifiers.
- **Metrics:** accuracy/balanced accuracy, Brier, NLL, ECE.

## Gates

| Gate | Threshold |
|---|---|
| H1 top-4 skill | GBDT balanced accuracy ≥ 0.70 |
| H2 top-4 calibration | GBDT ECE ≤ 0.05 |
| H3 view effect | top-4 balanced accuracy ≥ context+thermal + 0.10 |
| H4 base-view caveat | report base balanced accuracy near 0.50 |
| H5 frozen benchmark | unchanged |

## Metrics

- Brier, NLL, ECE;
- accuracy / balanced accuracy;
- positive rate;
- per-view comparison.

## Baselines

| Baseline | Notes |
|---|---|
| majority | class prior |
| GBDT | histogram gradient boosting |
| MLP | small neural classifier |

## Known pitfalls

- Base views have almost no skill; low ECE there is easy.
- Top-4 uses pre-noise selection and 32 features.
- Calibration is row-bootstrap, not seed-to-seed.
- Not part of `factory-v0.1`.

## Results (0078)

Three 40-episode blocks; top-4 view:

| model | balanced | Brier | NLL | ECE |
|---|---:|---:|---:|---:|
| GBDT | 0.950 ± 0.011 | 0.0084 | 0.0386 | 0.0080 |
| MLP | 0.897 ± 0.041 | 0.0171 | 0.0557 | 0.0167 |

Base context+thermal is at majority (balanced 0.50), so its low ECE is not
skill. H1/H2/H3/H5 pass; H4 caveat reported. See
[`experiments/0078-fault-calibration`](../experiments/0078-fault-calibration/summary.md).

## Changelog

- 2026-11-24 — task card created; calibration gates defined.
- 2026-11-24 — formal run positive on top-4; base views at majority.
