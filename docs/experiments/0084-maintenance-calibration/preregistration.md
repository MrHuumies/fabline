# Experiment 0084 — Maintenance-risk calibration

- **Status:** complete (mixed; see [summary](summary.md))
- **Date:** 2026-11-25
- **Type:** P3 calibration follow-up
- **Task:** `factory.fault.maintenance_calibration.v1` (debug/P3, not in
  `factory-v0.2`)
- **Code:** planned `src/fabline/harness/maintenance_calibration.py`
- **CLI:** planned `python -m fabline maintenance-calibration`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Are maintenance-risk probabilities calibrated on a state distribution where the
model has real fault-prediction skill?

## Hypothesis

A lightly maintained line produces states where a fault is likely within the
next 10 ticks, but the exact timing depends on future activity and maintenance
state. A probabilistic model should have skill and non-degenerate calibration,
unlike the saturated 50-tick fault task and the near-majority base views in 0078.

## Task

- Gear line, faults enabled, preventive-maintenance environment.
- Behavior policy: 5% random maintenance, 95% noop, sampled with a seeded RNG.
- Sample every 10 ticks after 100 warmup ticks; 500-tick episodes.
- Observation: the existing preventive-maintenance 15-feature view (13
  diagnostics + maintenance count + remaining time).
- Label: a `fault_started` event occurs within the next 10 ticks **under no
  further maintenance** (a clone with events enabled).
- Splits: episode-grouped 70/20/10 by seed.
- Models: GBDT and MLP probabilistic classifiers; majority baseline.

## Pilot

40 episodes, seeds 60,000–60,039, horizon 10, maintenance probability 0.05:

| view | model | balanced | Brier | ECE |
|---|---|---:|---:|---:|
| diagnostics + maintenance | GBDT | 0.977 | — | 0.014 |
| diagnostics + maintenance | MLP | 0.974 | — | 0.044 |

Positive rate 0.631; test positive rate 0.594. A 0.20 maintenance probability
was too sparsely positive and had weak skill (balanced 0.61, ECE 0.15). The
0.05 regime is the calibration task; the 0.20 regime is a negative pilot, not a
formal condition.

## Formal design

- 60 fresh episodes: seeds 61,000–61,059.
- Same behavior policy, horizon, observation, models, and splits.
- No sensor noise; calibration is about state aliasing and future-activity
  uncertainty, not sensor noise.
- No post-hoc threshold or maintenance-probability tuning.

## Gates

| Gate | Threshold |
|---|---|
| H1 skill | GBDT balanced accuracy ≥ 0.75 |
| H2 calibration | GBDT ECE ≤ 0.05 |
| H3 view relevance | GBDT balanced ≥ majority + 0.20 |
| H4 base caveat | report positive rate and majority balanced |
| H5 frozen benchmark | `factory-v0.2` unchanged |

If H1 fails, the task is near majority and the calibration result is negative.
If H2 fails, report miscalibration; do not refit post-hoc.

## Predictions

- Positive rate 0.55–0.70; test positive rate 0.5–0.7.
- GBDT balanced 0.95–0.99, ECE 0.005–0.03.
- MLP balanced 0.93–0.98, ECE 0.02–0.06.
- H1/H2/H3 pass if the pilot replicates; H4 is reported.

## Kill criteria

- GBDT balanced under 0.75: no skill to calibrate.
- GBDT ECE over 0.05: miscalibration.
- No post-hoc view, horizon, noise, or behavior tuning.

## Transparency note

The pilot chose the 0.05 maintenance / 10-tick regime from a small design sweep.
Formal seeds are fresh and disjoint. The task is a calibration diagnostic, not a
deployment risk model.
