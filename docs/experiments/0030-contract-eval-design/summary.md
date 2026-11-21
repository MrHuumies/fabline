# Experiment 0030 — Contract evaluation with unique interleaved seeds

- **Status:** complete (H3 misses narrowly; sampling fix validated)
- **Date:** 2026-11-21
- **Type:** P0 evaluation-design experiment; follow-up to
  [`0028`](../0028-risk-contract/summary.md) and
  [`0029`](../0029-risk-contract-dense/summary.md)
- **Task:** `factory.power.contract.v1`, failure-dense regime
- **Code:** `experiments/risk_control/contract.py`
- **Formal config:** `experiments/risk_control/eval_design_formal.json`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**The instability was a sampling bug, not the mechanic.** After fixing the block
expansion and using 2,000 unique, interleaved train and test episodes, the
train/test distributions are nearly identical (mean 129.96 vs 129.94; zero rate
3.8% in both) and both select target 120 by mean and target 110 by CVaR₂₀. The
clean CVaR gain is **+13.55** with a block-bootstrap 95% CI of **[10.50, 16.95]**
— real and well above zero, but **1.45 points below the pre-registered +15
gate**, so H3 still fails operationally. The gate was derived from the 0028
pilot, which was contaminated by overlapping blocks and overstated the effect.
The contract task is now measurable; the next step is a fresh-seed confirmation
with a re-baselined gate, not another regime change.

## Correction context

The 0028/0029 runner called `evaluate_policy(episodes=N, seed=block)`, which
resets with `seed + episode`. Adjacent blocks overlapped, and train/test episode
seeds were not disjoint:

| experiment | reported train/test | unique train | unique test | overlap |
|---|---:|---:|---:|---:|
| 0028 | 400 / 200 | 49 | 29 | 80–88 |
| 0029 | 400 / 400 | 49 | 49 | 140–148 |

The earlier summaries retain their numbers as historical results of that
sampler. This experiment expands blocks as `block * 10 + episode`, calls
`evaluate_policy` one episode at a time, and rejects overlapping episode sets at
config construction.

## Design

- Failure-dense power regime: load jitter 60, capacity jitter 40, period 20,
  generator capacity 5, radius 8.
- Scripted alternator operating policy.
- Train blocks: even 200–598; test blocks: odd 201–599.
- 10 episodes per block → 2,000 unique train and 2,000 unique test episodes.
- Target tiers 80–150 step 5; payoff adds `T - 100` on a hit and subtracts 40 on
  a miss.
- CVaR alpha 0.2; offline selection over logged scores.
- Block bootstrap: 2,000 resamples of the 200 test blocks, seed 0.

## Results

| target | train mean | train CVaR₂₀ | test mean | test CVaR₂₀ | test hit |
|---:|---:|---:|---:|---:|---:|
| 80 | 109.19 | 66.40 | 109.17 | 66.03 | 0.962 |
| 85 | 113.95 | 70.20 | 113.95 | 69.94 | 0.961 |
| 90 | 118.75 | 74.20 | 118.75 | 73.95 | 0.961 |
| 95 | 123.38 | 77.33 | 123.38 | 77.09 | 0.956 |
| 100 | 128.16 | 81.20 | 128.16 | 80.97 | 0.956 |
| 105 | 131.92 | 80.01 | 131.70 | 78.67 | 0.928 |
| 110 | 136.58 | **83.33** | 136.34 | **81.88** | 0.928 |
| 115 | 137.28 | 66.84 | 137.32 | 66.79 | 0.862 |
| 120 | **141.59** | 68.35 | **141.63** | 68.33 | 0.862 |
| 125 | 136.14 | 50.20 | 135.96 | 49.88 | 0.708 |
| 130 | 139.69 | 50.20 | 139.50 | 49.88 | 0.708 |
| 135 | 127.31 | 50.20 | 126.47 | 49.88 | 0.487 |
| 140 | 129.79 | 50.20 | 128.90 | 49.88 | 0.487 |
| 145 | 111.20 | 50.20 | 112.76 | 49.88 | 0.269 |
| 150 | 112.45 | 50.20 | 114.11 | 49.88 | 0.269 |

Selected policies on test:

| policy | test mean | test CVaR₂₀ | test worst |
|---|---:|---:|---:|
| mean-optimal (120) | **141.63** | 68.33 | −40.00 |
| CVaR-optimal (110) | 136.34 | **81.88** | −40.00 |

The risk-safe policy gives up 5.29 mean points for 13.55 CVaR points.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 tradeoff | train mean target > train CVaR target | **pass**, 120 > 110 |
| H2 mean cost | mean policy test mean ≥ CVaR policy − 5 | **pass**, 141.63 vs 131.34 |
| H3 tail gain | CVaR policy test CVaR ≥ mean policy + 15 | **fail**, +13.55 |
| H4 directional stability | mean target > CVaR target on train and test | **pass**, both 120 > 110 |
| H5 no free lunch | neither policy dominates | **pass** |

Block-bootstrap 95% CI for the CVaR gain: **[10.50, 16.95]**. The interval
excludes zero and includes the +15 gate; the point estimate is below it.

## Distribution alignment

| split | mean | std | zero rate | q05 | q20 | median |
|---|---:|---:|---:|---:|---:|---:|
| train | 129.96 | 30.33 | 3.8% | 100 | 120 | 130 |
| test | 129.94 | 30.51 | 3.8% | 100 | 120 | 130 |

The two sets are matched to within 0.02 mean points. This is the strongest
evidence that the earlier train/test shift was a sampler artifact.

## Interpretation

- **The sampler was the root cause.** Unique, interleaved seeds remove the
  train/test distribution gap that dominated 0028 and 0029.
- **The clean effect is smaller than the contaminated pilot.** The real CVaR
  gain is about 13.5 points, not 26. The original +15 gate came from the
  overlapping pilot and was too high for the clean design.
- **The effect is real.** The block-bootstrap lower bound is 10.5, well above
  zero, and the direction is stable across train and test.
- **The trade is now interpretable.** The risk-safe contract costs 5.3 mean
  points for 13.6 CVaR points, a much better trade than the 7.5-for-2.5 seen in
  the contaminated 0029 test block.
- **Do not lower the gate in this experiment.** H3 fails as pre-registered. The
  correct follow-up is a fresh-seed confirmation with a gate chosen from this
  clean estimate.

## Caveats

- One world, one contract mechanism, one failure-dense regime, one miss penalty,
  one alpha.
- Offline selection; no online learning or context.
- The block bootstrap treats 200 blocks as exchangeable; it does not model
  long-range seed drift.
- 2,000 test episodes, but the tail is still dominated by zero-score episodes
  (3.8%).
- The target does not affect the world; this is a commitment decision, not
  sequential control.
- The +15 gate is retained in the result; it is not renegotiated post-hoc.

## Next

A confirmation run on fresh blocks (for example 600–999) with a pre-registered
gate of **+10** CVaR. If that passes, the contract task becomes a usable
risk-sensitive benchmark with a documented effect size of about +13.5. If it
fails, retire the task.

Do not change the regime, contract, or gate in this experiment.

## Artifacts

- Code: `experiments/risk_control/contract.py`
- Formal config: `experiments/risk_control/eval_design_formal.json`
- Raw results: `results/risk_control/contract_eval_design/` (ignored)
- Task card: `docs/tasks/power-contract.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
