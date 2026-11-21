# Task card — next-state prediction

- **Task ID:** `factory.next_state.predict.v1`
- **Version:** 0.1.0
- **Status:** benchmark candidate (`factory-v0.1`), saturated
- **World:** factory-0.1.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Predict the vector observation 10 ticks ahead. This is a passive
self-supervised dynamics task: it tests whether a representation captures how
the factory evolves, without labels or actions.

## Contract

- **Observation:** `vector` (18 features).
- **Action:** none; the world evolves passively.
- **Target:** the vector observation at `t + 10`.
- **Sampling:** every 10 ticks after a jittered warmup.
- **Splits:** same scenario plan as throughput.
- **Metrics:** MSE, MAE, mean cosine with 95% bootstrap confidence intervals.
- **Baselines:** copy, linear, MLP.

## Data — `factory-v0.1`

- 46 episodes, 852 samples (shared with the other projections).
- Test: 110 samples; shift: 110 samples.

## Results — `factory-v0.1`

Test:

| method | MSE | cosine |
|---|---:|---:|
| copy | 0.0006 | 0.9974 |
| linear | **0.0000** | **0.9998** |
| MLP | 0.0022 | 0.9883 |

Shift:

| method | MSE | cosine |
|---|---:|---:|
| copy | 0.0005 | 0.9973 |
| linear | 0.0000 | 0.9998 |
| MLP | 0.0028 | 0.9828 |

## Known pitfalls

- **Saturated by copy/linear.** In a steady-state factory with tick and
  cumulative-production features, the next observation is nearly the current
  observation and nearly linear in time.
- **Measures continuity, not useful dynamics.** A low MSE does not imply a
  world model that supports planning.
- **No interventions.** The task cannot test action-conditioned dynamics.
- **Not a representation-quality claim.** Downstream probes are needed.

## Next variant

- Action-conditioned dynamics is now covered separately by
  [`control-dynamics.md`](control-dynamics.md).
- A future variant should use transient regimes, masked state, or longer
  horizons with non-stationary mechanics.

## Changelog

- 2026-11-21 — card created; M2 debug results added.
- 2026-11-21 — shared-episode results added; saturation confirmed.
