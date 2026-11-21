# Mechanic RFC 0007 — Wired power topology and cascades

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-21
- **Related:** ADR 0017, RFC 0004, ADR 0014

## Summary

Add an opt-in wired power topology. Generators supply consumers through
pre-placed wire segments instead of a Manhattan radius. A failed wire removes a
graph cut and disconnects everything downstream, producing a deterministic
cascade. Add wire-aware observations and a cascade-prediction task that asks
which entities lose connectivity when a marked wire fails.

Phase 1A covers wired topology, deterministic wire faults, observations, and
cascade prediction. Phase 1B (topology repair control) is deferred to a
follow-up RFC so the prediction question is answered first.

## Motivation

The radius grid is a spatial but not a relational power model. Every consumer
within range is equivalent; there is no path, no cut, and no multi-hop
dependency. The coverage map identifies wired power as the P1 mechanic for
graph constraints, long-range dependence, and failure propagation.

The current world cannot answer:

- does a model use wire connectivity, or only aggregate capacity and demand?
- can a graph model predict which entities are downstream of a failed segment?
- does message passing beat flattened features when the label is a graph cut?

This is a prediction question first. Repair control is only meaningful once the
cascade label is learnable and not saturated by a trivial feature.

## Rules

### Topology selection

- `PowerConfig.topology` is `"radius"` (default) or `"wired"`.
- Radius mode is unchanged: same placement, allocation, views, hashes, and
  tasks.
- Wired mode is opt-in and is not part of frozen `factory-v0.1`.

### Generators and wires

- Phase 1A uses one pre-placed generator. Multi-generator wired grids are a
  follow-up.
- Wires are infrastructure cells in a parallel layer, not entities:
  - they do not occupy the entity occupancy map;
  - they do not block belts, machines, or the depot;
  - they are not buildable in phase 1A.
- A wire is an orthogonal edge between two adjacent cells:
  `PowerWire(id, ax, ay, bx, by, failed=False)`.
- Wires are canonical state and hashed only when the list is non-empty, so
  radius/power-free hashes are unchanged.
- Wire placement is deterministic from the seed and the generated layout:
  - build a candidate cell band around the production line that avoids rocks
    and entity cells;
  - choose terminal cells adjacent to the generator and each consumer;
  - build a seeded randomized spanning tree over the candidate band that
    connects all terminals (multi-source randomized Prim);
  - add `wire_redundancy` extra edges (default 2) to create loops;
  - each tree/extra edge becomes a wire.
- The result is a connected graph with branches and loops, not a single bus.
  A loop edge is not a bridge: a fault on it reroutes power. A tree edge is a
  bridge: a fault disconnects its downstream component.
- If the candidate band cannot connect all terminals, fail generation with a
  clear error instead of silently falling back to radius mode.

### Connectivity

- Wire edges connect their two endpoint cells; endpoints are orthogonally
  adjacent by construction.
- A failed wire edge is removed from the wire graph.
- A generator supplies the connected component containing its terminal cell.
- A consumer is connected when at least one of its terminal cells is reachable
  from the generator through non-failed wire edges.
- Connectivity is computed before capacity allocation. Capacity then allocates
  among connected consumers by the existing priority and entity-id order.
- Bridge status is derived from the graph, not stored as a feature; it is part
  of what the model must infer.
- Disconnected consumers have demand but are treated as unpowered; they
  increment `brownout_ticks` and emit the usual brownout events.
- Wires have no capacity limit in phase 1A. Wire capacity and overload trips are
  a follow-up; the first question is pure connectivity.

### Faults

- `wire_fault_tick` (default `0`, disabled) and `wire_fault_id` select a single
  deterministic wire failure at a tick.
- A dataset generator may instead select a fault wire per sample from a seeded
  RNG; the selected wire id is part of the sample metadata, not hidden state.
- On failure, emit `power_wire_fault` with the wire id and endpoints.
- A fault on a loop edge leaves every consumer connected; a fault on a bridge
  disconnects exactly the component on the far side from the generator.
- Phase 1A does not repair wires. The wire remains failed for the episode.
- Wire faults are independent of machine faults; a machine fault does not
  damage wires.

### Tick order

```text
tick += 1
telemetry
power:
  - apply scheduled wire fault
  - build the wire graph
  - mark reachable wires from the generator
  - mark connected consumers
  - allocate capacity among connected consumers
machines
logistics
finish_tick
```

