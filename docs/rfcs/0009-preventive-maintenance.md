# Mechanic RFC 0009 — Preventive machine maintenance

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-22
- **Related:** ADR 0019, RFC 0008, ADR 0018, ADR 0011

## Summary

Extend the normal machine-wear fault mechanic with preventive maintenance. A
worn but not yet faulted machine can be taken offline for a short maintenance
window; wear resets at completion. This offers the same early-action trade as
wire prevention: spend a short planned downtime before the fault threshold
instead of a longer auto-repair after a fault.

## Motivation

Faults currently only support reactive repair or waiting for the 40–60 tick
auto-repair. Wear is visible and deterministic, but it has no action channel.
The wire maintenance experiment (0035) showed that an early, timed action is
valuable; this RFC applies the pattern to the normal fault mechanic.

## Rules

- `FaultConfig.maintenance_ticks` (default 10) is the planned downtime.
- `FactoryWorld.maintain_entity(entity)`:
  - requires a non-faulted entity with no active maintenance;
  - sets `maintenance_remaining = maintenance_ticks`;
  - emits `maintenance_started`.
- While `maintenance_remaining > 0`, the entity skips machine work.
- At the end of each tick, `maintenance_remaining` decreases. When it reaches
  zero, wear resets to 0 and `maintenance_completed` is emitted.
- A faulted entity still uses the existing policy:
  - explicit repair clears the fault instantly;
  - without repair, auto-repair takes `repair_ticks`.
- Maintenance does not clear fault state or craft progress; it only resets wear
  and blocks work during the window.
- The mechanic is opt-in through `FaultConfig.enabled`; fault-free and frozen
  hashes are unchanged.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wear/faults | maintenance resets wear before threshold | timing must be before the fault |
| auto-repair | fault downtime is longer than maintenance | prevention should win if timed well |
| explicit repair | still available in fault-recovery envs | not used by the preventive task |
| power | a maintained machine is offline | demand/craft interaction |
| sensors | wear/sensors reset at completion | diagnostics should reflect it |
| observations | diagnostics unchanged; env adds maintenance features | shape/version impact |
| frozen benchmark | faults disabled by default | hash regression |

## Observation impact

`DiagnosticsObservation` is unchanged. The preventive env appends two features:

```text
maintenance_count_norm, max_maintenance_remaining_norm
```

## Action impact

The preventive-fault env has two actions: noop and maintain the most worn
eligible machine. The global grid action contract is unchanged.

## Data impact

- New task `factory.fault.preventive.v1` (debug/P1).
- New metrics: maintenance count, fault events, production score.
- No dataset artifact.
- Frozen `factory-v0.1` has no faults and no maintenance.

## Determinism

- Maintenance target selection is by wear, then entity id.
- Maintenance countdown is in `_finish_tick`.
- `maintenance_remaining` is canonical only when nonzero; frozen hashes are
  unchanged.
- Replays validate maintenance events and remaining time.

## Tests

- Maintenance sets the timer, skips work, and resets wear at completion.
- Faulted/active-maintenance entities are rejected.
- Observation shape and action mask.
- Noop vs threshold maintenance scores.
- Maintenance events and replay round-trip.
- Frozen benchmark hash regression.

## Performance

One timer per entity; O(entities) per tick. The 1k ticks/s floor holds.

## Alternatives

- **Maintenance takes zero time.** Rejected: no scheduling trade.
- **Maintenance while the machine keeps working.** Rejected: harder to audit
  and no clear downtime cost.
- **Repair time only.** Rejected: 0034/0035 showed that early action needs a
  preventive state.

## Decision

Accepted. See ADR 0019; experiment 0037 tests preventive vs reactive/noop.
