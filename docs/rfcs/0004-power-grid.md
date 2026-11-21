# Mechanic RFC 0004 — Power grid and brownouts

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-21
- **Related:** ADR 0014, ADR 0011, ADR 0013

## Summary

Add an opt-in power grid. Pre-placed generators supply capacity to machines
within a Manhattan radius. Each machine has a power demand; when demand exceeds
the capacity that reaches it, it browns out and stops working until power is
restored. Add aggregate and spatial power observations, a brownout-prediction
debug task, and a follow-up allocation-control environment.

Phase 1 (this RFC's implementation) covers the grid, brownouts, observations,
and prediction. Phase 2 covers allocation control and is implemented separately.

## Motivation

The factory currently has one resource flow: items. Every machine always works
if it has inputs and output space. Power adds a second, shared resource with
spatial coupling and a new failure mode. It also creates a natural
resource-allocation control problem: under a tight budget, which machines should
get power?

The mechanic must be opt-in so the frozen `factory-v0.1` benchmark, observations,
and hashes stay unchanged.

## Rules

### Generators

- Generators are infrastructure, not buildable entities in the MVP.
- They are placed deterministically at reset when `PowerConfig.enabled` is true.
- A generator has an id, position, and per-tick capacity.
- Generators are canonical state. They are excluded from the hash when the list
  is empty, so power-free hashes are unchanged.
- Making generators buildable is deferred: it would add an entity type and
  change the frozen action/observation contracts.

### Distribution

- Each generator covers entities within a Manhattan radius.
- Process generators in id order; each has `capacity` to spend this tick.
- For each covered consumer in entity-id order, if its demand fits in the
  remaining capacity, it is powered and the capacity is reduced.
- A consumer covered by several generators uses the first that powers it;
  remaining capacity stays with the later generator.
- This is a simple shared grid, not a flow solver.

### Demand and brownouts

Demand is activity-gated so the grid changes over time:

| Entity | Demand |
|---|---|
| miner | 2 continuously |
| belt | 1 while carrying an item (output buffer non-empty) |
| furnace | 3 while crafting (`craft_progress > 0`) |
| assembler | 4 while crafting (`craft_progress > 0`) |
| depot | 0 |

Idle machines draw 0 and are considered ready to start. When a machine starts
a craft, its demand appears on the next power tick; if capacity is insufficient,
the craft stalls until power returns. This is what makes brownouts intermittent
and the prediction task non-degenerate.

- Faulted entities demand 0 and are offline; a fault can free power for others.
- An entity with positive demand that is not powered is browned out:
  - miners do not produce ore;
  - furnaces/assemblers do not start or advance crafts;
  - belts do not move items (they may still receive and hold items);
  - `brownout_ticks` increments.
- Emit `power_brownout` on the transition powered → unpowered and
  `power_restored` on the reverse.
- A depot has zero demand and is always considered powered.

### Tick order

```text
tick += 1
telemetry        # fault sensor decay/warm
power            # allocate capacity, set powered/brownout
machines         # skip unpowered entities
logistics        # skip unpowered senders
finish_tick
```

Power is computed before work so the same tick observes the consequence.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| crafting | unpowered machines stop | production can collapse if allocation is poor |
| belts | unpowered belts stop moving | backups can cascade upstream |
| faults | faulted machines demand 0 | faults free power; interactions must be tested |
| repair | repaired machines re-enter demand | repair can trigger a new brownout |
| grid actions | no new action in phase 1 | frozen action contract unchanged |
| observations | new `power` / `power_grid` views | frozen views unchanged |
| benchmark | power disabled by default | hash regression must be tested |

## Observation impact

### `power.v1`

12 aggregate features:

```text
tick_norm, capacity_norm, demand_norm, load_ratio,
powered_ratio, brownout_count_norm, mean_brownout_ticks_norm,
miner_powered_ratio, belt_powered_ratio, furnace_powered_ratio,
assembler_powered_ratio, headroom_norm
```

### `power_grid.v1`

`(H, W, 3)` field: normalized generator coverage, normalized demand, powered
flag. It is a spatial view for grid/CNN models.

The standard vector/grid/entity views do not change.

## Task impact

- New label `future_brownout`: any new `power_brownout` event in the next
  `horizon` ticks.
- New task `factory.power.brownout.v1`, debug task:
  - observation `power` (and optionally `power_grid`);
  - label as above;
  - fixed gear line, power enabled, tight or default budget.
- New `power-benchmark` CLI comparing the standard vector view against `power`.

## Control (phase 2)

A separate `PowerAllocationEnv` will choose a power priority each decision
interval:

- `default` — entity-id allocation;
- `favor_furnace` — furnaces first;
- `favor_assembler` — assemblers first;
- `favor_miner` — miners first.

Reward is score delta. The world exposes a `power_priority` field so the env can
set it. This is a follow-up RFC/implementation and does not change the phase-1
task or benchmark.

## Determinism

- Generator placement is deterministic from the seed and config.
- Allocation order is fixed: generators by id, consumers by id.
- Integer capacities and demands; no RNG in the power tick.
- Powered/brownout state is canonical and hashed when nonzero.

## Tests

- Power-free worlds keep empty generator lists and unchanged hashes.
- Generators are placed deterministically and do not overlap entities.
- Allocation powers covered entities in id order and respects capacity.
- Radius excludes distant entities.
- Brownouts stop miner/craft/belt work and emit transition events.
- Faulted entities free capacity.
- `power` and `power_grid` shapes, ranges, and feature values.
- Replay round-trip with power enabled.
- Power-free golden trace and frozen benchmark regression.
- Power benchmark end-to-end.

## Performance

Power is O(generators × consumers) per tick. With two generators and tens of
entities, it is negligible. The headless floor remains 1k ticks/s.

## Alternatives

- **Buildable generators now.** Rejected for phase 1: adding an entity type
  changes the frozen entity/action contracts.
- **Global power budget with no locality.** Rejected: it removes the spatial
  coupling and the reason for a grid.
- **Wire entities and connectivity.** Deferred: a larger action/observation
  change; radius coverage is the MVP.
- **Fuel and stored energy.** Deferred: per-tick capacity is enough for the
  first mechanic; fuel adds another resource loop.
- **Power in the existing macro control task.** Rejected: it would change the
  control task's observation/action contract.

## Open questions

- Should generators be buildable or upgradable?
- Should capacity degrade with wear/faults?
- Should power be stored in batteries?
- Should allocation be a flow problem over wires?
- Should the control task choose per-entity priorities rather than type order?