Power is computed before work, as in the radius grid.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| radius power | mutually exclusive topology mode | config validation must reject mixed state |
| capacity/brownouts | capacity still limits connected consumers | a connected but under-capacity entity still browns out |
| machine faults | faulted entities demand 0 | a machine fault can free capacity but does not affect wires |
| repair | machine repair re-enters demand | wire repair is not in phase 1A |
| stochastic power | load/capacity factors apply in both modes | schedules are independent of topology |
| observations | new wire-aware views; existing views unchanged | shape/version drift |
| frozen benchmark | wired mode disabled by default | hash regression must be tested |
| control | no new action in phase 1A | action contract unchanged |

## Observation impact

Existing `power.v1` and `power_grid.v1` are unchanged.

New `power_topology.v1`, 8 aggregate features:

```text
wire_count_norm, failed_wire_ratio, connected_ratio,
disconnected_ratio, component_count_norm, max_component_ratio,
redundancy_ratio, fault_marker
```

New `power_wires.v1`, `(H, W, 4)` spatial view:

```text
horizontal_wire, vertical_wire, failed_wire, connected_wire
```

Consumers are marked through their terminal adjacency, not by painting over
their entity cell.

The standard vector/grid/entity views are unchanged.

For the cascade task, the entity graph view gains a `wire_adjacency` sidecar:
a boolean `(M, M)` matrix over padded entity nodes where an edge means the two
entities are adjacent to the same connected wire component. A separate wire-node
graph encoding is used by graph baselines; it is not part of the frozen entity
view.

## Action impact

None in phase 1A. Repair control in phase 1B will add wire repair as a separate
environment action; it will not change the frozen grid action.

## Data impact

- New label `entity_disconnected`: for a sampled pre-fault state and a marked
  fault wire, 1 for each consumer that is connected before the fault and
  disconnected after the fault is applied.
- Labels are deterministic reachability, not a stochastic outcome.
- New task `factory.power.cascade.v1`, split by generation seed.
- New dataset card when the generator is implemented.
- Frozen `factory-v0.1` has no wires and no new labels.

## Determinism

- Wire placement is a pure function of the generated layout, seed, and config.
- Connectivity BFS visits wire cells in sorted `(y, x)` order.
- Capacity allocation keeps generator/consumer id order.
- Fault selection is explicit in config or seeded per sample.
- State hash includes wire positions and failed flags only when wires exist.
- Replays validate the full wire state and fault events.

## Tests

- Wire-free and radius-mode hashes are unchanged.
- Wired generation is deterministic and wires do not overlap rocks/entities.
- Connectivity reaches consumers through a bus and stops at a failed wire.
- A wire fault disconnects exactly the downstream component; upstream consumers
  stay powered.
- Capacity allocation still browns out connected consumers when demand exceeds
  supply.
- `power_topology` and `power_wires` shapes, ranges, and feature values.
- Fault events and replay round-trip.
- Cascade labels match a brute-force reachability oracle.
- Frozen benchmark regression and perf floor.

## Performance

Connectivity is O(wires + consumers) per tick with a small wire count (tens).
The supported 1k ticks/s floor must hold; the 20% same-machine regression gate
applies to the power tick.

## Alternatives

- **Wire entities with occupancy and build actions.** Rejected for phase 1A:
  it changes the entity/action contracts and makes placement part of control
  before the prediction question is answered.
- **A single bus with spurs.** Rejected: the disconnected set becomes a
  coordinate threshold, and a vector baseline with fault and entity positions
  can solve it without the graph.
- **Wire capacity and overload trips.** Deferred: pure connectivity already
  produces cascades and a clean graph label.
- **Random wire damage every tick.** Rejected for phase 1A: a deterministic
  single fault keeps labels and replays auditable.
- **Two-generator redundancy.** Deferred: it would make single-wire failures
  less informative and add a placement design question.

## Open questions

- Should the bus row be fixed or chosen per seed? Phase 1A chooses per layout
  with a deterministic rule.
- Should wire faults also stop belts physically? Phase 1A uses the existing
  power rule: unpowered belts do not move.
- Is entity-level outage too imbalanced for AUROC? Loop faults cause no
  disconnection, so the generator samples bridge and loop faults explicitly and
  reports positive rates; AUPRC is the primary metric if positives are sparse.
- Does the randomized spanning tree produce enough distinct cuts? The dataset
  generator reports the bridge count and downstream-size distribution before
  the formal run.

## Decision

Accepted. See ADR 0017. Implementation and the cascade experiment follow.
