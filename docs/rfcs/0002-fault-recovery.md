# Mechanic RFC 0002 — Repair action and fault recovery

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-21
- **Related:** RFC 0001, ADR 0011, ADR 0012

## Summary

Add an explicit `repair` op to the grid action contract and a two-action
fault-recovery control environment. A faulted machine can be repaired
immediately for a small reward penalty instead of waiting for auto-repair.

## Motivation

RFC 0001 introduced wear/fault/auto-repair but made faults passive. The control
half of the fault story is missing: when should an agent spend a repair action
to recover production? The fault mechanic should support both observation and
intervention.

## Rules

- New grid action: `repair(x, y)`.
- Legal only when:
  - the tile contains a non-depot entity;
  - the entity is faulted.
- Applying repair:
  - clears `faulted`, `repair_progress`, and `wear`;
  - emits `fault_repaired`.
- The generic action has no score cost. Environments/tasks may add one.
- The two-action recovery environment:
  - `noop` and `repair`;
  - repair chooses the first faulted entity in stable ID order;
  - reward = score delta − `repair_cost` when a repair happens;
  - episode length 500 ticks; decision interval 10;
  - fixed gear line with faults enabled.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wear/fault | repair clears the fault and wear | early repair avoids downtime |
| crafting | repaired machine resumes next tick | repair timing matters |
| auto-repair | repair action competes with waiting | if cost is low, repair-now dominates |
| grid actions | action space gains op 4 | mask and index version bump |
| frozen benchmark | action-free data unaffected | no replay hash change |

## Observation impact

The recovery environment uses the `diagnostics` view (13 features). No change to
the standard vector/grid/entity views.

## Action impact

`grid_build` action space becomes `(5, 5, H, W, 4)`:
op 0 noop, 1 build, 2 remove, 3 rotate, 4 repair. The action version becomes
`grid-build-0.2.0` for consumers that persist action specs.

## Data impact

- Fault-free state hashes unchanged.
- Fault replays already carry the fault config; repair actions are logged as
  actions and can be replayed.
- The recovery environment is online; demos can be recorded with the same demo
  format if needed.

## Determinism

- Repair is deterministic and instant.
- The recovery environment's policy RNG is explicit.
- No new state fields.

## Tests

- Repair is legal only on faulted, non-depot entities.
- Repair clears fault/wear and emits `fault_repaired`.
- Action mask includes repair only for faulted entities.
- Action index round-trip includes repair.
- Recovery environment mask, step, reward, and repair cost.
- Repair-now beats noop; tabular Q learns the two-action task.
- Frozen benchmark hash regression.

## Performance

Repair is O(1). The recovery environment adds one environment step per decision;
no impact on the factory tick target.

## Alternatives

- Add repair to the macro control task: rejected; it would change the existing
  control observation/action version and benchmark.
- Make repair costly in the world: rejected; cost belongs to the task/reward.
- Auto-repair only: rejected; the control half is the point.

## Open questions

- Should repair take multiple ticks or consume a resource?
- Should the agent choose which faulted entity to repair?
- Should repair be available in the playable client?
