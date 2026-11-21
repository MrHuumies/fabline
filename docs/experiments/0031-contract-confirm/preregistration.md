# Experiment 0031 — Contract confirmation with a re-baselined gate

- **Status:** complete (all gates pass; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P0 risk-sensitive control confirmation; follow-up to
  [`0030`](../0030-contract-eval-design/summary.md)
- **Task:** `factory.power.contract.v1`, failure-dense regime
- **Benchmark:** none; `factory-v0.1` unchanged

## Question

Does the clean contract effect replicate on fresh seed blocks when the gate is
set from the corrected estimate?

Experiment 0030 fixed the overlapping-block sampler, aligned train and test
(mean 129.96 vs 129.94), and measured a CVaR gain of **+13.55 [10.50, 16.95]**.
The original +15 gate was derived from the contaminated 0028 pilot and was
missed by 1.45. This run uses fresh blocks and a pre-registered **+10** gate,
chosen from 0030’s clean lower confidence bound (10.50), not from this run’s
data.

## Design

- Same failure-dense regime: load jitter 60, capacity jitter 40, period 20,
  generator capacity 5, radius 8.
- Same contract: tiers 80–150 step 5; payoff adds `T - 100` on a hit and
  subtracts 40 on a miss; CVaR alpha 0.2.
- Train blocks: even 600–998 (200 blocks).
- Test blocks: odd 601–999 (200 blocks).
- 10 episodes per block → 2,000 unique train and 2,000 unique test episodes.
- Episode seeds expand as `block * 10 + episode`; train and test are disjoint.
- Blocks 600–999 are disjoint from all prior contract runs (0–599).

## Gates

| Gate | Threshold |
|---|---|
| H1 tradeoff | train mean-optimal target > train CVaR-optimal target |
| H2 mean cost | test mean of the mean policy ≥ test mean of the CVaR policy − 5 |
| H3 tail gain | test CVaR of the CVaR policy ≥ test CVaR of the mean policy + **10** |
| H4 directional stability | mean target > CVaR target on both train and test |
| H5 no free lunch | neither policy dominates on test mean and CVaR |

H3’s +10 threshold is the only gate change from 0030. It is justified before
this run by 0030’s clean lower CI bound of 10.50.

## Predictions

- The CVaR gain will replicate near +13.5.
- The block-bootstrap 95% CI will exclude zero and include +10.
- Train and test distributions will remain matched; the zero rate will be near
  3–4% in both.
- The risk-safe policy will cost roughly 5–7 mean points.

## Analysis

- Report every tier’s train and test mean, CVaR₂₀, hit rate, and worst payoff.
- Report both selection rules and all five gates.
- Report the train/test distribution summaries.
- Report the block-bootstrap 95% CI for the CVaR gain (2,000 resamples of 200
  test blocks, seed 0).
- Report the risk premium (mean policy mean minus CVaR policy mean) separately.
- Do not change the regime, contract, blocks, or gates after the formal run.

## Kill criteria

- H3 fails (gain below +10).
- The risk premium exceeds 10 mean points.
- The mean/CVaR direction reverses.
- Train and test means differ by more than 5 points, or zero rates differ by
  more than 2 percentage points.
- The result requires post-hoc changes.

Any of these retires the contract task as a benchmark.

## Artifacts

- Code: `experiments/risk_control/contract.py`
- Formal config: `experiments/risk_control/eval_design_confirm.json`
- Raw results: `results/risk_control/contract_confirm/` (ignored)
- Summary: `docs/experiments/0031-contract-confirm/summary.md`
- Task card: `docs/tasks/power-contract.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
