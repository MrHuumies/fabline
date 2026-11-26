# Experiment 0090 — Order-control pilot

- **Status:** complete (positive; see [summary](summary.md))
- **Date:** 2026-11-26
- **Type:** 0.4.0 Phase 2 order-control experiment
- **Task:** `factory.orders.control.v1` (draft, not in a frozen benchmark)
- **Code:** `src/fabline/env/orders.py`,
  `src/fabline/harness/order_control.py`
- **CLI:** `python -m fabline order-control`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Does a seeded gear/component order stream create a real recipe-switching
decision, and can a tabular Q policy beat random while scripted EDF/value
policies provide strong references?

## Environment

- 16×8 gear line, 300-tick episodes, 10-tick decisions.
- Production mix enabled: recipe 0 gear, recipe 1 component.
- 4 seeded orders per episode: gear/component, quantity 3–8, deadline 100–280,
  value 10–25 per unit.
- Fulfillment on delivery; earliest-deadline allocation; failed units lose
  `0.5 × value`; success at fulfilled value ≥ 160.
- Order state is task-layer state; default world hash is unchanged.

## Conditions

| Policy | Rule |
|---|---|
| always_gear | recipe 0 throughout |
| always_component | recipe 1 throughout |
| edf | earliest active order’s item |
| value | highest remaining value per tick |
| random | uniform recipe |
| tabular Q | recipe/tick/deadline/demand buckets, 100 training episodes |

## Pilot (71,000–71,004)

5 episodes per seed:

| policy | value | success |
|---|---:|---:|
| always_gear | 117.8 | 0.20 |
| always_component | 189.2 | 0.80 |
| edf | 265.2 | 1.00 |
| value | 275.5 | 1.00 |
| random | 217.1 | 0.84 |
| tabular Q | 257.6 | 0.96 |

The pilot is positive but not yet a formal confirmation.

## Formal design

- Fresh seeds 72,000–72,004; same 5-episode block.
- Q seed/training start 72,000 + 1000; 100 episodes.
- No post-hoc order, value, deadline, or success tuning.

## Gates

| Gate | Threshold |
|---|---|
| H1 order effect | best scripted ≥ always_gear + 10 |
| H2 learned policy | Q ≥ random + 10 |
| H3 success | Q success ≥ 0.60 |
| H4 frozen benchmark | `factory-v0.2` unchanged |

## Predictions

- Value policy 250–290, success 0.9–1.0.
- Q 240–275, success 0.85–1.0.
- H1/H2/H3 pass if the pilot replicates; H4 is reported.

## Kill criteria

- Best scripted under always_gear + 10: no order effect.
- Q under random + 10: learned policy negative.
- Q success under 0.60: task not reliable.
- No post-hoc tuning.

## Transparency note

The 71k block was an implementation pilot. Formal seeds 72k are fresh.
