# Mechanic RFC 0020 — Three-crew initial assignment

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0031, RFC 0013, ADR 0023, RFC 0017, ADR 0028

## Summary

Add a three-crew initial assignment task on the twin-line layout. Three crews
each choose one of three positive bridges in one 64-action assignment; duplicate
positive targets are masked. The task tests full three-agent coverage, not a
replacement slot or sequential survivor. The two-crew upper baseline uses the
same layouts with the third crew forced to noop.

## Motivation

The replacement handoff (0060) and pair-policy pilot (0061) were mixed: a
slot-swap oracle helped, but scripted handoff policies did not. A full third
crew at the initial decision tests the missing three-agent coordination axis
directly.

## Rules

- 32×16 twin-line, three positive bridges.
- Crews A, B, C: A at the depot, B on a seeded random base, C on another seeded
  random empty cell at least eight cells from A and B.
- Warning 40; failures 100/130/160 (wider than the two-crew task so three crews
  can cover the three bridges).
- One-shot action: each crew chooses noop or one of three bridges; duplicate
  positive targets masked. 64 actions.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score; success ≥ 400.
- Two-crew baseline: same layout and roles, crew C forced to noop; 16 actions.

## Observation and action impact

New observation adds crew C position and its distance to each role. `info` roles
add `distance_c` and `service_c`. Defaults and existing tasks are unchanged.

## Data impact

- New task `factory.power.crew-three.v1`.
- Frozen `factory-v0.1` is unchanged.

## Determinism

- A/B/C bases, roles, deadlines, and wires are seeded.
- Crews remain control state, not factory hash state.

## Tests

- Three positive roles and 64-action mask.
- Duplicate positive targets masked.
- C base separation.
- Two-crew baseline forces C noop.
- Frozen benchmark regression.

## Alternatives

- **Replacement slot swap.** Already 0060; scripted handoff failed H2.
- **Sequential survivor.** Already 0055.
- **Three crews plus recall.** Deferred; initial coverage first.

## Decision

Accepted. See ADR 0031 and experiment 0062. If three crews do not beat the
two-crew upper baseline by 10, retire the slice.
