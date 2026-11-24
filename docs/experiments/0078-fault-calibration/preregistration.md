# Experiment 0078 — Fault calibration

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 calibration experiment
- **Task:** `factory.fault.calibration.v1` (debug/P3, not in `factory-v0.1`)
- **Code:** `src/fabline/harness/fault_calibration.py`
- **CLI:** `python -m fabline fault-calibration`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Do fault probabilities stay calibrated on a view that has real discrimination
skill, and do the base views only look calibrated because they are near the
majority class?

## Pilot

40 episodes, seed 55,000, horizon 10, sample interval 5, noise 0.30:
3,160 samples, positive rate 0.076.

| view | model | balanced | Brier | NLL | ECE |
|---|---|---:|---:|---:|---:|
| context+thermal | GBDT | 0.490 | 0.0884 | 0.4507 | 0.0646 |
| context+thermal | MLP | 0.500 | 0.0696 | 0.2641 | 0.0136 |
| +vibration | GBDT | 0.498 | 0.0778 | 0.4505 | 0.0678 |
| +vibration | MLP | 0.500 | 0.0696 | 0.2646 | 0.0059 |
| +top-4 | GBDT | 0.957 | 0.0078 | 0.0653 | 0.0086 |
| +top-4 | MLP | 0.868 | 0.0163 | 0.0532 | 0.0272 |

The base views are near majority; low ECE there is not skill. The top-4 view is
skilled and calibrated for GBDT; MLP has lower NLL but higher ECE.

## Design

- Three formal blocks: 56,000, 56,100, 56,200; 40 episodes each.
- Same views, label, noise, and models.
- No post-hoc calibration fitting in this slice; raw probabilities first.

## Gates

| Gate | Threshold |
|---|---|
| H1 top-4 skill | GBDT balanced accuracy ≥ 0.70 |
| H2 top-4 calibration | GBDT ECE ≤ 0.05 |
| H3 view effect | top-4 balanced ≥ context+thermal + 0.10 |
| H4 base caveat | base balanced near 0.50 |
| H5 frozen benchmark | unchanged |

## Predictions

- Top-4 GBDT balanced 0.90–0.97, ECE 0.005–0.02.
- Base views balanced 0.48–0.52.
- H1/H2/H3 pass; H4 is a reported caveat.
- If top-4 calibration fails, report a negative calibration result.

## Kill criteria

- Top-4 balanced under 0.70: no skill to calibrate.
- ECE over 0.05: calibration fails.
- No post-hoc view or noise tuning.

## Transparency note

The pilot is one 40-episode block. Formal blocks are fresh and aggregated.
