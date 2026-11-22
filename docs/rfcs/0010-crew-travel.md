# Mechanic RFC 0010 — Crew travel and repair scheduling

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-22
- **Related:** ADR 0020, RFC 0007, RFC 0008, ADR 0017, ADR 0018

## Summary

Add a spatial repair crew to the wired-power maintenance tasks. The crew has a
position; servicing a wire costs travel time plus repair time. The agent chooses
which failed or degraded wire to service under a two-repair budget. Travel makes
the order and subset choice spatial, not just impact-ranked.

## Motivation

P1 repair tasks rank wires by outage impact or watch one wire. The 0.1.2
coverage review found that impact-only and fixed-threshold policies are already
close to optimal; contextual thresholds added only +5. The missing variable is
space: a far large bridge and a near small bridge create a real order/subset
trade.

## Rules

### Crew

- One crew with a position `(x, y)`, initialized at the depot.
- The crew is control state, not factory state; it is exposed in the observation
  and event log, not hashed into the factory state.
- Only one service job at a time.

### Target wires

- Select three wires from the outage audit:
  - a zero-impact loop;
  - a small-outage bridge;
  - a large-outage bridge.
- Warning tick: 40 for all three; the wires become degraded.
- Failure ticks: loop 220, small bridge 280, large bridge 340.
- A service started on a degraded wire is preventive; if it completes before the
  failure, the failure is canceled.
- If the target fails during travel or service, the job aborts; the wire remains
  failed and can be repaired reactively later.
- A service on an already-failed wire is reactive and completes normally.

### Travel and service time

- Travel ticks = Manhattan distance from the crew to the nearest target
  endpoint, multiplied by 2.
- Service ticks = 40.
- The action is atomic: the crew spends travel + service, then the wire is
  repaired and the crew position updates to the target endpoint.
- No repair budget is spent until the job starts; an aborted job still spends
  it.
- Budget: 2 jobs for 3 wires.

### Reward and outcome

- Preventive completion: time-weighted avoided outage.
- Reactive completion: time-weighted restored outage.
- Aborted job: no reward; budget spent.
- Outcome: final production score.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wire degradation | warnings and failures during travel | ticking jobs |
| repair budget | 2 jobs for 3 wires | subset choice |
| wire connectivity | outage impact per role | graph-derived label |
| production | travel and downtime cost | timing trade |
| frozen benchmark | wired mode only | hash regression |

## Observation impact

New crew-scheduling observation:

```text
tick_norm, score_norm, budget_remaining, crew_x_norm, crew_y_norm,
loop_outage, small_outage, large_outage,
loop_state, small_state, large_state,
loop_distance, small_distance, large_distance,
loop_service_time, small_service_time, large_service_time,
loop_deadline, small_deadline, large_deadline
```

The existing wire/repair views are unchanged.

## Action impact

Four actions: noop, service the loop, service the small bridge, service the
large bridge. The global grid action contract is unchanged.

## Data impact

- New task `factory.power.crew-schedule.v1` (debug/P1).
- New metrics: prevented/restored outage, travel ticks, aborted jobs.
- No dataset artifact.
- Frozen `factory-v0.1` has no wires or crew.

## Determinism

- Target selection is deterministic from the outage audit.
- Warning/failure ticks are fixed.
- Crew position updates are deterministic.
- The factory state hash does not include crew position; the control event log
  does.
- Replays validate warnings, failures, travel, and service events.

## Tests

- Crew position and travel time update deterministically.
- A preventive job completes before failure; a late job aborts.
- Budget and action masks.
- Observation shape and ranges.
- Role selection (loop/small/large).
- Frozen benchmark hash regression.

## Performance

Three targets, one crew; O(1) travel calculation per action. The 1k ticks/s
floor holds.

## Alternatives

- **Ranked slots without travel.** Already implemented (0033); no spatial trade.
- **One watched wire.** Already implemented (0035); no subset/order choice.
- **Buildable wires and rerouting.** Larger scope; defer.
- **Continuous crew movement.** Rejected for the first slice; atomic jobs are
  easier to audit.

## Decision

Accepted. See ADR 0020; experiment 0040 tests whether travel-aware scheduling
beats impact-only by at least 5 points. If not, P1 is retired.
