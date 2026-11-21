# ADR 0013 — Dynamic diagnostic sensors

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** RFC 0003, ADR 0011, experiment 0010

## Context

The fault mechanic's diagnostic channels were stateless functions of wear,
activity, and fault state at the current tick. Experiment 0010 showed that
thermal, vibration, and acoustic were therefore redundant: adding the latter
two to a base that already saw thermal cleared no gain gate.

The world needs channels that measure different processes over different time
windows if view-arrival experiments are to be meaningful. This is a mechanic
change, not a model change.

## Decision

1. Store `temperature`, `vibration`, and `acoustic` as integer entity state in
   `[0, 100]`.
2. Update them once per tick, only when faults are enabled:
   - thermal first-order lag;
   - vibration impulse at craft start / miner output;
   - acoustic impulse at blockage and fault onset.
3. Include the fields in the canonical hash only when nonzero, preserving
   fault-free `factory-v0.1` hashes.
4. Bump `SensorsObservation` and `DiagnosticsObservation` to `0.2.0`.
5. Treat 0008 fault-prediction numbers as `0.1.0` results; do not rewrite the
   historical experiment. Rerun the fault recovery baselines to confirm they
   are stable.
6. Pre-register a new view-arrival experiment (0011) before running it. Do not
   rerun 0010 with tuned channels.

## Alternatives considered

- **Adapter-side smoothing.** Rejected: hidden state outside the canonical
  state; it would not survive cloning or replay consistently.
- **Keep static channels and accept redundancy.** Rejected: the negative
  result would be a property of the observation model, not the world.
- **Add fault types first.** Deferred: more scope than needed to separate the
  channels.
- **Tune noise or coefficients until 0010 passes.** Rejected: violates the
  pre-registration and the "do not tune the world to make a method win" rule.

## Consequences

- Fault episodes now carry sensor state; state hashes for fault runs change.
- Fault-free data, the frozen benchmark, and fault-free replays are unchanged.
- The existing fault-prediction results are historical `0.1.0` numbers.
- A new pre-registered experiment is required to test gain. The mechanic is
  motivated by physical distinctness, not by a promised win.
- The dynamic parameters are fixed before the experiment and must not be tuned
  against its results.
