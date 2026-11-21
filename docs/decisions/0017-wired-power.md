# ADR 0017 — Opt-in wired power topology

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** RFC 0007, ADR 0014, experiment 0032

## Context

The radius power grid answers spatial capacity questions but not relational
ones. Every consumer inside a radius is equivalent; there is no path, cut,
multi-hop dependency, or failure propagation. The P1 coverage item is wired
power topology and cascades.

The frozen `factory-v0.1` benchmark is power-free. The new mechanic must be
opt-in and must not change existing power behavior, hashes, views, or tasks.

## Decision

1. Add `PowerConfig.topology`, default `"radius"`. Radius mode is unchanged.
2. Add `"wired"` mode with a pre-placed wire-edge graph and one generator in
   phase 1A. Wires are infrastructure, not entities; they do not occupy the
   entity grid, and they are not buildable.
3. Build a seeded randomized spanning tree over a candidate cell band and add
   `wire_redundancy` loop edges. Model connectivity as reachability from the
   generator over non-failed edges. A bridge fault disconnects a downstream
   component; a loop-edge fault reroutes power. Capacity allocation still
   applies to connected consumers.
4. Add deterministic single-wire faults through config, plus a seeded per-sample
   fault selection for dataset generation. Wire repair is deferred to phase 1B.
5. Add `power_topology` and `power_wires` observations. Existing power views and
   the frozen vector/grid/entity views are unchanged.
6. Add the `factory.power.cascade.v1` debug prediction task: per-entity
   disconnection after a marked wire fault. Baselines are flattened/aggregate,
   `graph_mp`, and an end-to-end GNN.
7. Keep wired mode and the cascade task outside `factory-v0.1`.

## Alternatives considered

- **Wire entities with occupancy and build actions.** Rejected for phase 1A:
  it changes the entity/action contracts and adds control before the prediction
  question is answered.
- **Wire capacity and overload cascades.** Deferred: pure connectivity already
  produces graph-dependent labels.
- **Repair control first.** Rejected: a control task is only meaningful once the
  cascade label is learnable and not saturated by a trivial feature.
- **Radius mode with a connectivity mask.** Rejected: it would not add a wire
  graph or a cut.
- **A single bus with spurs.** Rejected: the label becomes a coordinate
  threshold and does not require graph reasoning.

## Consequences

- Radius-mode hashes, views, tasks, and the frozen benchmark are unchanged.
- Wired episodes carry wire state and wire-fault events in canonical state and
  replays.
- The cascade task tests whether graph structure improves prediction over
  aggregate and flattened views.
- Wire placement, connectivity, and fault selection need dedicated tests.
- Multi-generator redundancy, wire capacity, and repair control remain
  follow-ups.

## Follow-ups

- [ ] Implement wire state, placement, connectivity, and fault events.
- [ ] Add `power_topology` and `power_wires` views.
- [ ] Generate the cascade dataset and run experiment 0032.
- [ ] Add a task card and dataset card.
- [ ] Revisit repair control only if the prediction task is not saturated.
- [ ] Keep `factory-v0.1` frozen and verify its hash.
