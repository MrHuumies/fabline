# Mechanic RFC 0014 — Recall/replanning on twin-line layouts

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-22
- **Related:** ADR 0024, RFC 0012, ADR 0022, RFC 0013, ADR 0023

## Summary

Combine the crew recall/replanning task with the twin-line randomized layout.
Two crews are assigned on a 32×16 twin-line map with a random crew-B base; crew
B is recalled at 100 and the survivor recovers the abandoned bridge. The layout
makes the first assignment non-trivial, while the recall tests whether the
second dispatch still adds value when distances are nonlocal.

## Motivation

The 16×8 recall task is positive but shallow: nearest is within 6 points of
oracle. The twin-line layout (0046) breaks the assignment ceiling: oracle 441,
greedy 419, nearest 361. The natural question is whether recovery still matters
when the first assignment is hard.

## Rules

- 32×16 map, two gear lines, random x offsets, one generator capacity 24.
- Crew A at the first depot; crew B on a random empty cell at least eight
  Manhattan cells from A.
- Warning 40; failures 90 (loop), 110 (small), 130 (large).
- B recall at 100; unfinished B job aborts.
- Initial one-shot pair assignment; same-wire positive pairs masked.
- After B leaves and A's first job resolves, A may recover the abandoned
  positive bridge or noop. A loop orphan grants no useful dispatch.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score; success ≥ 400.

## Observation and action impact

Same two-crew observation plus phase, B availability, recall countdown, and
orphan role. Same 16-action vector; the second decision is masked to noop or the
abandoned positive bridge.

## Data impact

- New task `factory.power.crew-replan-layouts.v1` (debug/P2).
- Frozen `factory-v0.1` is unchanged.

## Determinism

- Twin-line rows, x offsets, random B, generator, wires, and crew positions are
  seeded.
- Crews remain control state, not factory hash state.

## Tests

- Twin-line layout and random B are deterministic.
- Recall aborts B's unfinished job and exposes the orphan.
- The survivor's recovery improves score over no-replan.
- Frozen benchmark regression.

## Alternatives

- **Recall on the 16×8 layout only.** Already done (0045); nearest is too close
  to oracle.
- **Twin-line assignment only.** Already done (0046); no recall.
- **Full random topology plus recall.** Deferred.

## Decision

Accepted. See ADR 0024; experiment 0047 tests whether recovery adds at least 10
points on the twin-line layout and whether the layout keeps an oracle gap.
