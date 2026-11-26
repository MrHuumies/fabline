# Task card — order control

- **Task ID:** `factory.orders.control.v1`
- **Version:** 0.1.0
- **Status:** Phase 2 formal positive; not in any frozen benchmark
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

## Results (0090)

Seeds 72,000–72,004; five episodes per seed:

| policy | value | success |
|---|---:|---:|
| always gear | 119.6 | 0.40 |
| always component | 222.3 | 0.56 |
| EDF | 289.0 | 1.00 |
| value | **289.8** | **1.00** |
| random | 226.4 | 0.88 |
| tabular Q | **280.2** | **1.00** |

H1/H2/H3/H4 pass. Q is +53.8 over random and succeeds on every formal episode.
See [`experiments/0090-order-control`](../experiments/0090-order-control/summary.md).

## Deep/offline RL (0092)

Seeds 77,000–77,004; 10k PPO steps, 100 BC episodes:

| policy | value | success |
|---|---:|---:|
| scripted value | 272.5 | 1.00 |
| tabular Q | 259.5 | 1.00 |
| BC | 249.8 | 0.80 |
| PPO | 169.0 | 0.44 |

BC is +6.6 over random, below the +10 gate; PPO is below random. The deep/offline
RL baseline track is negative at this budget; do not tune it. See
[`experiments/0092-order-rl`](../experiments/0092-order-rl/summary.md).

## Changelog

- 2026-11-26 — draft card created; Phase 3 pending.
- 2026-11-26 — formal positive: value 289.8, Q 280.2, random 226.4.
