# ADR 0003 — Canonical state, derived observations

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0001, ADR 0004

## Context

A testbed must serve many methods and tasks. If observations are baked into the
simulation or stored per task, the same world is duplicated, versions drift, and
methods cannot be compared on the same episodes.

## Decision

The world emits **one canonical, factored state** and an event log. Observation
adapters, labels, rewards, and splits are pure derived views.

- The state contains entities, tiles, inventories, events, metrics, and RNG
  state.
- Observation adapters are versioned pure functions.
- Tasks are projections over episodes, not separate worlds.
- Ground truth lives in `info`/annotations, separate from agent-visible views.

## Alternatives considered

- **Per-task datasets.** Rejected: duplication, drift, and unfair comparisons.
- **Renderer output as the observation.** Rejected: forces vision and loses
  structure; pixels remain one optional adapter.
- **A universal observation schema.** Rejected: too rigid; adapters plus specs
  are more flexible.

## Consequences

- Observation and task contracts need versioning and tests.
- The same episode can serve an MLP, GNN, transformer, world model, and RL agent.
- More upfront design, but much less duplication later.
- Adapter cost must be measured and reported.
