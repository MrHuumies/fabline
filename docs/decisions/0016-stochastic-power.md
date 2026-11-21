# ADR 0016 — Stochastic power variation

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** RFC 0006, RFC 0004, ADR 0014

## Context

The deterministic power grid made brownout prediction mechanical: line buffers
and craft progress determine the future label, so the power view had no headroom
with the strong base (0017). A stochastic supply/demand regime gives the task
genuine uncertainty and tests robustness without adding hidden runtime RNG.

## Decision

1. Add `load_jitter`, `capacity_jitter`, and `variation_period` to
   `PowerConfig`, defaulting to zero/deterministic.
2. Pre-generate piecewise-constant integer percentage factors at reset from the
   world seed and store them in `WorldState`.
3. Apply factors to active demand and generator capacity in the power tick and
   in power observations.
4. Include the schedules in the state hash only when non-empty, so deterministic
   and power-free hashes are unchanged.
5. Keep the prediction task contract; a new experiment will use a stochastic
   power config.
6. Do not expose future factors in observations.

## Alternatives considered

- **Runtime RNG with serialized state.** Rejected: more state and replay
  complexity.
- **Observation noise only.** Rejected: it does not change allocation or future
  outcomes.
- **Discrete generator outages.** Deferred: factor schedules are the MVP.
- **Tune the deterministic task instead.** Rejected: 0017 is a documented
  ceiling; variation is a new mechanic.

## Consequences

- Deterministic power runs and hashes are unchanged when jitter is zero.
- Stochastic power runs carry schedules in state and replay.
- The power view still has the same shape; its values become time-varying.
- The allocation control task may become harder and will need a separate
  experiment.
- The frozen benchmark remains untouched.
