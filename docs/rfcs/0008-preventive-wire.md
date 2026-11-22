# Mechanic RFC 0008 — Preventive wire maintenance

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-22
- **Related:** ADR 0018, RFC 0007, ADR 0017

## Summary

Make wire repair predictive, not only reactive. A wire can enter a **degraded**
state with a scheduled failure tick. A repair started while degraded is a
preventive job; if it completes before the failure, the outage is prevented. If
the failure lands mid-repair, the job aborts and the budget is spent. This gives
a prediction a timing-sensitive action channel.

## Motivation

RFC 0007 wire repair only accepts failed wires: `PowerWire.failed` is the only
repair gate. A failure prediction can rank failed wires, but it cannot justify
starting work early. The 0034 timing experiment changed repair duration but
still only repaired failed wires on a schedule, so the order effect was weak.

Preventive maintenance is the missing consumer of a prediction. The agent sees a
warning before the failure and must decide whether to spend a repair window now
or wait. Starting early avoids downtime; starting late wastes the job.

## Rules

### Degraded state

- `PowerWire` gains `degraded: bool` and `failure_tick: int` (0 = none).
- `degraded` wires are still functional; they are not failed.
- `FactoryWorld.degrade_wire(wire_id, failure_tick)` marks a wire degraded and
  emits `power_wire_degraded`.
- At `failure_tick`, `_apply_wire_degradation` fails the wire through the normal
  `fail_wire` path and clears `degraded`/`failure_tick`.
- `repair_wire` clears `failed`, `degraded`, and `failure_tick`.
- Only wired power supports degradation; radius mode is unchanged.

### Preventive repair

- A repair action may target a failed **or degraded** wire.
- The repair is atomic: the crew spends `repair_ticks`; the wire is not
  restored until completion.
- If the target is degraded and fails during the repair, the job aborts:
  - no restoration reward;
  - the budget is spent;
  - the wire remains failed for a later reactive repair.
- If the target is already failed at the start, the repair is reactive and
  completes normally.
- If the target is degraded and does not fail, the repair is preventive; the
  wire stays healthy and the scheduled failure is canceled.

### Warning and failure schedule

- The environment chooses a target from the outage audit and sets the warning
  and failure ticks.
- The world owns the failure transition; the environment owns the warning.
- The warning is deterministic and visible in the observation.
- Noisy predictions, false positives, and false negatives are future work.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wire faults | degraded wires fail at their scheduled tick | ordering must be before power allocation |
| reactive repair | failed wires still repairable | budget competition |
| wire connectivity | degraded wires still carry power | no outage until failure |
| repair timing | preventive jobs must finish before failure | late jobs abort |
| frozen benchmark | wire state only in wired mode | hash regression must be tested |

## Observation impact

New maintenance observation, 8 features:

```text
tick_norm, score_norm, outage_norm, degraded, failed,
time_to_failure_norm, budget_norm, repaired
```

Existing wire and power views are unchanged.

## Action impact

The maintenance task has two actions: noop and repair. The repair action is
legal only when the target is degraded or failed and budget remains. The wire
repair and allocation control action spaces are unchanged.

## Data impact

- New task `factory.power.wire-maintenance.v1`.
- New labels/rewards: prevented vs reactive restoration vs aborted job.
- No dataset artifact; the environment generates layouts.
- Frozen `factory-v0.1` has no wires and no degradation.

## Determinism

- Target selection and warning/failure ticks are deterministic from the layout.
- The world applies failure before power allocation.
- Degraded and failure fields are canonical and hashed with wires.
- Replays validate degradation and repair events.

## Tests

- Wire-free and radius hashes unchanged.
- Degrade/repaire clears state and emits events.
- Failure occurs at the scheduled tick and not before.
- Preventive completion cancels failure.
- Late repair aborts and spends budget.
- Reactive repair works after failure.
- Observation shape and action mask.
- Q training/evaluation seeds are disjoint.
- Frozen benchmark regression.

## Performance

One watched wire and one repair job; O(wires + consumers) for the outage audit.
The 1k ticks/s floor must hold.

## Alternatives

- **Health percentage with gradual decay.** Deferred: a binary warning is
  enough to test actionability.
- **Noisy failure prediction.** Deferred: first show that a perfect warning is
  useful.
- **Repair while degraded continues through failure.** Rejected: it removes the
  timing penalty and makes early starts less meaningful.
- **Preventive repair on normal machines.** A follow-up; wire maintenance is the
  smaller mechanic.

## Decision

Accepted. See ADR 0018; experiment 0035 tests preventive vs reactive repair.
