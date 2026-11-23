# ADR 0029 — Crew report budget

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0018, RFC 0015, ADR 0026, experiment 0057

## Context

The distributed visibility task has a shared union and a delayed report, but no
bandwidth limit. A one-report-per-crew budget tests selective communication; the
pilot shows two reports match shared-local and one loses 60 points.

## Decision

1. Add `BudgetVisibilityEnv` with `reports_per_crew`.
2. Each crew reports its top-K visible positive bridges by outage/distance.
3. Reports are shared; either crew may target a reported bridge.
4. No report age in the budget condition.
5. Compare shared-local, K=2, K=1, and private policies on the spread layout.
6. Keep the task opt-in and frozen benchmark unchanged.

## Alternatives considered

- **Age only.** Already 0052/0056.
- **Explicit report actions.** Deferred; top-K scripted first.
- **Private only.** Already 0056; budget is the shared middle ground.

## Consequences

- K=3 is the shared-local upper bound.
- K=2 may be enough; K=1 is the bandwidth-limited condition.
- A negative result (K=1 matches shared) would mean the channel is not
  bandwidth-bound; report it.
- No world or frozen benchmark change.

## Follow-ups

- [ ] Formal experiment 0057.
- [ ] Keep `factory-v0.1` frozen.
