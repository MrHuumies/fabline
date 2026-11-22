# ADR 0020 — Spatial repair crew

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** RFC 0010, RFC 0007, RFC 0008, experiment 0040

## Context

P1 repair tasks rank wires by outage impact or watch a single wire. The 0.1.2
coverage review found that threshold and impact-only policies are close to
optimal; contextual thresholds added only +5. The next plausible variable is
space: travel time makes the order and subset choice non-trivial.

## Decision

1. Add a single crew with a position, initialized at the depot.
2. Select three target wires: loop, small bridge, large bridge.
3. Add `factory.power.crew-schedule.v1` with four actions: noop, service loop,
   service small bridge, service large bridge.
4. Service time = 2 × Manhattan travel + 40-tick repair. Jobs are atomic.
5. Warn all three at tick 40; failures at 220/280/340. Budget 2.
6. Keep crew position in the control observation/event log, not the factory
   state hash.
7. Compare noop, impact-only, nearest, travel-aware, oracle, random, and Q.
8. If travel-aware does not beat impact-only by 5 points, retire P1 and move to
   P2.

## Alternatives considered

- **Ranked slots without travel.** Implemented; no spatial trade.
- **One watched wire.** Implemented; no subset/order choice.
- **Continuous crew movement.** Deferred; atomic jobs are easier to audit.
- **Buildable wires/rerouting.** Larger scope.

## Consequences

- The repair decision gains a spatial context: near small vs far large.
- The control state has a crew position outside the factory hash.
- The task is a small, bounded scheduling benchmark.
- If the gain is weak, the review's kill rule stops the line.

## Follow-ups

- [ ] Implement the crew env and observation.
- [ ] Pilot and formal experiment 0040.
- [ ] Multi-crew scheduling only if the single-crew gain is real.
- [ ] Keep `factory-v0.1` frozen.
