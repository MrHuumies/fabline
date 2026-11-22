# Task card — crew repair scheduling with travel

- **Task ID:** `factory.power.crew-schedule.v1`
- **Version:** 0.1.0
- **Status:** P1 debug task; implementation pending; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

A repair crew must service degraded or failed wires before they fail. The crew
has a position; travel plus repair time makes the order and subset choice
spatial. A far large bridge and a near small bridge create a real trade.

## Contract

- **Observation:** tick, score, budget, crew position, and per-role outage,
  state, travel time, and deadline.
- **Actions:** noop; service the loop; service the small bridge; service the
  large bridge.
- **Crew:** one position, starts at the depot.
- **Travel:** 2 ticks per Manhattan cell to the nearest wire endpoint.
- **Service:** 40 ticks.
- **Warnings:** tick 40; failures at 220/280/340.
- **Budget:** 2 jobs for 3 wires.
- **Reward:** time-weighted prevented/restored outage.
- **Outcome:** production score; success threshold set in the pilot.

## Metrics

- mean production score;
- prevented and restored outage;
- travel ticks;
- aborted jobs;
- success rate.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never service |
| impact_only | largest positive outage |
| nearest | nearest positive outage |
| travel_aware | outage per service tick |
| oracle | best two-wire order |
| random | uniform legal action |
| tabular Q | role/spatial state |

## Gates

See [`experiments/0040-crew-schedule`](../experiments/0040-crew-schedule/preregistration.md).

| Gate | Threshold |
|---|---|
| H1 travel gain | best travel-aware ≥ impact_only + 5 |
| H2 oracle gain | oracle ≥ impact_only + 10 |
| H3 order sensitivity | order differs on ≥3/5 seeds |
| H4 Q quality | Q ≥ 0.85 × best; success ≥ 0.80 |
| H5 budget | report travel/abort/service counts |

## Known pitfalls

- **Atomic jobs.** Travel and service are one action; continuous movement is a
  follow-up.
- **One crew.** Multi-crew scheduling is not modeled.
- **Role selection is deterministic.** The loop/small/large roles come from the
  outage audit.
- **Crew position is control state.** It is not in the factory state hash.
- **If travel adds less than 5 points, retire P1.**
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-22 — card created; mechanic and gates preregistered.
