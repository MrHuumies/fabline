# Experiment 0029 — Reliability contract in a failure-dense power regime

- **Status:** complete (H3 fails; see [`summary.md`](summary.md))
- **Correction:** the block expansion overlapped adjacent blocks; see the
  sampling note in the summary. Experiment 0030 fixes it.
- **Date:** 2026-11-21
- **Type:** P0 risk-sensitive control experiment; follow-up to
  [`0028`](../0028-risk-contract/summary.md)
- **Task:** `factory.power.contract.v1` under a failure-dense regime
- **Benchmark:** none; `factory-v0.1` unchanged

## Question

Does the mean/CVaR contract tradeoff survive when power failures are frequent
enough that the tail is sampled rather than clustered?

Experiment 0028 showed the tradeoff, but the pre-registered 20% tail gain failed:
the held-out test block was benign except for five contiguous seeds with zero
scores. This experiment changes only the stochastic-power regime, not the world
or the contract mechanism, and uses fresh seeds.

## Regime change

| Setting | 0028 | 0029 |
|---|---:|---:|
| Generator capacity | 5 | 5 |
| Generator radius | 8 | 8 |
| Load jitter | 30 | **60** |
| Capacity jitter | 20 | **40** |
| Variation period | 20 | 20 |

The 60/40 regime was chosen in a design pilot (seeds 0–39) because it produces a
heavier lower tail while keeping the line productive:

- mean score 126.5; standard deviation 32.2;
- 5th percentile 95, 20th percentile 120, median 130;
- zero-score rate 5%, spread across seeds (no seed block mean below 100).

This is a **scope condition**, not a claim that the harsher regime is the
canonical one. The 30/20/20 regime remains the reference.

## Contract

- Each episode runs the stochastic power-allocation task with the scripted
  alternator.
- Target tiers: 80, 85, …, 150 (step 5).
- Payoff for target `T`:
  - production score `s`;
  - bonus `T - 100` when `s >= T`;
  - miss penalty 40 when `s < T`.
- The target does not affect the world; it changes only the payoff.
- Selection is offline over logged scores, not online bandit learning.

The miss penalty 40 is unchanged from 0028. The bonus base moves from 120 to 100
because the failure-dense regime lowers the score scale. Both were frozen from
the design pilot before the formal run.

## Data

- Training log: seeds 100–139, 10 episodes each = 400 scores.
- Test log: seeds 140–179, 10 episodes each = 400 scores.
- Design pilot: seeds 0–39 under the same 60/40 regime; not formal evidence.
- The formal seeds are disjoint from both the 0028 formal seeds (40–99) and the
  design pilot (0–39).

## Selection rules

| Rule | Choice |
|---|---|
| mean-optimal | target with the highest mean payoff on train |
| CVaR-optimal | target with the highest CVaR₂₀ payoff on train |

CVaR₂₀ is the mean of the worst 20% of payoffs. Ties go to the lower target.

## Gates

| Gate | Threshold |
|---|---|
| H1 tradeoff | train mean-optimal target > train CVaR-optimal target |
| H2 mean cost | test mean of the mean policy ≥ test mean of the CVaR policy − 5 |
| H3 tail gain | test CVaR of the CVaR policy ≥ test CVaR of the mean policy + 15 |
| H4 directional stability | mean target > CVaR target on both train and test |
| H5 no free lunch | neither selected policy dominates the other on test mean and CVaR |

H4 checks the direction, not exact target identity. The design pilot selected
130 vs 100 on train and 120 vs 110 on test; exact targets may move with the seed
block, but the ordering should not reverse.

## Predictions

- Train selects target **130** by mean and target **100** by CVaR₂₀.
- On test, the mean policy (130) earns about 127 mean and 48 CVaR; the CVaR
  policy (100) earns about 123 mean and 78 CVaR.
- The risk-safe target costs about 4 mean points and gains about 30 CVaR points.
- Test-optimal targets may be 120/110 rather than 130/100; the direction should
  still hold.
- Zero scores remain near 5% and are spread across seeds, not clustered in a
  contiguous block.

## Analysis plan

- Report every tier's train and test mean, CVaR, hit rate, and worst payoff.
- Report both selection rules and all five gates.
- Report the score distribution and a per-seed block summary to check for
  clustering.
- Report CVaR at alpha 0.1 and 0.05 as **exploratory** diagnostics only; gates
  use the pre-registered alpha 0.2.
- Do not change the regime, tiers, penalty, alpha, or seeds after the formal run.
- If the tradeoff fails to replicate, report the negative in the first
  paragraph; do not search for a regime that works.

## Kill criteria

- Mean- and CVaR-optimal targets coincide on train.
- The risk-safe policy costs more than 10 mean points.
- The tail gain is below 10 CVaR points.
- The direction reverses between train and test.
- The test failures are again concentrated in a contiguous seed block.
- The result requires post-hoc changes to the regime or payoff.

## Artifacts

- Code: `experiments/risk_control/contract.py`
- Formal config: `experiments/risk_control/regime_d_formal.json`
- Raw results: `results/risk_control/contract_regime_d/` (ignored)
- Summary: `docs/experiments/0029-risk-contract-dense/summary.md`
- Task card: `docs/tasks/power-contract.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
