# ADR 0012 — Repair action and fault recovery

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0011, RFC 0002

## Context

Faults were observation-only with auto-repair. The control half of the mechanic
needs an intervention: spending an action to recover production before the
auto-repair timer expires.

The frozen `factory-v0.1` benchmark is action-free, so adding a grid action does
not change its data or state hashes. The existing macro control task must stay
unchanged to keep its observation/action contract.

## Decision

1. Add `repair(x, y)` as op 4 in the grid action contract.
2. Repair is legal only on a faulted non-depot entity; it clears fault, repair
   progress, and wear.
3. Bump the grid action adapter version to `grid-build-0.2.0`.
4. Add a separate two-action `FaultRecoveryEnv` using the diagnostics view,
   `noop` vs `repair`, and a configurable repair cost.
5. Keep the existing macro control task and playable client unchanged.
6. Add a `fault-recovery` CLI benchmark for noop, repair-now, random, and
   tabular Q policies.

## Alternatives considered

- **Extend the macro control task with repair.** Rejected: changes the existing
  observation/action contract and demo format.
- **Repair cost in the world.** Rejected: cost is task-specific; the generic
  action should only change state.
- **Multi-tick repair.** Deferred: first pass is an instant action with a task
  penalty.

## Consequences

- The action space grows from 4 to 5 ops; masks and indexes change.
- The frozen benchmark and fault-free hashes remain valid.
- Recovery is a separate small control task, not a change to the line-building
  control task.
- A future RFC can add repair charges, multi-tick repair, or entity choice.
