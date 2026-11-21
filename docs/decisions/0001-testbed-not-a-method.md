# ADR 0001 — A general testbed, not a single-method proof

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** `devec`, `circlenn`

## Context

A controlled world is useful for testing modularity, composition, transfer,
world models, planning, efficiency, and causal questions. Public datasets are
static snapshots; they cannot test view arrival, retention under distribution
shift, or counterfactual structure.

A world built around one method would bias the tasks toward that method and make
negative results hard to trust.

## Decision

Build a **general testbed**: a deterministic world, canonical state, observation
and task adapters, reproducible data, and a method-agnostic benchmark harness.

The testbed's success criteria are defined in [`../testbed.md`](../testbed.md),
not by whether any single method wins.

## Alternatives considered

- **Build a method-specific world.** Rejected: it would bias the tasks and make
  negative results hard to interpret.
- **Publish a static dataset.** Rejected: it cannot test view arrival,
  counterfactuals, or retention under controlled shift.
- **Extend `circlenn`.** Rejected: its ring and world are a different research
  program; the observation and data layers need a different design.

## Consequences

- The project is larger than a single experiment, but more reusable.
- The benchmark core must stay method-agnostic and versioned.
- Success is measured by task coverage, reproducibility, and extensibility, not
  by a single method's score.
