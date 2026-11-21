# ADR 0006 — Python and NumPy first

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0004

## Context

The first milestone needs a correct, testable factory, not a high-performance
engine. The team's existing work is Python. A Rust/C++ core or a full ECS would
add build complexity before the contracts are stable.

## Decision

Use Python 3.12 with the standard library for the core. Use NumPy only where
arrays are genuinely useful. Keep Torch, Pygame, and data tooling optional.

Performance policy for M1:

- 10k ticks/s is the reference target on a recorded reference machine;
- 1k ticks/s is the supported-machine floor;
- no more than a 20% same-machine regression against a stored baseline;
- 100k-step generation should be practical on the development machine;
- replay should be at least as fast as generation.

Absolute throughput is recorded with hardware, not assumed across machines.
Optimize only measured hot paths. Consider Numba or a Rust extension later if
the floors are missed.

## Alternatives considered

- **Rust/C++ core with Python bindings.** Rejected for now: slower iteration and
  more build surface before the contracts are stable.
- **JAX/vectorized simulation.** Rejected for now: the factory is discrete and
  stateful; vectorizing it would complicate determinism.
- **An existing ECS.** Rejected for now: the factory is small and explicit; an
  ECS adds abstraction without a measured need.

## Consequences

- The core may need optimization at larger scales.
- The perf test is a first-class artifact.
- The architecture keeps the hot loop isolated so it can be replaced later.
