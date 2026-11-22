# ADR 0021 — Two-crew parallel repair assignment

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** RFC 0011, RFC 0010, ADR 0020, experiment 0042

## Context

Multi-agent coordination is the largest missing family in the coverage review. A
full worker world is too large; the crew scheduling task already has travel,
deadlines, and spatial assignment. Adding a second crew is the smallest step
that tests parallel cooperation and duplicate-work avoidance.

## Decision

1. Add a second crew with a fixed starting base and position.
2. Add a one-shot parallel assignment task with three targets: loop, small
   bridge, large bridge.
3. Actions are 16 pairs; same-wire positive assignments are masked.
4. Jobs run concurrently; each target can abort if it fails during travel or
   service.
5. Compare single-crew EDF, parallel nearest, parallel greedy, oracle, random,
   and Q.
6. Keep the task opt-in and outside frozen `factory-v0.1`.

## Alternatives considered

- **Full mobile worker agents.** Deferred; too large for the first slice.
- **Sequential dispatch.** Rejected; no parallel coordination.
- **Partial per-crew views.** Deferred; first establish the centralized gain.
- **Shared repair budget.** Rejected for the first slice; one job per crew is
  simpler and still tests duplication.

## Consequences

- The task tests coordination and spatial assignment, not communication.
- Two crews add a 16-action pair space and a second position.
- If two crews do not beat the best single-crew assignment by 10 points, the
  slice is retired and P2 moves to larger/random layouts or full agents.
- Crew positions remain control state, not factory hash state.

## Follow-ups

- [ ] Implement the two-crew env and observation.
- [ ] Pilot and experiment 0042.
- [ ] Partial views/communication only if the centralized gain is real.
- [ ] Keep `factory-v0.1` frozen.
