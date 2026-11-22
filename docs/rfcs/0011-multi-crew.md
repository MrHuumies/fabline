# Mechanic RFC 0011 — Multi-crew repair coordination

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-22
- **Related:** ADR 0021, RFC 0010, ADR 0020

## Summary

Add a two-crew repair assignment task. Two crews with different starting
positions are dispatched in parallel to a loop, a small bridge, and a large
bridge. The agent chooses a wire for each crew (or noop). The crews travel and
repair concurrently; one crew alone cannot cover both bridges before their
deadlines, but two crews can. This is the first multi-agent slice: shared
deadlines, spatial assignment, and duplicate-work avoidance.

## Motivation

The coverage review identifies multi-agent coordination as the largest missing
family. A full worker/vehicle world is too large for one step. The existing crew
scheduling task already has positions, travel, and deadlines; adding a second
crew tests coordination with minimal new mechanics.

## Rules

- Two crews, A and B, with fixed starting positions (depot and a second base).
- Three target wires: loop, small bridge, large bridge.
- Warnings at tick 40; failures at 90 (loop), 110 (small), 130 (large).
- The agent assigns each crew one target (or noop) when the wires are degraded.
- The assignment is one-shot: both jobs start at the same tick and run
  concurrently; after both complete, no more jobs.
- Travel = 2 × Manhattan distance to the target endpoint; service = 40 ticks.
- Assigning both crews to the same positive wire is illegal.
- A crew whose target fails before its service completes aborts.
- Reward: production score gained from the assignment to the end of the episode.
- Outcome: final production score; success threshold set in the pilot.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wire degradation | failures during parallel travel | two jobs tick together |
| crew travel | different bases create the assignment trade | position state |
| repair budget | each crew one job; no shared pool | duplicate assignment |
| production | parallel restoration | timing |
| frozen benchmark | wired mode only | hash regression |

## Observation impact

New two-crew observation: tick, score, crew positions, and per-wire outage,
state, deadline, and distance to each crew.

## Action impact

16 pair actions (noop/loop/small/large for each crew), with same-wire positive
assignments masked. The existing crew task is unchanged.

## Data impact

- New task `factory.power.crew-coordination.v1` (debug/P2).
- Metrics: prevented/restored outage, travel, aborted jobs, duplicate
  assignments.
- Frozen `factory-v0.1` has no crews or wires.

## Determinism

- Target roles, bases, warnings, and failures are deterministic.
- Crew positions update after each job.
- Crews are control state, not factory hash state.
- Replays validate the assignment and both job timelines.

## Tests

- Pair action decoding and masks.
- Parallel job completion and abort.
- Single-crew vs two-crew scores.
- Observation shape.
- Frozen benchmark regression.

## Performance

Two crews, three targets; constant work per action. The 1k ticks/s floor holds.

## Alternatives

- **Full mobile worker agents.** Deferred; much larger.
- **Sequential two-crew dispatch.** Rejected for the first slice; it does not
  test parallel coordination.
- **Partial per-crew views.** Deferred until the centralized assignment is
  understood.

## Decision

Accepted. See ADR 0021; experiment 0042 tests whether two crews beat the best
single-crew assignment by at least 10 points.
