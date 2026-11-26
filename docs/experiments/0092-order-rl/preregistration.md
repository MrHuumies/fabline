# Experiment 0092 — Deep/offline RL on order control

- **Status:** complete (negative; see [summary](summary.md))
- **Date:** 2026-11-26
- **Type:** 0.4.0 baseline track
- **Task:** `factory.orders.control.v1` (draft, not in a frozen benchmark)
- **Code:** planned `src/fabline/harness/order_rl.py`
- **CLI:** planned `python -m fabline order-rl`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Can behavior cloning and PPO learn the online gear/component order-control
policy, and how do they compare with the scripted and tabular-Q references?

## Hypothesis

The task is a small two-action control problem with a strong scripted reference.
BC should approach the expert; PPO may match or beat Q but is not guaranteed to
beat the value policy. A negative learned baseline is a valid result.

## Environment

Same as 0090:

- 16×8 gear line, 300-tick episodes, 10-tick decisions;
- 4 seeded orders, gear/component, deadlines/values;
- success value 160;
- two actions: gear/component.

## Conditions

| Policy | Rule |
|---|---|
| always_gear / always_component | fixed |
| edf / value | scripted references |
| random | uniform |
| tabular Q | 100 training episodes (0090) |
| BC | cloned from value/EDF expert trajectories |
| PPO | on-policy, 5 seeds, optional Torch |

## Design

- Train seeds 75,000+; pilot eval seeds 76,000–76,004; formal eval 77,000–77,004.
- BC: 100 expert episodes from the value policy; MLP 16→64→2.
- PPO: 3 seeds, MLP 16→64→2 actor + value head, 10k steps, gamma 0.99,
  clip 0.2, 4 epochs; CPU.
- Torch is optional; without it, skip PPO/BC with a clear message.
- Report training/inference time and parameter count.

## Gates

| Gate | Threshold |
|---|---|
| H1 BC | BC ≥ random + 10 |
| H2 PPO | PPO ≥ random + 10 |
| H3 success | best learned success ≥ 0.60 |
| H4 cost | report training/inference seconds and parameters |
| H5 frozen benchmark | `factory-v0.2` unchanged |

If PPO is under random, report a negative deep-RL result; do not tune the
network after the formal block.

## Pilot (76,000–76,004)

| policy | value | success |
|---|---:|---:|
| edf | 260.6 | 1.00 |
| value | 275.4 | 1.00 |
| random | 238.2 | 0.96 |
| tabular Q | 254.5 | 1.00 |
| BC | 240.6 | 0.84 |
| PPO | 153.0 | 0.48 |

BC is +2.5 over random, below the +10 gate; PPO is below random. The pilot is
negative. Formal seeds 77k are fresh and use the same budgets.

## Predictions

- BC 240–290, success 0.85–1.0.
- PPO 200–290, success 0.7–1.0; seed-sensitive.
- Scripted value ~290; Q ~280.

## Kill criteria

- BC under random + 10: expert cloning is not useful.
- PPO under random + 10: negative deep-RL result.
- No post-hoc network, reward, or seed tuning.

## Transparency note

This is a baseline track, not a new mechanic. A negative result does not affect
the order-control task.
