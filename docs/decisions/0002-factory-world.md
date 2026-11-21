# ADR 0002 — Factory as the first world

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0001

## Context

The testbed needs a first world that supports many research axes at low
iteration cost. Candidates:

- drone/robot sim: continuous control, multi-modal sensors, expensive;
- tactics RPG: symbolic planning and memory, content-heavy;
- deckbuilder: cheap and combinatorial, narrow modalities;
- ops/station sim: time series and causal structure, UI-heavy;
- factory/automation: graphs, planning, optimization, causality, long horizons,
  cheap ticks, visual;
- swarm: multi-agent emergence, expensive and hard to evaluate.

## Decision

Use a **factory/automation world** as the first world.

The MVP is a 32×32 grid with ore, belts, furnaces, assemblers, and a depot. It
has a fixed tick order, integer state, procedural layouts, and known ground
truth. It deliberately excludes fluids, trains, full power networks, and
combat.

## Alternatives considered

- **Drone sim.** Best literal fit for multi-sensor view arrival, but 3D physics
  and rendering dominate the first year. Rejected for the first world.
- **Deckbuilder.** Fastest to build, but weak on spatial, graph, and continuous
  structure. A good second world if needed.
- **Ops/station sim.** Strong on time series and causal structure, but less fun
  and less legible as a first game. A good later expansion.
- **RPG.** Strong on symbolic planning and memory, but content-heavy and weaker
  on measurable throughput.

## Consequences

- The first world is cheap to simulate and supports prediction, control,
  planning, and causal tasks.
- Continuous control and raw perception are deferred; another world can cover
  them later.
- The factory's views are information channels, not necessarily sensors. This
  keeps multi-view research possible without a 3D sensor sim.
- The world must stay small and data-driven; content expansion is not the goal.
