# ADR 0018 — Preventive wire maintenance

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** RFC 0008, RFC 0007, ADR 0017, experiment 0035

## Context

Wire repair is reactive: only failed wires can be repaired. A failure prediction
can rank failed wires, but there is no action that uses the prediction before
the outage. Experiment 0034 added repair time but still repaired only failed
wires, and the repair-order effect was not robust.

## Decision

1. Add `PowerWire.degraded` and `failure_tick` as canonical wired state.
2. Allow repair of degraded wires. A preventive job that completes before the
   scheduled failure cancels it.
3. If the failure occurs during a preventive job, abort the job, spend the
   budget, and leave the wire failed for a later reactive repair.
4. Add a two-action maintenance environment: noop or repair the watched wire.
5. Add `factory.power.wire-maintenance.v1`, with preventive, reactive, late,
   random, and tabular-Q baselines.
6. Keep the mechanic opt-in and outside frozen `factory-v0.1`.

## Alternatives considered

- **Health percentage with gradual decay.** Deferred; a binary warning is
  enough to test whether prediction is actionable.
- **Noisy prediction.** Deferred until the perfect-warning case is useful.
- **Repair continues through failure.** Rejected; it removes the cost of
  starting late.
- **Preventive repair for normal machines.** Deferred; wire maintenance is the
  smaller, self-contained mechanic.

## Consequences

- A prediction now has a concrete action: start a repair during the warning
  window.
- Late starts are punished by aborted jobs and spent budget.
- Wired state hashes include degradation and failure ticks; radius/frozen hashes
  are unchanged.
- The task is small (one watched wire); multi-wire scheduling is a follow-up.
- Noisy prediction and false positives remain future work.

## Follow-ups

- [ ] Wire maintenance tests and CLI.
- [ ] Experiment 0035.
- [ ] Multi-wire preventive scheduling.
- [ ] Noisy warning/prediction quality.
- [ ] Preventive maintenance for machine wear.
