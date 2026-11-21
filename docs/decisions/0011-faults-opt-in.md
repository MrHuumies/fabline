# ADR 0011 — Opt-in machine faults

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0002, ADR 0007, ADR 0009

## Context

The next step is world complexity. The
first mechanic considered is machine wear and faults:

- machines stop producing while faulted;
- new diagnostic channels (wear, thermal, vibration, acoustic) become available;
- fault labels and recovery tasks create new causal/control structure.

The frozen `factory-v0.1` benchmark must keep its behavior, config hash, and
state hashes. Adding fault fields to `FactoryConfig` or always-on faults would
break both.

## Decision

1. Add a separate `FaultConfig`, disabled by default.
2. Add `wear`, `faulted`, and `repair_progress` to entities, but include them in
   the canonical state hash **only when nonzero**. Fault-free hashes stay
   identical to `factory-v0.1`.
3. Auto-repair after `repair_ticks`; no repair action at this point (ADR 0012
   later added one).
4. Add `sensors` (H×W×5: wear, temperature, vibration, acoustic, faulted) and
   `diagnostics` (13 aggregate features) observation adapters.
5. Add an opt-in `fault.predict` task and debug benchmark. It is not part of
   `factory-v0.1`.
6. Record the fault config in fault replay files; `validate_replay` restores it.
7. The viewer can show faults with `render --faults`.

## Alternatives considered

- **Add fault fields to FactoryConfig.** Rejected: changes the config hash and
  the frozen benchmark identity.
- **Always-on faults.** Rejected: changes default behavior and benchmark data.
- **Add a repair action now.** Deferred: the first mechanic pass is observation
  and auto-repair; a repair action changes the action contract and belongs in a
  separate RFC.
- **A separate world.** Rejected for now: the same factory with opt-in faults is
  enough and keeps content/data paths shared.

## Consequences

- `factory-v0.1` remains valid without regeneration.
- Fault-free state hashes are unchanged; a regression test covers this.
- Fault episodes must carry their fault config for replay.
- Fault tasks and datasets are a new consumer track, not a frozen benchmark.
- Auto-repair is a simplification; repair control is the next fault follow-up.

## Later

ADR 0012 added an explicit repair action after the passive auto-repair MVP.
