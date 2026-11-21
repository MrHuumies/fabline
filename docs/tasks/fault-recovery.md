# Task card — fault recovery

- **Task ID:** `factory.fault.recover.v1`
- **Version:** 0.1.0
- **Status:** debug control task; opt-in fault mechanic; not in `factory-v0.1`
- **World:** factory-0.1.0 + FaultConfig
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

A working gear line accumulates wear and faults. The agent chooses each decision
interval between waiting for auto-repair and spending a repair action to restore
production immediately. The task tests whether recovery timing is learnable under
a repair cost.

## Contract

- **Observation:** `diagnostics` (13 features: tick, score, fault count,
  mean/max wear, temperature, vibration, acoustic, machine count, blocked).
- **Actions:** `0 noop`, `1 repair` the first faulted entity in stable ID order.
- **Reward:** score delta over the decision interval minus `repair_cost` when a
  repair happens.
- **Decision interval:** 10 ticks.
- **Episode length:** 500 ticks.
- **Success:** final score ≥ 250.
- **Faults:** wear per craft 1, threshold 20, auto-repair 30 ticks.

## Data

Online; no offline dataset in this pass. Evaluation: 5 episodes per seed,
seeds 0–2. Tabular Q training: 100 episodes per seed.

## Metrics

- Mean final score.
- Mean task reward.
- Mean repairs.
- Success rate (score ≥ 250).
- 95% bootstrap CIs over pooled episodes.

## Baselines

| Policy | Notes |
|---|---|
| noop | Wait for auto-repair |
| repair_now | Repair whenever a fault is available |
| random | Uniform over legal actions |
| tabular Q | Q-learning over fault count, mean wear bucket, tick bucket |

## Debug results

| policy | mean score | mean reward | mean repairs | success |
|---|---:|---:|---:|---:|
| noop | 230.00 [230.00, 230.00] | 230.00 | 0.00 | 0.00 |
| repair_now | 260.00 [260.00, 260.00] | 257.00 | 3.00 | 1.00 |
| random | 248.67 [243.33, 253.33] | 246.20 | 2.47 | 0.67 |
| tabular Q | 260.00 [260.00, 260.00] | 257.00 | 3.00 | 1.00 |

## Known pitfalls

- **Two actions only.** The task tests timing, not diagnosis or which entity to
  repair.
- **Repair-now is optimal at this cost.** A cost of 1 is small relative to the
  lost output; the task is easy.
- **One fixed line, one threshold, one cost.** No held-out layouts or fault
  severities.
- **Auto-repair still exists.** Repair is an acceleration, not the only recovery
  path.
- **Small evaluation budget.** CIs are wide.

## Negative controls

- Noop should be below success at the 250 score threshold.
- Random should be between noop and repair-now.

## Changelog

- 2026-11-21 — card created; debug recovery results added.
