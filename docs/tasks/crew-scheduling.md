# Task card — crew repair scheduling with travel

- **Task ID:** `factory.power.crew-schedule.v1`
- **Version:** 0.1.0
- **Status:** P1 debug task; formal run complete; not in `factory-v0.1`
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
- **Warnings:** tick 40; failures at 90/120/150.
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
| earliest_deadline | earliest failure tick among positive wires |
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

## Results (0040)

Seeds 800–804, 5 episodes each; success ≥ 150.

| policy | score | prevented | travel | success |
|---|---:|---:|---:|---:|
| noop | 56.8 | 0.0 | 0.0 | 0.00 |
| impact_only | 62.4 | 1.0 | 16.7 | 0.00 |
| nearest | 223.2 | 1.8 | 14.0 | 0.80 |
| earliest_deadline | **260.0** | 2.0 | 14.4 | **1.00** |
| oracle | **260.0** | 2.0 | 14.0 | **1.00** |
| tabular Q | 156.4 | 1.24 | 16.4 | 0.52 |

H1–H3 and H5 pass; **H4 fails** because Q does not learn the deadline/order
policy. The travel gain is +197.6, so P1 is not retired. See
[`experiments/0040-crew-schedule`](../experiments/0040-crew-schedule/summary.md).

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
- 2026-11-22 — formal run: EDF 260 vs impact 62; Q 156, H4 fails.
