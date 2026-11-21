# Experiment 0030 — Contract evaluation with unique interleaved seeds

- **Status:** complete (H3 misses narrowly; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P0 evaluation-design experiment; follow-up to
  [`0028`](../0028-risk-contract/summary.md) and
  [`0029`](../0029-risk-contract-dense/summary.md)
- **Task:** `factory.power.contract.v1`, failure-dense regime
- **Benchmark:** none; `factory-v0.1` unchanged

## Why this experiment exists

Experiments 0028 and 0029 both failed the pre-registered 20% tail gate. A
post-hoc audit found a sampling defect: the runner called
`evaluate_policy(episodes=N, seed=block)`, and that function resets with
`seed + episode`. Adjacent blocks therefore overlapped, and the reported sample
counts overstated unique episodes.

- 0028 train: blocks 40–79, 10 episodes each → unique seeds 40–88 (49, not 400).
- 0028 test: blocks 80–99, 10 episodes each → unique seeds 80–108 (29, not 200).
- The train and test episode sets overlapped on seeds 80–88.
- 0029 had the same defect: train unique 100–148, test unique 140–188, overlap
  140–148.

This experiment fixes the expansion, uses disjoint interleaved blocks, and
re-runs the same contract and regime. It is an **evaluation-design** test, not a
mechanic change.

## Sampling fix

`episode_seed_list` expands each block as `block * episodes_per_seed + episode`
before calling `evaluate_policy` one episode at a time. This makes every
evaluated episode seed unique and keeps train and test disjoint.

- Train blocks: even 200–598 (200 blocks).
- Test blocks: odd 201–599 (200 blocks).
- 10 episodes per block → 2,000 unique train episodes and 2,000 unique test
  episodes.
- Interleaving blocks by parity balances any low-frequency drift across the
  seed range.

## Regime and contract

- Failure-dense power regime: load jitter 60, capacity jitter 40, period 20,
  generator capacity 5, radius 8.
- Scripted alternator operating policy.
- Target tiers: 80, 85, …, 150.
- Payoff: production score `s`, plus `T - 100` when `s >= T`, minus 40 when
  `s < T`.
- CVaR alpha 0.2.
- Selection is offline over logged scores.

The regime and payoff are unchanged from 0029 so that the sampling fix is the
only experimental variable.

## Analysis

- Report every tier's train and test mean, CVaR₂₀, hit rate, and worst payoff.
- Report both selection rules and all five gates.
- Report train/test distribution summaries to check whether the shift shrank.
- Report a **block bootstrap** 95% CI for the CVaR gain: resample the 200 test
  blocks with replacement, 2,000 iterations, seed 0.
- Report the number of unique episode seeds and confirm zero train/test overlap.
- Do not change the regime, tiers, penalty, alpha, blocks, or gates after the
  formal run.

## Gates

Same as 0029:

| Gate | Threshold |
|---|---|
| H1 tradeoff | train mean-optimal target > train CVaR-optimal target |
| H2 mean cost | test mean of the mean policy ≥ test mean of the CVaR policy − 5 |
| H3 tail gain | test CVaR of the CVaR policy ≥ test CVaR of the mean policy + 15 |
| H4 directional stability | mean target > CVaR target on both train and test |
| H5 no free lunch | neither policy dominates on test mean and CVaR |

Data-integrity precondition: train and test episode seeds are disjoint. The
runner rejects overlap at config construction.

## Predictions

- The train/test distribution gap will shrink because the seed blocks are now
  unique and interleaved.
- The mean/CVaR direction will hold.
- The design pilot on blocks 0–39 gave a +6.5 CVaR gain with a block-bootstrap CI
  of [−4.0, 18.0]. The formal result may or may not clear +15.
- If H3 fails again with clean sampling, the contract task is retired as a
  benchmark.

## Kill criteria

- H3 fails (tail gain below +15).
- Train and test mean differ by more than 10 points, or zero rates differ by
  more than 3 percentage points.
- The mean/CVaR direction reverses.
- The result requires post-hoc changes to the regime, contract, or gates.

Any of these retires the contract task as a benchmark; it remains a documented
negative.

## Artifacts

- Code: `experiments/risk_control/contract.py`
- Formal config: `experiments/risk_control/eval_design_formal.json`
- Raw results: `results/risk_control/contract_eval_design/` (ignored)
- Summary: `docs/experiments/0030-contract-eval-design/summary.md`
- Task card: `docs/tasks/power-contract.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
