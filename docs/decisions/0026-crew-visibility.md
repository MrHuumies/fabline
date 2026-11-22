# ADR 0026 — Private crew views and communication

- **Status:** pilot negative; retired for now
- **Date:** 2026-11-23
- **Related:** RFC 0015, RFC 0012, ADR 0022, RFC 0013, ADR 0023

## Context

The compact-Q line is near its ceiling and the 16×8 partial-view pilot was
binary. The twin-line layout now provides graded distances. The largest missing
multi-agent question is coordination when each crew has local information.

## Decision

1. Add an opt-in visibility wrapper to the crew tasks:
   - per-crew Manhattan radius;
   - shared report memory with an age limit;
   - action masks filtered to currently visible or reported targets.
2. Start with the centralized pair action; keep private per-crew policies and
   explicit message budgets as follow-ups.
3. Use the twin-line layout for the pilot; do not change the frozen benchmark.
4. Pilot a radius sweep and a delayed-report condition before any formal task.
5. Report scripted global/local/oracle results; Q is optional.

## Alternatives considered

- **Private per-crew policies immediately.** Deferred; it changes the action
  contract and would confound information with coordination.
- **Message budget instead of age.** Deferred; age is the simpler first channel.
- **Line-of-sight occlusion.** Deferred; radius is enough for the first test.
- **Repeated failure.** Fallback if visibility is binary again.

## Consequences

- Hidden wires are unknown to a crew; the dispatcher must assign under partial
  information.
- The survivor can only recover an orphan it has seen or been told about.
- Global behavior is unchanged when visibility is disabled.
- The radius curve is binary/stepwise and delayed reports add nothing on the
  current twin-line layout; the mechanic is retired for now.
- If the curve is graded, the next slice is private per-crew policies or a
  message budget.

## Follow-ups

- [ ] Implement the visibility wrapper and tests.
- [ ] Run the radius/report pilot.
- [ ] Promote only if the response is graded.
- [ ] Keep `factory-v0.1` frozen.
