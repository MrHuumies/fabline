# Task card — fault + power interaction control

- **Task ID:** `factory.fault_power.control.v1`
- **Version:** 0.1.0
- **Status:** debug control task, opt-in faults and power; not in `factory-v0.1`
- **World:** factory-0.1.0 + FaultConfig + PowerConfig
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Faults change power demand: a faulted machine draws nothing, and repairing it
re-enters demand. Under a tight power budget, an agent must combine priority
switching and selective repair. Unconditional repair causes brownouts;
ignoring faults loses production.

## Contract

- **Observation:** `fault_power` (24 features: power 12, line buffers 6, fault
  aggregates 6).
- **Actions:** `0 noop`, `1 favor_furnace`, `2 favor_assembler`,
  `3 repair` the first faulted entity in stable id order.
- **Reward:** score delta minus `repair_cost` when a repair happens.
- **Decision interval:** 10 ticks.
- **Episode length:** 500 ticks.
- **Success:** final score ≥ 90.
- **Faults:** wear per craft 1, threshold 5, auto-repair downtime 30.
- **Power:** one generator, capacity 5, radius 8, deterministic.

## Data

Online; no offline dataset or replay. Evaluation: 5 episodes per seed, seeds
0–2. Tabular Q training: 200 episodes per seed.

## Metrics

- Mean final score.
- Mean task reward.
- Mean repairs per episode.
- Success rate (score ≥ 90).
- 95% bootstrap CIs over pooled episodes.

## Baselines

| Policy | Notes |
|---|---|
| noop | Default power order, never repair |
| favor_furnace | Furnace-first, never repair |
| favor_assembler | Assembler-first, never repair |
| repair_now | Repair whenever available, else noop |
| alternate_repair | Scripted: repair when the assembler is active and input ≥ 2; otherwise alternate |
| random | Uniform over legal actions |
| tabular Q | Q-learning over buffers, fault type, repair progress, max wear, tick bucket |

## Debug results

| policy | mean score | mean reward | mean repairs | success |
|---|---:|---:|---:|---:|
| noop | 0.00 [0.00, 0.00] | 0.00 | 0.00 | 0.00 |
| favor_furnace | 0.00 [0.00, 0.00] | 0.00 | 0.00 | 0.00 |
| favor_assembler | 10.00 [10.00, 10.00] | 10.00 | 0.00 | 0.00 |
| repair_now | 0.00 [0.00, 0.00] | 0.00 | 2.00 | 0.00 |
| alternate_repair | **110.00** [110.00, 110.00] | 106.00 | 4.00 | **1.00** |
| random | 70.00 [64.67, 75.33] | 67.73 | 2.27 | 0.07 |
| tabular Q | **93.33** [91.33, 96.00] | 90.33 | 3.00 | **1.00** |

## Known pitfalls

- **One line, budget, and fault regime.** Capacity 5, threshold 5, downtime 30,
  success ≥ 90 are chosen from a pilot.
- **Repair has no entity choice.** It always targets the first faulted entity.
- **Unconditional repair is bad.** It re-enters demand and causes brownouts.
- **The scripted policy is oracle-style.** It uses buffer and repair state.
- **Q is below the scripted policy.** 93.33 vs 110.00, but within 20%.
- **Success is 90, not the maximum score.** This is a modest production target.
- **Online-only.** No dataset or replay is written.

## Negative controls

- Noop, furnace-first, and assembler-first should score near zero.
- Repair-now should be worse than selective repair.
- Random should be between fixed policies and learned policies.

## Changelog

- 2026-11-21 — card created; fault + power interaction results added.
