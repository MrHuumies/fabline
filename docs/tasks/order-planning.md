# Task card — order planning

- **Task ID:** `factory.orders.plan.v1`
- **Version:** 0.1.0
- **Status:** draft; Phase 2 candidate; not in any frozen benchmark
- **World:** factory-0.1.0 + opt-in production/order configs
- **Owner:** FABLINE
- **Date:** 2026-11-26

## Phenomenon

A known set of orders with quantities, deadlines, and values must be satisfied
by choosing an initial production plan. The task tests finite-horizon planning
with a product mix and demand value, not another one-shot recipe rule.

## Contract

- **Observation:** initial production/order state.
- **Plan:** a sequence of recipe choices or a line configuration, fixed before
  execution.
- **Orders:** item, quantity, deadline, value; deterministic seeded set.
- **Reward:** fulfilled value minus late/unfilled penalties.
- **Episode:** 500 ticks; plan horizon fixed at preregistration.
- **Success threshold:** fixed at preregistration.

## Baselines

| Baseline | Rule |
|---|---|
| always_gear | fulfill gear orders only |
| always_component | fulfill component orders only |
| EDF/value | scripted order priority |
| random | random legal plan |
| CEM/true | CEM with the simulator |
| oracle | small exhaustive plan set |

## Metrics

- fulfilled value and fraction;
- late/unfilled quantity;
- plan success;
- planning latency and model error if a learned model is used.

## Gates (pilot)

| Gate | Threshold |
|---|---|
| H1 task validity | oracle ≥ best scripted + 10 |
| H2 planning | CEM true ≥ random + 10 |
| H3 success | CEM true success ≥ 0.60 |
| H4 frozen benchmark | `factory-v0.2` unchanged |

## Known pitfalls

- The plan action space must stay small enough for an oracle.
- Demand values can make one item dominant; report the mix.
- Orders are a task layer; they must be opt-in.
- Do not tune deadline/value distributions after the formal block.

## Changelog

- 2026-11-26 — draft card created; Phase 2 pending.
