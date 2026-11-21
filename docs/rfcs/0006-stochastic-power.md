# Mechanic RFC 0006 — Stochastic power variation

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-21
- **Related:** RFC 0004, ADR 0016

## Summary

Add seeded, pre-generated variation to power demand and generator capacity.
`PowerConfig` gains load jitter, capacity jitter, and a variation period. At
reset, the world generates piecewise-constant integer percentage factors for the
whole episode and stores them in canonical state. The power tick applies the
current factors to demand and capacity. Future factors are not exposed in
observations.

## Motivation

The deterministic power grid makes brownout prediction nearly mechanical: line
buffers and craft progress determine the future label. Experiments 0017 and
0018 confirmed this. Stochastic variation creates genuine uncertainty without
adding hidden tick RNG or changing the frozen benchmark.

## Rules

- New `PowerConfig` fields, all defaulting to deterministic behavior:
  - `load_jitter: int = 0` — percentage points, 0–100;
  - `capacity_jitter: int = 0` — percentage points, 0–100;
  - `variation_period: int = 20` — ticks per factor block.
- When either jitter is nonzero, generate schedules at reset from the world
  seed:
  - `load_factor` in `[100 - load_jitter, 100 + load_jitter]`;
  - `capacity_factor` in `[100 - capacity_jitter, 100 + capacity_jitter]`;
  - one factor pair per `variation_period` ticks, truncated to the episode
    length.
- Store `power_load_factors` and `power_capacity_factors` in `WorldState`.
- The power tick uses:
  - `scaled_demand = max(1, active_demand * load_factor // 100)` for active
    entities;
  - `scaled_capacity = source.capacity * capacity_factor // 100` per source.
- Observations use the scaled values. They do not expose future factors.
- If both jitters are zero, no schedule is generated and existing power state
  hashes are unchanged.
- Schedules are included in the state hash only when non-empty.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| power grid | factors scale demand/capacity | existing deterministic runs unchanged |
| faults | faulted machines demand 0; factors apply to the rest | interaction tests needed |
| allocation control | priority order unchanged; budget varies | control may need retraining |
| view-arrival | power view varies; base views do not | new experiment required |
| replay | schedule regenerated from seed and config | hash must match |
| frozen benchmark | power disabled by default | no change |

## Observation impact

- `power` and `power_grid` shapes are unchanged; values use scaled demand and
  capacity.
- Current factors can be inferred from the observations, but future factors are
  not visible.
- No new observation view in this RFC.

## Data impact

- Deterministic power data and hashes are unchanged when jitter is zero.
- Stochastic power data is a new opt-in regime.
- The power prediction task keeps its contract; only the power config changes.

## Determinism

- Schedules are generated from the explicit world seed with a dedicated
  generator (`seed * 1009 + 17`).
- No runtime RNG, no global RNG.
- The schedule is cloned with the state and replayed from seed + config.

## Tests

- Jitter config validation.
- Schedule length, range, determinism, and seed sensitivity.
- Hash changes when schedules are non-empty.
- Scaled demand/capacity in allocation.
- Observations use scaled values.
- Replay with stochastic power.
- Power-free and deterministic power regressions.
- A pilot confirms stochastic data has a non-degenerate label.

## Performance

Two integer lists of episode length; O(1) per tick. Negligible.

## Alternatives

- **Runtime RNG with serialized state.** Rejected for now: more state and replay
  complexity; a pre-generated schedule is easier to inspect and hash.
- **Observation noise only.** Rejected: it does not change the underlying
  allocation or make the future uncertain.
- **Stochastic faults.** Separate mechanic; keep power variation independent.
- **Generator outages/fuel.** Deferred: factor schedules are the MVP.

## Open questions

- Should demand and capacity factors be correlated?
- Should generator outages be discrete events rather than smooth factors?
- Should observations expose a forecast or only current conditions?
- Should the control task see the schedule or learn it?
