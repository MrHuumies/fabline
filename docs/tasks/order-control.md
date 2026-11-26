# Task card — order control

- **Task ID:** `factory.orders.control.v1`
- **Version:** 0.1.0
- **Status:** draft; Phase 3 candidate; not in any frozen benchmark
- **World:** factory-0.1.0 + opt-in production/order configs
- **Owner:** FABLINE
- **Date:** 2026-11-26

## Phenomenon

Orders arrive with quantities, deadlines, and values. The agent chooses recipe
switches and production actions online. The task tests sequential control under
demand pressure and is the deep/offline RL baseline surface.

## Contract

- **Observation:** production view + order queue/status.
- **Action:** recipe selection plus existing build/remove actions; wrapper
  action contract fixed at preregistration.
- **Orders:** seeded arrivals; fulfillment on delivery; late/unfilled penalties.
- **Reward:** order value plus production score minus penalties.
- **Episode:** 500 ticks; decision interval 10.
- **Success threshold:** fixed at preregistration.

## Baselines

| Baseline | Rule |
|---|---|
| always_gear | produce gear only |
| always_component | produce component only |
| EDF/value | scripted priority |
| random | random legal actions |
| tabular Q | production/order buckets |
| behavior cloning | scripted/oracle trajectories |
| PPO/SAC | optional Torch baselines |

## Metrics

- fulfilled value/fraction, lateness, wasted production;
- score and success;
- recipe switches/setup time;
- sample/compute/inference cost.

## Gates (pilot)

| Gate | Threshold |
|---|---|
| H1 task validity | oracle ≥ best scripted + 10 |
| H2 learned baseline | best learned ≥ random + 10 |
| H3 success | best baseline success ≥ 0.60 |
| H4 frozen benchmark | `factory-v0.2` unchanged |

## Known pitfalls

- Deep RL is optional; scripted and tabular baselines must run headless.
- Order value can dominate; report the fixed/learned gap.
- The action wrapper must not change the frozen grid action contract.
- Do not tune demand distributions after the formal block.

## Changelog

- 2026-11-26 — draft card created; Phase 3 pending.
