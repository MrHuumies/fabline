# ADR 0015 — Power-allocation control

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** RFC 0005, RFC 0004, ADR 0014

## Context

The power grid is observational in phase 1. Under a tight budget, the agent
needs a way to decide which load gets power. A fixed priority is insufficient
because the gear line needs the furnace and assembler at different times.

The existing line-building control task has its own observation/action contract
and must stay unchanged.

## Decision

1. Add `WorldState.power_priority` as canonical state, hashed only when
   nonzero.
2. Extend allocation order: default by entity id, furnace-first, or
   assembler-first.
3. Add a separate `PowerAllocationEnv` with three actions, a 500-tick gear-line
   episode, capacity 5, decision interval 10, and reward = score delta.
4. Add a `power_control` observation with the 12 power features plus line
   buffers, craft progress, miner output, and score.
5. Add `power-allocation` CLI with default, furnace-first, assembler-first,
   scripted alternation, random, and tabular-Q baselines.
6. Keep the frozen benchmark, fault tasks, and macro control unchanged.

## Alternatives considered

- **Extend the macro control task with power.** Rejected: it changes the
  construction task's observation/action contract.
- **Per-entity allocation.** Rejected: too large an action space for the MVP.
- **Load shedding.** Rejected: fixed shedding policies are degenerate; the
  interesting decision is when to switch priority.
- **Two independent lines.** Deferred: the single gear line already creates the
  furnace-vs-assembler trade-off.

## Consequences

- Power allocation is a small control task with a clear scheduling structure.
- `power_priority` changes power-enabled state hashes; power-free hashes are
  unchanged.
- The task is online-only; no dataset or replay is written.
- The scripted alternator is an oracle-style baseline, not a learned policy.
- The task is easy for tabular Q at this budget; it is a debug control task, not
  a hard RL benchmark.
