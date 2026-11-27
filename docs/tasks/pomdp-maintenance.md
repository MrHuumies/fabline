# Task card — POMDP maintenance under noisy faults

- **Task ID:** `factory.fault.pomdp-maintenance.v1` (draft)
- **Version:** 0.1.0-draft
- **Status:** deferred to 0.8.0; design only (ADR 0043)
- **World:** `factory-0.1.0` + opt-in stochastic faults/sensors
- **Owner:** FABLINE
- **Date:** 2026-11-26
- **RFC:** [`0032-uncertain-repair.md`](../rfcs/0032-uncertain-repair.md)

## Phenomenon

A machine accumulates hidden wear and fails stochastically. Sensors are noisy
and sometimes false-alarm. The agent chooses inspect, repair, or continue; the
true wear/fault state is not directly observed. The task tests belief-state
estimation, calibration, and preventive control.

## Contract (draft)

- **Observation:** noisy sensor history (temperature, vibration, acoustic),
  production state, maintenance budget; no true wear/fault state.
- **Action:** noop/continue, inspect, repair; optional priority.
- **Dynamics:** stochastic onset hazard depends on wear/load/maintenance;
  sensor noise/drift and false positives/negatives; correlated failures via
  shared power/load.
- **Reward:** production minus inspection/repair costs and downtime.
- **Episode:** 500 ticks; decision interval 10.
- **Success:** fixed at pre-registration.
- **Labels:** true fault onset/wear in `info` for evaluation only.

## Baselines

| Baseline | Rule |
|---|---|
| threshold/reactive | repair at a sensor threshold |
| GBDT | tabular onset/risk prediction |
| HMM | discrete hidden state filter |
| Kalman/particle filter | continuous belief |
| survival model | Cox/Weibull hazard |
| belief-state RL | POMDP policy |
| POMDP solver | small-state exact/approx solver |

## Gates (draft)

| Gate | Threshold |
|---|---|
| H1 detection skill | balanced/AUROC over base rate |
| H2 calibration | ECE ≤ 0.05 with skill |
| H3 control | belief policy ≥ best threshold + 10 |
| H4 success | best learned success ≥ 0.60 |
| H5 cost | report inference/training cost |

## Known pitfalls

- **Calibration is not skill.** Report skill first; low ECE at majority is not a
  calibration result.
- **Noise model must be in the observation spec.** Do not leak true wear.
- **Hidden state must be seeded and replayable.**
- **Do not add another calibration view without a skill gate.**
- **Sensor history needs a window/RNN; a single frame may be insufficient.**

## Changelog

- 2026-11-26 — design card created.
- 2026-11-28 — deferred to 0.8.0; 0.7.0 is deterministic sequential crews.
