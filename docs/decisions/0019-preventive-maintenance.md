# ADR 0019 — Preventive machine maintenance

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** RFC 0009, ADR 0011, ADR 0018, experiment 0037

## Context

Machine wear is visible and faults are deterministic, but repair is reactive:
the agent can only repair a faulted machine or wait for auto-repair. The wire
maintenance experiment showed that an early, timed action is valuable. The same
action channel is missing for normal faults.

## Decision

1. Add `FaultConfig.maintenance_ticks` (default 10).
2. Add `Entity.maintenance_remaining`, hashed only when nonzero.
3. Add `FactoryWorld.maintain_entity`: take a non-faulted, non-maintained
   machine offline; reset wear at completion.
4. Skip machine work while maintenance is active; count down in `_finish_tick`.
5. Add `factory.fault.preventive.v1`: noop vs maintain the most worn machine.
6. Compare noop, early/late wear thresholds, always-maintain, random, and
   tabular Q.
7. Keep the mechanic opt-in and outside frozen `factory-v0.1`.

## Alternatives considered

- **Instant maintenance.** Rejected; it removes the downtime trade.
- **Maintenance during work.** Rejected; no clear cost and harder to audit.
- **Only reactive repair.** Rejected; leaves wear without an action channel.
- **Wire prevention only.** Rejected; the user's question explicitly includes
  normal machines.

## Consequences

- Wear becomes actionable before the fault threshold.
- A planned 10-tick downtime can replace a longer auto-repair window.
- Maintenance adds a canonical timer only when active; frozen hashes unchanged.
- The task is deterministic and small; seed variance may be low.
- Maintenance target selection is the most worn machine; per-entity choice is
  not modeled.

## Follow-ups

- [ ] Maintenance tests and CLI.
- [ ] Experiment 0037.
- [ ] Per-entity maintenance scheduling and crew travel.
- [ ] Noisy wear sensors.
- [ ] Combine with the wire maintenance task.
