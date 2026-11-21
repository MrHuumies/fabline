# Mechanic RFC 0003 — Sensor diversity

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-21
- **Related:** RFC 0001, ADR 0011, ADR 0013

## Summary

Give the three fault diagnostic channels separate temporal dynamics:
temperature becomes a slow follower with thermal inertia, vibration becomes a
decaying impulse at work start, and acoustic becomes a decaying impulse at
blockage and fault onset. The channels stop being linear restatements of the
same wear/activity/fault latents at the same tick.

## Motivation

An earlier sensor experiment added thermal, vibration, and acoustic views to a frozen
predictor and failed the gain gate. The cause was the sensor model: every channel was computed from the same latents with fixed
coefficients at the current tick, so thermal already spanned the others.

A view-arrival test needs views that carry different information. Distinct
temporal filters are the smallest change that makes the channels physically
different without adding a new resource system.

## Rules

The sensor values are canonical state, because they affect future observations.

- Add three integer fields to `Entity`, each in `[0, 100]`:
  `temperature`, `vibration`, `acoustic`.
- Update them once per tick, at the start of the tick, only when
  `FaultConfig.enabled`:
  - **temperature:** first-order lag toward
    `min(100, 40·wear_fraction + 20·crafting + 40·faulted)` with
    `temperature = (15·temperature + target) // 16`.
  - **vibration:** `vibration = 3·vibration // 4`, then impulses:
    `+70` on `craft_started`, `+50` on miner `item_spawned`.
  - **acoustic:** `acoustic = 7·acoustic // 8`, then impulses:
    `+40` on `item_blocked`, `+80` on `fault_started`.
- `crafting` is 1 while `craft_progress > 0`.
- Impulses are capped at 100.
- Sensor fields are zero and are not updated when faults are disabled.
- Canonical entity hashes include the sensor fields only when any of them is
  nonzero, using the same conditional block as wear/fault. Fault-free
  `factory-v0.1` hashes stay byte-identical.
- `SensorsObservation` and `DiagnosticsObservation` read the state fields and
  divide by 100. Their versions become `0.2.0`.

Tick order stays explicit:

```text
tick += 1
telemetry        # decay and thermal approach
machines         # craft starts/completions, wear, faults
logistics        # movement, blockage
finish_tick
```

Impulses raised during machines/logistics are visible in the observation at
the end of the same tick. Decay happens on the next tick.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wear/fault | temperature rises with wear; acoustic spikes on fault | sensors now depend on event timing, not just totals |
| crafting | vibration is a work-start transient | furnace/assembler cadence changes the channel |
| logistics | acoustic counts blockage | congestion becomes visible in a sensor |
| repair | repair clears wear; thermal decays slowly | a repaired machine stays warm for a while |
| grid actions | no change | — |
| frozen benchmark | sensor fields stay zero without faults | hash regression must be tested |

## Observation impact

- `sensors` shape stays `(H, W, 5)`; channels are wear, temperature, vibration,
  acoustic, faulted.
- `diagnostics` shape stays `(13,)`; feature names are unchanged.
- Values remain normalized to `[0, 1]`.
- Version bump to `0.2.0` is required because the semantics changed.

## Data impact

- Fault-free data and hashes are unchanged.
- Fault episode data changes. The 0008 fault-prediction results and the
  `fault-debug-v0.1` card describe the static `0.1.0` sensor model; they become
  historical and are annotated, not rewritten.
- The fault-recovery task uses diagnostics as an observation, but its policies
  depend on the info dict (fault count, wear), not the sensor values, so its
  baselines should be stable. Rerun and confirm.

## Determinism

- Integer state, integer updates, no RNG.
- Update order is fixed in `FactoryWorld.tick`.
- Sensor state is cloned with the entity and is part of the state hash.

## Tests

- Fault-free worlds keep sensor fields at zero and the golden hash unchanged.
- Sensor fields change the state hash when nonzero.
- Temperature rises toward the target and decays after repair.
- Vibration spikes on craft start and decays without work.
- Acoustic spikes on blockage and fault onset and decays.
- Sensors and diagnostics remain in `[0, 1]` and reflect the state fields.
- Replay round-trip with faults enabled.
- Fault benchmark, fault recovery, and frozen benchmark regression tests.

## Performance

Three integer updates per entity per tick. Expected impact is small; the
headless floor is 1k ticks/s and the current rate is far above it.

## Alternatives

- **Observation-only exponential smoothing.** Rejected: it hides state in the
  adapter and breaks replay/observation equivalence.
- **Stateless nonlinear mixtures.** Rejected: still the same latents at the same
  tick; diversity requires different temporal filters.
- **Fault types with distinct signatures.** Deferred: a larger mechanic; this
  RFC only separates the channels.
- **Add sensor noise in the world.** Rejected for now: noise belongs to dataset
  generation so the world stays deterministic and the noise level is a data
  choice.
- **Rerun the earlier experiment with tuned noise.** Rejected: violates its
  pre-registration. This is a new mechanic and needs a new experiment.

## Open questions

- Should temperature have a per-machine heat capacity?
- Should vibration depend on machine type?
- Should acoustic distinguish fault types once faults have types?
- Should repair leave residual heat that affects the next fault?
