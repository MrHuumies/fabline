# ADR 0023 — Twin-line randomized crew layouts

- **Status:** accepted
- **Date:** 2026-11-22
- **Related:** RFC 0013, RFC 0011, ADR 0021, experiment 0046

## Context

The two-crew assignment is robust over 40 seeds but nearest is near-ceiling and
the oracle pair is nearly always the same. Larger empty maps made the task
easier, because the production line stayed compact and the scaled deadlines gave
crews more time. A layout change is needed to make spatial assignment matter.

## Decision

1. Add a `random_gear` scenario with two east-facing gear lines at independent
   rows and random horizontal offsets.
2. Share one generator with capacity 24 across both lines.
3. Let crew B start on a seeded random empty cell at least eight cells from A.
4. Add opt-in `scenario`, `randomize_crew_b`, and `crew_b_min_distance` fields
   to `MultiCrewConfig`; all defaults preserve the 0042/0045 behavior.
5. Define `factory.power.crew-layouts.v1` on a 32×16 map with the existing
   two-crew action and observation contract.
6. Compare noop, single-crew EDF, nearest, greedy, random, oracle, and tabular Q.
7. Keep the task opt-in and outside frozen `factory-v0.1`.

## Alternatives considered

- **Larger single-line maps.** Rejected by pilot: nearest saturated at 260.
- **Random line orientation.** Deferred; the first spatial test is east-facing.
- **Multiple generators.** Deferred; one shared generator keeps the graph
  connected.
- **Full random factory topology.** Deferred; too large for this slice.

## Consequences

- The wire graph spans two lines; crew travel and bridge assignment are no
  longer local.
- The score scale doubles (~520 at full service); success is 400.
- The map is larger but still deterministic and replayable.
- If the oracle does not beat the best scripted policy by 10, the layout variant
  is retired.
- Q may fail on the larger state; report the gap rather than tuning on the
  evaluation seeds.
- Crews remain control state, not factory hash state.

## Follow-ups

- [ ] Add the twin-line scenario and opt-in crew config.
- [ ] Pilot and experiment 0046.
- [ ] Test the recall/replan task on the same layouts only after the assignment
  gap is established.
- [ ] Keep `factory-v0.1` frozen.
