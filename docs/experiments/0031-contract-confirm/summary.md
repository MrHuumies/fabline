# Experiment 0031 — Contract confirmation with a re-baselined gate

- **Status:** complete (all gates pass)
- **Date:** 2026-11-21
- **Type:** P0 risk-sensitive control confirmation; follow-up to
  [`0030`](../0030-contract-eval-design/summary.md)
- **Task:** `factory.power.contract.v1`, failure-dense regime
- **Code:** `experiments/risk_control/contract.py`
- **Formal config:** `experiments/risk_control/eval_design_confirm.json`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**The clean contract effect replicates on fresh seed blocks and clears the
re-baselined gate.** On blocks 600–999 (2,000 unique train and 2,000 unique test
episodes), both splits select target 120 by mean and target 110 by CVaR₂₀. The
test CVaR gain is **+17.05**, block-bootstrap 95% CI **[13.25, 21.15]**, against
a pre-registered +10 gate. The mean premium is 4.59. All five gates pass. Train
and test remain matched (mean 128.62 vs 129.56; zero rate 4.6% vs 3.5%). Together
with 0030 (+13.55 [10.50, 16.95]), the contract task now has a stable,
replicated risk-sensitive effect of roughly +13 to +17 CVaR points for about 5
mean points.

## Design

- Failure-dense regime: load jitter 60, capacity jitter 40, period 20,
  generator capacity 5, radius 8.
- Scripted alternator operating policy.
- Train blocks: even 600–998; test blocks: odd 601–999.
- 10 episodes per block → 2,000 unique train and 2,000 unique test episodes.
- Episode seeds expand as `block * 10 + episode`; train and test are disjoint.
- Target tiers 80–150 step 5; payoff adds `T - 100` on a hit and subtracts 40 on
  a miss.
- CVaR alpha 0.2; offline selection over logged scores.
- H3 gate +10, chosen from 0030’s clean lower CI bound (10.50) before this run.

## Results

| target | train mean | train CVaR₂₀ | test mean | test CVaR₂₀ | test hit |
|---:|---:|---:|---:|---:|---:|
| 80 | 107.69 | 60.15 | 108.86 | 67.72 | 0.965 |
| 85 | 112.42 | 63.80 | 113.66 | 71.72 | 0.964 |
| 90 | 117.18 | 67.60 | 118.48 | 75.83 | 0.964 |
| 95 | 121.54 | 69.39 | 123.12 | 79.05 | 0.959 |
| 100 | 126.24 | 72.90 | 127.92 | 83.03 | 0.959 |
| 105 | 129.91 | 71.24 | 131.41 | 80.47 | 0.930 |
| 110 | 134.50 | **74.17** | 136.06 | **83.72** | 0.930 |
| 115 | 135.81 | 60.75 | 136.39 | 65.39 | 0.852 |
| 120 | **140.10** | 62.20 | **140.65** | 66.67 | 0.852 |
| 125 | 134.48 | 44.80 | 135.68 | 51.23 | 0.710 |
| 130 | 138.00 | 44.80 | 139.22 | 51.23 | 0.710 |
| 135 | 124.62 | 44.80 | 124.85 | 51.23 | 0.470 |
| 140 | 127.02 | 44.80 | 127.20 | 51.23 | 0.470 |
| 145 | 109.91 | 44.80 | 110.05 | 51.23 | 0.241 |
| 150 | 111.17 | 44.80 | 111.25 | 51.23 | 0.241 |

Selected policies on test:

| policy | test mean | test CVaR₂₀ | test worst |
|---|---:|---:|---:|
| mean-optimal (120) | **140.65** | 66.67 | −40.00 |
| CVaR-optimal (110) | 136.06 | **83.72** | −40.00 |

Mean premium: 4.59. CVaR gain: 17.05.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 tradeoff | train mean target > train CVaR target | **pass**, 120 > 110 |
| H2 mean cost | mean policy test mean ≥ CVaR policy − 5 | **pass**, 140.65 vs 131.06 |
| H3 tail gain | CVaR policy test CVaR ≥ mean policy + 10 | **pass**, +17.05 |
| H4 directional stability | mean target > CVaR target on train and test | **pass**, both 120 > 110 |
| H5 no free lunch | neither policy dominates | **pass** |

Block-bootstrap 95% CI for the CVaR gain: **[13.25, 21.15]**.

## Distribution alignment

| split | mean | std | zero rate | q05 | q20 | median |
|---|---:|---:|---:|---:|---:|---:|
| train | 128.62 | 32.60 | 4.6% | 90 | 120 | 130 |
| test | 129.56 | 29.24 | 3.5% | 100 | 120 | 130 |

The mean gap is 0.94 and the zero-rate gap is 1.1 percentage points, inside the
pre-registered tolerances.

## Comparison with 0030

| experiment | blocks | mean premium | CVaR gain | 95% CI |
|---|---|---:|---:|---:|
| 0030 | 200–599 | 5.29 | +13.55 | [10.50, 16.95] |
| 0031 | 600–999 | 4.59 | +17.05 | [13.25, 21.15] |

The intervals overlap. The replicated effect is roughly +13 to +17 CVaR points
for about 5 mean points. The direction and selected targets are identical.

## Interpretation

- **The contract task is now a usable P0 risk-sensitive benchmark.** Two
  independent, clean seed ranges produce the same qualitative and quantitative
  result.
- **The risk-return trade is modest and consistent.** A conservative contract
  gives up about 5 mean points for 13–17 tail points.
- **The original +15 gate failure in 0030 was a threshold problem, not a
  mechanic problem.** The gate came from the contaminated 0028 pilot; the clean
  effect is smaller but stable.
- **The sampling fix was essential.** Without unique, interleaved seeds, the
  train/test tail estimates were unreliable.
- **The task is offline selection with a fixed operating policy.** It is not
  online learning, not context-dependent, and not sequential control.

## Caveats

- One world, one failure-dense regime, one contract mechanism, one miss penalty,
  one alpha.
- The scripted alternator is fixed; the contract does not adapt the operating
  policy.
- Offline selection over logged scores; no exploration or online regret.
- Block bootstrap assumes exchangeable blocks; it does not model long-range seed
  drift.
- 2,000 test episodes, but the tail is dominated by zero-score episodes
  (3.5%).
- The target does not affect the world; this is a commitment decision.
- Not part of frozen `factory-v0.1`.

## Next

- Document the contract task as a P0 benchmark candidate with the replicated
  effect size (+13 to +17 CVaR, ~5 mean premium).
- P0 coverage is now complete: calibration, partial observability,
  representative architecture baselines, and risk-sensitive control.
- The next project-scope decision is consolidation/release, multi-agent
  workers, or a second world; each needs its own pre-registration.

## Artifacts

- Code: `experiments/risk_control/contract.py`
- Formal config: `experiments/risk_control/eval_design_confirm.json`
- Raw results: `results/risk_control/contract_confirm/` (ignored)
- Task card: `docs/tasks/power-contract.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
