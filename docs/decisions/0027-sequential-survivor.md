# ADR 0027 — Sequential survivor dispatch

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0016, RFC 0012, ADR 0022, RFC 0013, ADR 0023, experiment 0054

## Context

The one-shot double-orphan pilot was negative: one survivor could recover one of
two orphans, so the best first assignment sent both crews at the same bridge and
greedy matched oracle. A repeated-failure task needs sequential survivor work.

## Decision

1. Add `job_failure_tick` to abort all active initial jobs at a fixed tick.
2. Track an orphan set rather than a single orphan.
3. Add `replan_jobs` (default 1). When greater than one, A gets another
   decision after each completed recovery while an orphan remains.
4. Keep the pair action space; the replan mask allows noop plus remaining
   positive orphans.
5. Define `factory.power.crew-multi-orphan.v1` on the twin-line layout with
   failure/recall at 80, two survivor jobs, success 400.
6. Compare noop, single EDF, nearest, greedy, recall-aware, no-replan, and an
   oracle sequence. Q is optional.

## Alternatives considered

- **One-shot double orphan.** Negative pilot (0053).
- **Third crew.** Deferred; new action contract.
- **Repair-attempt failure.** Deferred.
- **Multiple recalls.** Leaves no survivor after the second recall.

## Consequences

- The survivor can recover two orphans in sequence; travel order and deadlines
  matter.
- Defaults preserve 0045/0047 and the frozen benchmark.
- If greedy matches the oracle, the task is a recovery demonstration, not a hard
  assignment benchmark; report that caveat.
- The oracle requires sequence search, not a single pair lookup.

## Follow-ups

- [ ] Implement the multi-job replan loop and tests.
- [ ] Pilot and experiment 0054.
- [ ] Keep `factory-v0.1` frozen.
