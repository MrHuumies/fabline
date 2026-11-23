# ADR 0032 — Three-crew recall and recovery

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0021, RFC 0020, ADR 0031, RFC 0017, ADR 0028, experiment 0063

## Context

Three-crew initial assignment is positive (0062). The recall tasks are positive
at two crews. The remaining question is whether the third crew helps when one
crew is recalled.

## Decision

1. Add `ThreeCrewReplanEnv`: 64-action initial dispatch, recall at 100, B job
   aborts, A/C 16-action recovery pair.
2. Keep deadlines 100/130/160 and success 400.
3. Compare three nearest/greedy/aware with and without recovery, plus oracle.
4. Keep the task opt-in and the frozen benchmark unchanged.

## Alternatives considered

- **Sequential survivor with three crews.** Deferred; one recovery pair first.
- **Replacement slot swap.** Already 0060; mixed.
- **Three crews plus failure without recall.** Deferred.

## Consequences

- The task tests third-crew coverage and post-loss recovery together.
- The initial 64-action and recovery 16-action spaces are fixed.
- If recovery does not beat no-replan by 10, retire the slice.
- If the oracle gap is small, report a shallow recovery result.
- No world or frozen benchmark change.

## Follow-ups

- [ ] Formal experiment 0063.
- [ ] Keep `factory-v0.1` frozen.
