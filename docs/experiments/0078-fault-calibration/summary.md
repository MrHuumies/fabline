# Experiment 0078 — Fault calibration

- **Status:** complete (positive on skilled top-4 view; base views are a caveat)
- **Date:** 2026-11-24
- **Type:** P3 calibration experiment
- **Task:** `factory.fault.calibration.v1` (debug/P3, not in `factory-v0.1`)
- **Code:** `src/fabline/harness/fault_calibration.py`
- **CLI:** `python -m fabline fault-calibration`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Calibration is meaningful only where the model has skill.** Across three
40-episode blocks, the context + thermal and + vibration views are at majority
(balanced 0.50) even when ECE looks low. The top-4 entity sensor view is skilled:
GBDT balanced **0.950 ± 0.011**, Brier **0.0084**, NLL **0.0386**, ECE
**0.0080**; MLP balanced **0.897 ± 0.041**, Brier 0.0171, NLL 0.0557, ECE
0.0167. H1/H2/H3/H5 pass; H4 is the reported base-view caveat.

## Formal results

Mean ± std over three blocks (56,000 / 56,100 / 56,200), 3,160 samples per
block, positive rate 0.076:

| view | model | balanced | Brier | NLL | ECE |
|---|---|---:|---:|---:|---:|
| context+thermal | GBDT | 0.500 ± 0.013 | 0.0824 | 0.3997 | 0.0653 |
| context+thermal | MLP | 0.500 ± 0.000 | 0.0705 | 0.2706 | 0.0142 |
| +vibration | GBDT | 0.496 ± 0.014 | 0.0845 | 0.4673 | 0.0703 |
| +vibration | MLP | 0.500 ± 0.000 | 0.0705 | 0.2705 | 0.0154 |
| **+top-4** | **GBDT** | **0.950 ± 0.011** | **0.0084** | **0.0386** | **0.0080** |
| +top-4 | MLP | 0.897 ± 0.041 | 0.0171 | 0.0557 | 0.0167 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 top-4 skill | balanced ≥ 0.70 | **pass**, 0.950 |
| H2 top-4 calibration | ECE ≤ 0.05 | **pass**, 0.008 |
| H3 view effect | top-4 ≥ base + 0.10 | **pass**, +0.45 |
| H4 base caveat | report base near 0.50 | pass, reported |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Low ECE without skill is not calibration.** The base views are at majority;
  their low MLP ECE is easy and not evidence of a useful probability model.
- **The skilled view is well calibrated for GBDT.** ECE 0.008 and Brier 0.0084
  on a 7.6% positive rate.
- **MLP trades NLL for ECE.** It has lower NLL (0.0557 vs 0.0386? Actually GBDT
  NLL 0.0386 is lower; MLP NLL 0.0557, so GBDT wins both NLL and ECE) and worse
  balanced/ECE on top-4.
- **Calibration is not a separate task from skill.** The task must report both.
- **Top-4 is a strong view.** It uses pre-noise selection and 32 features; do
  not generalize the calibration result to aggregate sensors.

## Caveats

- Three 40-episode blocks; row-bootstrap CIs, not seed-to-seed.
- Top-4 uses pre-noise selection and 32 features.
- No post-hoc calibration fitting (Platt/isotonic) in this slice.
- One gear line, one fault threshold, horizon 10.
- Not part of frozen `factory-v0.1`.

## Next

1. **Causal intervention task:** remove/disable a component and compare
   observational vs interventional prediction.
2. Optional calibration follow-up: Platt/isotonic on the skilled view.
3. Keep the frozen benchmark unchanged.

## Artifacts

- Task card: [`../../tasks/fault-calibration.md`](../../tasks/fault-calibration.md)
- Code: `src/fabline/harness/fault_calibration.py`
- Raw results: `results/fault-calibration/` (ignored)
