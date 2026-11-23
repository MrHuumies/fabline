# ADR 0028 — Three-bridge survivor triage

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0017, RFC 0016, ADR 0027, experiment 0055

## Context

The all-abort sequential task (0054) is positive but shallow: both jobs fail
before completing, the initial assignment is irrelevant, and greedy matches
oracle. A useful repeated-failure task needs some initial jobs to finish so the
first assignment trades off against survivor triage.

## Decision

1. Add `role_mode="three_positive"`: use three positive bridges instead of
   loop/small/large. The internal `loop` key becomes the medium bridge.
2. Add `replan_mode="all_positive"`: survivor decisions may target any
   unresolved positive bridge, not only orphans.
3. Set job failure/recall at 100, two survivor jobs, success 300.
4. Define `factory.power.crew-triage.v1` on the 32×16 twin-line layout.
5. Compare noop, single EDF, nearest, greedy, recall-aware, no-replan, and an
   oracle sequence. Q is optional.
6. Keep defaults and the frozen benchmark unchanged.

## Alternatives considered

- **All-abort triage.** Initial assignment is irrelevant; 0053/0054 showed the
  collapse.
- **Third crew.** Deferred.
- **Spread-layout triage.** Possible follow-up.

## Consequences

- Initial jobs can complete before 100, so the first pair matters.
- A can recover two of the three unresolved bridges; one is left.
- The role names are legacy (`loop` means medium); task docs must state this.
- If oracle does not beat the best scripted policy by 10, the task is a shallow
  recovery demo, not a benchmark.

## Follow-ups

- [ ] Pilot and experiment 0055.
- [ ] Keep `factory-v0.1` frozen.
