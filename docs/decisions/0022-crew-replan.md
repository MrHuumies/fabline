# ADR 0022 — Crew recall and replanning

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** RFC 0012, RFC 0011, ADR 0021, experiment 0045

## Context

The two-crew assignment is robust over 40 seeds, but nearest is near-ceiling and
the oracle always chooses the same pair. The task has one decision and no agent
loss. Multi-agent coordination needs a failure/replanning question that is
smaller than a full worker world.

## Decision

1. Add a known recall tick for crew B (default 100).
2. Abort B's unfinished job at recall; completed B jobs count.
3. Let crew A recover B's abandoned positive bridge after B is gone and A's
   first job resolves; a loop orphan grants no useful dispatch.
4. Keep a fixed 16-action vector; mask the second decision to noop or the
   orphan.
5. Compare noop, single-crew EDF, failure-unaware nearest/greedy, recall-aware
   assignment, oracle, random, and tabular Q.
6. Keep the task opt-in and outside frozen `factory-v0.1`.

## Alternatives considered

- **Random failure.** Deferred; a known recall is deterministic and isolates
  replanning from failure prediction.
- **Mid-job redirection.** Deferred; needs partial travel state and a larger
  decision model.
- **No second decision.** Rejected; robust assignment without replanning is a
  weaker question.
- **Shared repair budget.** Rejected for this slice.

## Consequences

- The task has two decision points and a changing legal-action mask.
- B's service time and the recall window create a real assignment constraint.
- A's second dispatch tests whether the survivor can recover the abandoned
  target.
- If the second dispatch does not recover the orphan by at least 10 points
  over no-replan, the slice is retired. If recall-aware assignment is more than
  10 points worse than nearest, the slice is also retired. If Q fails the 0.85
  quality gate, that is a representation boundary, not a reason to tune on the
  evaluation seeds.
- Crews remain control state, not factory hash state.

## Follow-ups

- [ ] Implement the recall env and observation.
- [ ] Pilot and experiment 0045.
- [ ] Partial views only after failure/replanning is understood.
- [ ] Keep `factory-v0.1` frozen.
