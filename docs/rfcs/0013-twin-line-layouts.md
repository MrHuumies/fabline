# Mechanic RFC 0013 — Twin-line randomized crew layouts

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-22
- **Related:** ADR 0023, RFC 0011, ADR 0021, experiment 0046

## Summary

Add an opt-in twin-line layout family for the two-crew repair assignment. Two
gear lines are placed on a 32×16 map with random row and horizontal offsets;
one generator feeds both lines; crew B starts on a random empty cell at least
eight cells from crew A. The two-crew assignment task is unchanged, but the
larger, less compact layout makes crew-target matching matter.

## Motivation

The 16×8 two-crew task is robust but easy: nearest is within a few points of the
oracle and the oracle pair is almost always the same. Larger empty maps did not
help; the production line stayed compact. A second line makes the wire graph and
crew distances spatially nonlocal, which is the missing larger/random-layout
test.

## Rules

- Map 32×16, two gear lines with independent row placement and random x offsets.
- One generator, capacity 24, wired topology; both lines share it.
- Crew A starts at the first depot; crew B starts on a random empty cell at
  least eight Manhattan cells from A.
- Targets: the zero-outage loop and the smallest/largest positive bridge, as in
  the two-crew task.
- Warning 40; failures 90 (loop), 110 (small), 130 (large).
- One-shot pair assignment; same-wire positive pairs masked.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score. Success ≥ 400 on the two-line score scale.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wired power | two lines share a generator and wire tree | connectivity |
| crew travel | random B base creates assignment conflicts | nearest failures |
| two-crew assignment | larger layout makes the pair non-obvious | saturation |
| production | two depots, score ~520 at full service | threshold |
| frozen benchmark | opt-in scenario only | hash regression |

## Observation impact

The two-crew observation is unchanged: tick, score, crew positions, and
per-role outage/state/deadline/distance. Only the layout and crew base change.

## Action impact

No change: 16 initial pair actions with same-wire positive masks.

## Data impact

- New task `factory.power.crew-layouts.v1` (debug/P2).
- New scenario `random_gear` with two lines.
- Frozen `factory-v0.1` has no twin lines and no randomized crew base.

## Determinism

- Line rows, x offsets, crew B, generator placement, and wires are seeded.
- Crew positions are control state, not factory hash state.
- Replays validate the assignment and job timelines.

## Tests

- Twin-line generation places two miners and two depots.
- Random crew B is deterministic and at least the minimum distance from A.
- One-shot assignment and masks are unchanged.
- Frozen benchmark regression.
- Oracle/scripted gap on the pilot block.

## Performance

Two lines add entities and wire edges but remain small (14 entities, <110
wires). The 1k ticks/s floor holds.

## Alternatives

- **Larger single line.** Rejected; the production line stayed compact and
  nearest sat on the ceiling.
- **Random line orientation.** Deferred; east-facing lines are enough for the
  first spatial test.
- **Multiple generators.** Deferred; one shared generator keeps the wire graph
  connected.
- **Full random factory topology.** Deferred; larger than this slice.

## Decision

Accepted. See ADR 0023; experiment 0046 tests whether the twin-line layout makes
the oracle at least 10 points better than the best scripted two-crew policy.
