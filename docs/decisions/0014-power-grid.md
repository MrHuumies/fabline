# ADR 0014 — Opt-in power grid

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** RFC 0004, ADR 0011, ADR 0013

## Context

The factory has one resource flow and no shared constraint. Adding power gives
the world a second resource, spatial coupling, a new failure mode (brownout),
and a resource-allocation control problem.

The frozen `factory-v0.1` benchmark uses the existing vector/grid/entity
observations and action-free data. Adding power must not change those shapes or
hashes.

## Decision

1. Add `PowerConfig`, disabled by default and separate from `FactoryConfig`.
2. Model generators as canonical infrastructure state, not entities, in phase 1.
   This avoids changing the frozen entity type, action mask, and observation
   shapes.
3. Distribute power by Manhattan radius with deterministic generator-id and
   consumer-id allocation.
4. Add per-entity `powered` and `brownout_ticks` state; demand is
   activity-gated, unpowered machines skip work, and transitions emit events.
5. Add `power` and `power_grid` observations and a
   `factory.power.brownout.v1` debug prediction task.
6. Defer buildable generators, fuel, batteries, wires, and allocation control to
   follow-up work. Phase 2 is a separate `PowerAllocationEnv`.
7. Include the power config in replay and manifest metadata when enabled.

## Alternatives considered

- **Add a generator entity type.** Rejected for phase 1: it changes the entity
  and action contracts used by the frozen benchmark.
- **Global budget without locality.** Rejected: it loses the grid and the
  spatial representation question.
- **Wire connectivity.** Deferred: a larger mechanic with new entities and
  actions.
- **Integrate power into the existing control task.** Rejected: it changes the
  control observation/action contract.

## Consequences

- Power-free state hashes and observations are unchanged.
- Power episodes carry generator state, powered flags, and brownout events.
- The frozen benchmark remains action-free and power-free.
- Generators are pre-placed infrastructure in phase 1; a follow-up can make
  them buildable.
- The power task is a debug task, not part of `factory-v0.1`.
