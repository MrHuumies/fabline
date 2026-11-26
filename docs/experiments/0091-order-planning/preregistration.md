# Experiment 0091 — Order planning

- **Status:** complete (positive; see [summary](summary.md))
- **Date:** 2026-11-26
- **Type:** 0.4.0 Phase 2 order-planning experiment
- **Task:** `factory.orders.plan.v1` (draft, not in a frozen benchmark)
- **Code:** `src/fabline/harness/order_planning.py`
- **CLI:** `python -m fabline order-planning`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Given a known seeded order set, can a finite recipe-block plan beat scripted
EDF/value plans, and does CEM with the simulator find the exhaustive oracle?

## Environment

- 16×8 gear line, 300-tick episodes, 10-tick decisions.
- Five recipe blocks of six decisions; each block is gear or component.
- Orders from `OrderConfig`: 4 orders, gear/component, quantity 3–8, deadline
  100–280, value 10–25; success value ≥ 160.
- Plan: 5 bits; exhaustive oracle is 32 plans.

## Conditions

| Policy | Rule |
|---|---|
| always_gear | all gear blocks |
| always_component | all component blocks |
| edf_plan | earliest-deadline order per block |
| value_plan | highest remaining value per block |
| random_plan | one random 5-bit plan |
| cem | CEM with the simulator |
| oracle | exhaustive 32 plans |

## Pilot (73,000–73,004)

| policy | mean value | success |
|---|---:|---:|
| always_gear | 126.0 | 0.20 |
| always_component | 142.8 | 0.20 |
| edf_plan | 200.4 | 0.80 |
| value_plan | 198.6 | 0.80 |
| random_plan | 196.0 | 0.60 |
| **cem** | **236.8** | **1.00** |
| **oracle** | **236.8** | **1.00** |

The pilot is positive but not a formal confirmation.

## Formal design

- Fresh seeds 74,000–74,004; same 5-block plan.
- CEM population 16, elites 4, iterations 4, 32 random samples.
- No post-hoc block count, order, or CEM tuning.

## Gates

| Gate | Threshold |
|---|---|
| H1 planning gap | oracle ≥ best scripted + 10 |
| H2 CEM over random | CEM ≥ random plan + 10 |
| H3 CEM quality | CEM within 10 of oracle |
| H4 success | CEM success ≥ 0.60 |
| H5 frozen benchmark | `factory-v0.2` unchanged |

## Predictions

- Oracle/CEM 220–250, success 1.0.
- EDF/value 190–215.
- H1–H4 pass if the pilot replicates; H5 is reported.

## Kill criteria

- Oracle under best scripted + 10: planning task too shallow.
- CEM under random + 10: planner search fails.
- CEM under oracle − 10: model/search gap.
- No post-hoc tuning.

## Transparency note

The 73k block was a pilot. Formal seeds 74k are fresh.
