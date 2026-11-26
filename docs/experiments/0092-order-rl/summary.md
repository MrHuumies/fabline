# Experiment 0092 — Deep/offline RL on order control

- **Status:** complete (negative for BC/PPO gates)
- **Date:** 2026-11-26
- **Type:** 0.4.0 baseline track
- **Task:** `factory.orders.control.v1` (draft, not in a frozen benchmark)
- **Code:** `src/fabline/harness/order_rl.py`
- **CLI:** `python -m fabline order-rl`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The deep/offline RL baselines are negative on this task.** On fresh seeds
77,000–77,004, behavior cloning scores **249.8** with success 0.80, only **+6.6**
over random **243.2/1.00**, below the +10 gate. PPO scores **169.0/0.44**, well
below random. Scripted value is 272.5/1.00, EDF 270.6/1.00, and tabular Q
259.5/1.00. H1 (BC) and H2 (PPO) fail; H3 (best learned success) and H4 (cost)
pass; H5 passes. The scripted/tabular references remain the useful baselines.
Do not tune PPO/BC after this block.

## Formal results

Five evaluation seeds, five episodes each:

| policy | value | success | train s | parameters |
|---|---:|---:|---:|---:|
| EDF | 270.6 | 1.00 | 0.00 | — |
| value | **272.5** | **1.00** | 0.00 | — |
| random | 243.2 | 1.00 | 0.00 | — |
| tabular Q | 259.5 | 1.00 | 0.00 | — |
| BC | 249.8 | 0.80 | 1.05 | 1,218 |
| PPO | 169.0 | 0.44 | 5.34 | 1,283 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 BC | BC ≥ random + 10 | **fail**, +6.6 |
| H2 PPO | PPO ≥ random + 10 | **fail**, −74.3 |
| H3 success | best learned success ≥ 0.60 | **pass**, BC 0.80 |
| H4 cost | report training/inference/parameters | **pass** |
| H5 frozen benchmark | `factory-v0.2` unchanged | **pass** |

## Interpretation

- **BC is close to random but not useful.** It imitates the value expert on
  training states, but the policy is not robust enough on fresh order seeds.
- **PPO fails at this budget/task.** The two-action recipe decision is small but
  the reward is sparse/delayed; 10k steps is not enough, or PPO is a poor fit.
- **Scripted and Q references dominate.** The task is valid; the deep-RL
  baseline track is negative at this scope.
- **This is not a task failure.** Order control remains positive with Q at
  259.5/1.00 and the order-planning task is positive.

## Caveats

- 10k PPO steps, 100 BC episodes, 3 PPO seeds; a larger budget is a new
  pre-registration.
- BC uses value-policy demonstrations, not human data.
- The task is a small two-action discrete control problem; deep RL has little
  room.
- Torch is optional; the core remains headless.

## Next

1. Do not tune PPO/BC after this block.
2. Move to demand calibration/causal variants or a `factory-v0.3` freeze
   decision.
3. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/order-control.md`](../../tasks/order-control.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/order_rl.py`
- Raw results: `results/order-rl/` (ignored)
