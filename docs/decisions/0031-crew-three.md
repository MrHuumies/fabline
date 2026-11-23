# ADR 0031 — Three-crew initial assignment

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0020, RFC 0019, ADR 0030, experiment 0062

## Context

The replacement handoff oracle helped but the best scripted replacement policy
was worse than the no-replacement baseline. A full third crew at the initial
decision tests three-agent coverage instead of a slot swap.

## Decision

1. Add `ThreeCrewEnv` with 64 actions (four choices per crew).
2. Three positive bridges; A at the depot, B and C on seeded random bases at
   least eight cells apart.
3. Widen deadlines to 100/130/160 so three crews can cover the bridges.
4. Mask duplicate positive targets.
5. Compare two-crew (C noop) and three-crew nearest/greedy/aware/oracle on the
   same layouts.
6. Keep the task opt-in and frozen benchmark unchanged.

## Alternatives considered

- **Replacement slot swap.** Mixed; scripted H2 failed.
- **Three crews plus recall.** Deferred.
- **Larger action space with four bridges.** Deferred.

## Consequences

- The three-crew oracle can cover all three bridges; two crews cannot.
- The third crew adds a coverage gain, but scripted policies may saturate.
- C's base and deadlines are scope choices; do not tune them per method.
- No world or frozen benchmark change.

## Follow-ups

- [ ] Formal experiment 0062.
- [ ] Keep `factory-v0.1` frozen.
