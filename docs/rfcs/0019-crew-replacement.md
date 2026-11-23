# Mechanic RFC 0019 — Replacement crew handoff

- **Status:** mixed; not promoted as a benchmark (0060 H2 fails)
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0030, RFC 0016, ADR 0027, RFC 0017, ADR 0028

## Summary

Add a replacement crew to the three-bridge triage task. Crew B is recalled at
tick 100; a replacement crew C arrives at the same base and takes B's slot. The
survivor decision becomes a pair assignment for A and C, testing handoff and
parallel recovery instead of sequential survivor work.

## Motivation

The P2 coverage review identifies third crew/replacement as the largest
remaining multi-agent axis. A full three-crew initial action space would be 64
actions; the replacement slot tests handoff with the existing 16-action pair
contract. Pilot: replacement best scripted 490 vs no-replacement 430 (+60).

## Rules

- Base: three-positive triage, 32×16 twin-line, failure/recall at 100.
- Initial pair: A and B.
- B is recalled at 100; C arrives immediately at B's original base.
- Post-failure decision: A and C each choose noop or a remaining positive
  bridge; duplicate positive assignments are masked.
- One replacement pair; no additional sequential jobs.
- Reward: final production score; success ≥ 300.

## Observation and action impact

The 16-action pair vector is reused: first = A, second = the second crew (B
initially, C after recall). The observation's second-crew position becomes C
after recall. `info` exposes `replacement_arrived`. Defaults preserve existing
tasks.

## Data impact

- New task `factory.power.crew-replacement.v1`.
- Frozen `factory-v0.1` is unchanged.

## Determinism

- C's base is B's original seeded base.
- Failure, recall, positions, and job durations are deterministic.
- Crews remain control state, not factory hash state.

## Tests

- C arrives at recall and the mask allows an A/C pair.
- B's unfinished jobs abort; C is available.
- Defaults preserve no-replacement tasks.
- Frozen benchmark regression.

## Alternatives

- **Full three-crew initial action space.** Deferred; 64 actions.
- **Sequential A-only recovery.** Already 0055.
- **Random replacement delay.** Deferred; immediate handoff first.

## Decision

Accepted. See ADR 0030 and experiment 0060. Compare replacement handoff against
the no-replacement triage; if the handoff does not add 10, retire it.
