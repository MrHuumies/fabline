# Task card — power allocation control

- **Task ID:** `factory.power.allocate.v1`
- **Version:** 0.1.0
- **Status:** debug control task, opt-in power mechanic; not in `factory-v0.1`
- **World:** factory-0.1.0 + PowerConfig
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

A gear line shares a generator budget too small to run the furnace and assembler
together. The agent chooses a power priority each decision interval. It must
build ingot buffers with the furnace, then switch to the assembler to make
gears. A fixed priority either never makes gears or drains the buffer and
stalls.

## Contract

- **Observation:** `power_control` (18 features: 12 power features, assembler
  input, furnace output, assembler/furnace craft progress, miner output, score).
- **Actions:** `0 default` (entity-id order), `1 favor_furnace`,
  `2 favor_assembler`.
- **Reward:** score delta over the decision interval.
- **Decision interval:** 10 ticks.
- **Episode length:** 500 ticks.
- **Success:** final score ≥ 100.
- **Power:** one generator, capacity 5, radius 8.
- **Faults:** disabled in this task.

## Data

Online; no offline dataset or replay. Evaluation: 5 episodes per seed, seeds
0–2. Tabular Q training: 100 episodes per seed.

## Metrics

- Mean final score.
- Mean task reward.
- Success rate (score ≥ 100).
- 95% bootstrap CIs over pooled episodes.

## Baselines

| Policy | Notes |
|---|---|
| default | Always id-order allocation |
| favor_furnace | Always furnace-first |
| favor_assembler | Always assembler-first |
| alternate | Scripted: assemble while crafting or input ≥ 2, else furnace |
| random | Uniform over actions |
| tabular Q | Q-learning over buffers, craft state, and tick bucket |

## Debug results

| policy | mean score | mean reward | success |
|---|---:|---:|---:|
| default | 0.00 [0.00, 0.00] | 0.00 | 0.00 |
| favor_furnace | 0.00 [0.00, 0.00] | 0.00 | 0.00 |
| favor_assembler | 10.00 [10.00, 10.00] | 10.00 | 0.00 |
| alternate | **130.00** [130.00, 130.00] | 130.00 | **1.00** |
| random | 78.67 [68.67, 87.33] | 78.67 | 0.13 |
| tabular Q | **116.67** [114.67, 119.02] | 116.67 | **1.00** |

## Stochastic results

Under load jitter 30, capacity jitter 20, period 20 (5 episodes per seed, seeds
0–2, 100 training episodes):

| policy | mean score | success |
|---|---:|---:|
| default | 6.67 | 0.00 |
| favor_furnace | 12.00 | 0.00 |
| favor_assembler | 90.67 | 0.40 |
| alternate | **136.00** | **1.00** |
| random | 108.00 | 0.80 |
| tabular Q | **118.00** | **0.80** |

Q beats the best fixed policy on every seed (118 vs 90/90/92) and reaches 86.8%
of the scripted alternator. All pre-registered gates pass.

## Known pitfalls

- **One line, one budget.** Capacity 5 is a narrow regime chosen to make the
  trade-off visible. Other capacities are different tasks.
- **Scripted alternator is oracle-style.** It uses buffer and craft state; it is
  a reference, not a learned result.
- **The task is easy for tabular Q.** The value is the allocation contract and
  the scheduling structure, not a hard RL benchmark.
- **Priority, not per-entity allocation.** The action space is three type-level
  priorities.
- **No faults.** Fault/power interaction is a future task.
- **Stochastic success is 0.80, not 1.00.** Q is robust but not optimal; random
  is a strong baseline at 108.00.
- **The 30/20/20 regime was chosen from a pilot.** It is not tuned against the
  formal run.
- **Small evaluation budget.** CIs are wide.

## Negative controls

- Fixed furnace-first and default should score near zero.
- Random should be between fixed policies and alternation.
- Tabular Q should beat fixed policies.

## Changelog

- 2026-11-21 — card created; power-allocation control results added.
- 2026-11-21 — stochastic allocation results added (0020).
