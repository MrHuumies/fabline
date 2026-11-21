# Experiment 0022 — Calibration on stochastic power

- **Status:** complete
- **Date:** 2026-11-21
- **Type:** engineering addition plus a debug measurement; not a pre-registered
  research experiment
- **World:** factory-0.1.0 + stochastic PowerConfig
- **Benchmark:** none; `factory-v0.1` unchanged
- **Coverage-map slice:** P0 calibration/risk

## Result in one paragraph

**The stochastic power benchmark now reports calibration, and the result is
mixed.** On 8,000 samples per view, GBDT is the stronger discriminator (balanced
accuracy 0.538 vector / 0.551 power) but less calibrated (ECE 0.042 / 0.035).
The MLP is better calibrated (ECE 0.016 / 0.020) but close to the majority
classifier on balanced accuracy (0.500 / 0.510). The power view improves Brier
and NLL for both models, improves GBDT ECE, but slightly worsens MLP ECE.
Calibration and discrimination are not the same axis; report both.

## What was added

- `calibration_metrics` in `harness/metrics.py`:
  - Brier score;
  - negative log-likelihood;
  - expected calibration error (ECE, 10 bins);
  - mean confidence and threshold accuracy.
- `evaluate_calibration_baselines` in `harness/baselines.py` for GBDT and MLP
  probabilities, with bootstrap CIs over test rows.
- A calibration section in `power_report.md` for each view.
- CLI jitter flags for `power-benchmark`.
- Tests for calibration metrics, evaluator, and the power benchmark report.

## Data

- 100 episodes; gear line; one generator, capacity 9, radius 8.
- Stochastic power: load jitter 60, capacity jitter 40, period 10.
- 5-tick sampling; 5-tick brownout horizon.
- 8,000 samples per view; positive rate 0.2269.
- Splits: 5,600 / 1,600 / 800 train / val / test.

## Results

Test split; bootstrap 95% CIs over test rows.

### Vector view

| method | accuracy | balanced | macro F1 | Brier | NLL | ECE |
|---|---:|---:|---:|---:|---:|---:|
| GBDT | 0.7837 | 0.5384 | 0.5278 | 0.1639 | 0.5166 | 0.0421 |
| MLP | 0.7875 | 0.5000 | 0.4406 | 0.1672 | 0.5168 | 0.0158 |
| majority | 0.7875 | 0.5000 | 0.4406 | — | — | — |

### Power view

| method | accuracy | balanced | macro F1 | Brier | NLL | ECE |
|---|---:|---:|---:|---:|---:|---:|
| GBDT | 0.7588 | 0.5505 | 0.5527 | 0.1594 | 0.4859 | 0.0353 |
| MLP | 0.7900 | 0.5102 | 0.4637 | 0.1606 | 0.4950 | 0.0204 |
| majority | 0.7875 | 0.5000 | 0.4406 | — | — | — |

## Interpretation

- **GBDT discriminates, MLP calibrates.** The MLP's accuracy is close to the
  majority rate, so its low ECE is easy to achieve; do not read calibration as
  skill.
- **The power view improves probability quality slightly.** Brier and NLL fall
  for both models; GBDT ECE improves from 0.042 to 0.035. MLP ECE rises from
  0.016 to 0.020.
- **ECE is sensitive to bins and sample size.** The test set has 800 rows and
  182 positives; the CIs are wide. Treat these as debug numbers.
- **Calibration is a missing axis in the other tasks.** Fault prediction and
  fault onset do not report Brier/NLL/ECE yet.

## Caveats

- One gear line, generator layout, budget, and jitter regime.
- One deterministic fit per model (random_state 0); CIs are row-bootstrap, not
  seed-to-seed.
- MLP convergence warnings are expected at the fixed 500-iteration budget.
- The 60/40/10 regime is a chosen scope condition, not tuned for calibration.
- Not a frozen benchmark; do not compare to `factory-v0.1`.

## Next P0

1. Partial-observability wrappers and a memory/state-estimation task.
2. End-to-end GNN/Transformer/CNN/RNN baselines on existing views.
3. Optional: add calibration to fault prediction and fault onset.

## Artifacts

- Run: `.venv/bin/python -m fabline power-benchmark --out results/power-calibration --episodes 100 --load-jitter 60 --capacity-jitter 40 --variation-period 10`
- Code: `src/fabline/harness/metrics.py`, `src/fabline/harness/baselines.py`,
  `src/fabline/harness/power.py`
- Task card: `docs/tasks/power-brownout.md`
- Dataset card: `docs/datasets/power-debug-v0.1.md`
