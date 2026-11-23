# Mechanic RFC 0021 — Three-crew recall and recovery

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0032, RFC 0020, ADR 0031, RFC 0017, ADR 0028

## Summary

Combine the three-crew initial assignment with a recall. Three crews choose
bridges in a 64-action initial dispatch; B is recalled at tick 100; the
remaining A/C pair makes a 16-action recovery decision. The task tests whether a
third crew helps both initial coverage and post-loss recovery.

## Motivation

The full three-crew task (0062) is positive: three greedy 476, oracle 520, two
crews 320. The recall/replan tasks are positive at two crews. This slice asks
whether the third crew also absorbs a loss.

## Rules

- 32×16 twin-line, three positive bridges.
- A at depot, B and C on seeded random bases.
- Warning 40; failures 100/130/160; recall 100.
- Initial action: 64 actions (noop/loop/small/large for A/B/C), duplicate
  positive targets masked.
- B's unfinished job aborts at recall; B leaves.
- Recovery action: 16 A/C pair actions, duplicate positive targets masked.
- One recovery pair; no sequential jobs.
- Reward: final production score; success ≥ 400.

## Observation and action impact

New observation adds phase, B availability, and recall countdown to the
three-crew feature vector. The initial action space is 64; the recovery action
space is the first 16 entries of the same vector.

## Data impact

- New task `factory.power.crew-three-replan.v1`.
- Frozen `factory-v0.1` is unchanged.

## Tests

- 64-action initial mask and 16-action recovery mask.
- B recall aborts the job and A/C pair is legal.
- Observation shape and phase transition.
- Defaults preserve one-shot three-crew.
- Frozen benchmark regression.

## Alternatives

- **Three crews + sequential survivor.** Deferred; one pair first.
- **Two-crew replacement.** Already 0060; mixed.
- **Four bridges.** Deferred.

## Decision

Accepted. See ADR 0032 and experiment 0063. If recovery does not beat no-replan
by 10, retire the slice; if the oracle gap is shallow, report it.
