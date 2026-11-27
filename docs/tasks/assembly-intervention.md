# Task card — assembly recipe intervention

- **Task ID:** `factory.assembly.recipe_intervention.v1`
- **Version:** 0.1.0
- **Status:** frozen in `factory-v0.5`
- **World:** `factory-0.1.0` + opt-in production tree
- **Owner:** FABLINE
- **Date:** 2026-11-27
- **RFC:** [`0031-assembly-edge.md`](../rfcs/0031-assembly-edge.md)
- **Code:** `src/fabline/harness/assembly_intervention.py`
- **CLI:** `python -m fabline assembly-intervention`

## Phenomenon

Operators switch the assembly recipe as buffers and craft progress change.
A planner wants to know the counterfactual effect of forcing the opposite recipe
and holding it. The effect is heterogeneous: switching is harmful in most
states, neutral in others, and beneficial in a minority. The task tests
state-conditional effect estimation and the decision value of that estimate.

## Contract

- **Unit:** an assembly-cell state at a decision step.
- **Control:** continue the epsilon-random batch policy from that state.
- **Treatment:** force the opposite of the current assembly recipe and hold it
  to the end of the episode.
- **Effect:** treatment terminal score minus factual terminal score.
- **Data:** 200 episodes, seeds 58,000–58,199; 4 sample steps (10, 20, 30, 40);
  800 samples.
- **Split:** episode-level 70/20/10 from `assign_split`; 560 / 160 / 80 samples.
- **Features:** the standard 12-feature assembly-cell state.
- **Baselines:** mean, linear, GBDT, MLP; bootstrap CIs. The decision CI uses
  an episode-cluster bootstrap because sample states share an episode.
- **Decision metric:** switch when the predicted effect is positive. Compare the
  model policy to always-switch, always-continue, and the paired oracle.

## Gates

| Gate | Threshold |
|---|---|
| H1 skill | GBDT R² ≥ 0.30 |
| H2 nonlinear | GBDT ≥ linear + 0.05 |
| H3 not saturated | GBDT R² < 0.98 |
| H4 decision | model gain ≥ half of oracle gain and ≥ 0.5 |
| H5 MLP skill | MLP R² ≥ 0.20 |

Frozen v0.1–v0.4 hashes are enforced by the test suite and CI, not by the task
runner.

## Results (formal pilot, 200 episodes)

| Model | Test R² | Test MAE |
|---|---:|---:|
| mean | −0.004 | 35.16 |
| linear | −0.838 | 45.11 |
| **GBDT** | **0.944** | 8.05 |
| MLP | 0.769 | 17.60 |

Decision quality on the test split:

| Policy | Mean terminal score |
|---|---:|
| oracle | 442.50 |
| model (GBDT) | 442.12 |
| always continue | 440.50 |
| always switch | 400.50 |

The model switches on 20% of test states and captures +1.62 of the +2.00 oracle
gain (81%), with regret 0.38.

## Known pitfalls

- **Paired potential outcomes.** Labels come from the simulator, not from a
  logged dataset with one arm per unit. A logged-data identification task is a
  follow-up.
- **Sparse benefit.** Only 10% of states have a positive effect. Do not report
  average effect as if switching were generally good.
- **Small absolute gain.** The decision improvement is +1.62 score over
  always-continue. The oracle gap itself is 2.00, so precision matters more than
  magnitude.
- **One stochastic control trajectory.** The factual continuation is a single
  realization of the behaviour policy, paired across sample states.
- **Fixed cell.** There is no layout or demand variation.

## Changelog

- 2026-11-27 — task card created; formal pilot positive and frozen in
  `factory-v0.5`.
