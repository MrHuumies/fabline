# ADR 0004 — Headless core, renderer separate

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0003, `circlenn` precedent

## Context

Coupling simulation to rendering makes runs slow, non-reproducible, hard to
parallelize, and impossible to test in CI. `circlenn` already established the
right pattern: the renderer reads state and never advances time.

## Decision

The core simulation is headless, deterministic, and fixed-timestep. The renderer
is a separate optional client that consumes state or replays. It never mutates
the world.

The core must import and run with only the standard library (and optional NumPy
for arrays). Pygame, Torch, and plotting live outside the core.

## Alternatives considered

- **Use a game engine for the simulation.** Rejected for the first world: engine
  physics and update order are hard to make deterministic and testable, and the
  factory does not need them.
- **Render inside the loop for convenience.** Rejected: speed, CI, and
  reproducibility costs.
- **A web-only simulator.** Rejected: harder to test and parallelize; a viewer
  can be added later.

## Consequences

- The factory needs its own small, explicit simulation. That is acceptable
  because the mechanics are simple.
- Headless generation and tests are fast.
- The viewer can change without touching benchmark behavior.
- Pixel observations are generated offline from state, not during training.
