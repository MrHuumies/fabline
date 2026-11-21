# Experiment 0029 — Reliability contract in a failure-dense power regime

- **Status:** complete (H3 fails; second negative)
- **Date:** 2026-11-21
- **Type:** P0 risk-sensitive control experiment; follow-up to
  [`0028`](../0028-risk-contract/summary.md)
- **Task:** `factory.power.contract.v1` under a failure-dense regime
- **Code:** `experiments/risk_control/contract.py`
- **Formal config:** `experiments/risk_control/regime_d_formal.json`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**A failure-dense regime does not fix the tail-stability problem.** Train
selects target 120 by mean (136.40) and target 110 by CVaR₂₀ (74.38), and the
direction holds on test, so H1, H2, H4, and H5 pass. On the formal test block,
the CVaR-optimal policy gains only **+2.5** over the mean-optimal policy (77.5 vs
75.0), below the +15 gate; H3 fails again. The test block is more benign than
train — mean 131.5 vs 126.15, zero rate 3.0% vs 5.8%, 5th percentile 90 vs 0 —
so the tail the contract is meant to price did not appear. This is the second
failure of the same gate under a deliberately harsher regime. The contract task
is not a stable risk-sensitive benchmark at this scale.

## Regime

| Setting | 0028 | 0029 |
|---|---:|---:|
| Generator capacity | 5 | 5 |
| Generator radius | 8 | 8 |
| Load jitter | 30 | **60** |
| Capacity jitter | 20 | **40** |
| Variation period | 20 | 20 |

The 60/40 regime was chosen from a design pilot (seeds 0–39) because it produced
a heavier lower tail while keeping the line productive. It is a scope condition,
not the canonical regime.

## Contract

- Target tiers: 80, 85, …, 150 (step 5).
- Payoff for target `T`:
  - production score `s`;
  - bonus `T - 100` when `s >= T`;
  - miss penalty 40 when `s < T`.
- The target does not affect the world; it changes only the payoff.
- Selection is offline over logged scores, not online bandit learning.

## Data

- Train: seeds 100–139, 10 episodes each = 400 scores.
- Test: seeds 140–179, 10 episodes each = 400 scores.
- Design pilot: seeds 0–39 under the same regime; not formal evidence.
- Formal seeds are disjoint from the 0028 formal seeds (40–99) and the pilot.

## Results

| target | train mean | train CVaR₂₀ | test mean | test CVaR₂₀ | test hit |
|---:|---:|---:|---:|---:|---:|
| 80 | 105.00 | 54.25 | 110.90 | 69.50 | 0.970 |
| 85 | 109.71 | 57.81 | 115.75 | 73.75 | 0.970 |
| 90 | 114.42 | 61.38 | 120.60 | 78.00 | 0.970 |
| 95 | 119.14 | 64.94 | 124.58 | 77.88 | 0.945 |
| 100 | 123.85 | 68.50 | 129.30 | 81.50 | 0.945 |
| 105 | 128.34 | 70.94 | 132.00 | 75.00 | 0.900 |
| 110 | 133.03 | **74.38** | 136.50 | 77.50 | 0.900 |
| 115 | 132.21 | 50.31 | 139.62 | 73.12 | 0.875 |
| 120 | **136.40** | 51.25 | **144.00** | 75.00 | 0.875 |
| 125 | 130.03 | 40.00 | 138.95 | 52.50 | 0.730 |
| 130 | 133.40 | 40.00 | 142.60 | 52.50 | 0.730 |
| 135 | 111.84 | 40.00 | 132.56 | 52.50 | 0.547 |
| 140 | 113.55 | 40.00 | 135.30 | 52.50 | 0.547 |
| 145 | 104.85 | 40.00 | 114.03 | 52.50 | 0.265 |
| 150 | 105.95 | 40.00 | 115.35 | 52.50 | 0.265 |

Selected policies on test:

| policy | test mean | test CVaR₂₀ | test worst |
|---|---:|---:|---:|
| mean-optimal (120) | **144.00** | 75.00 | −40.00 |
| CVaR-optimal (110) | 136.50 | **77.50** | −40.00 |

The risk-safe policy gives up 7.50 mean points for 2.50 CVaR points.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 tradeoff | train mean target > train CVaR target | **pass**, 120 > 110 |
| H2 mean cost | mean policy test mean ≥ CVaR policy − 5 | **pass**, 144.0 vs 131.5 |
| H3 tail gain | CVaR policy test CVaR ≥ mean policy + 15 | **fail**, +2.50 |
| H4 directional stability | mean target > CVaR target on train and test | **pass** |
| H5 no free lunch | neither policy dominates | **pass** |

## Distribution shift

| split | mean | std | zero rate | q05 | q20 | median |
|---|---:|---:|---:|---:|---:|---:|
| train | 126.15 | 34.95 | 5.8% | 0.0 | 120 | 130 |
| test | 131.50 | 28.71 | 3.0% | 90.0 | 120 | 140 |

The test seeds are better on every summary: higher mean, lower variance, fewer
zeros, and a much higher 5th percentile. The pilot's heavier tail did not carry
over to the formal block.

## Exploratory tail diagnostic (not gated)

| alpha | train gain (110 vs 120) | test gain (110 vs 120) |
|---:|---:|---:|
| 0.05 | 0.00 | 0.00 |
| 0.10 | +18.75 | 0.00 |
| 0.20 | +23.12 | +2.50 |
| 0.30 | +12.08 | −1.67 |

The train tail gain is concentrated at alpha 0.1–0.3; the test block has no
comparable gain at any alpha. This is a distribution problem, not an alpha
choice.

## Interpretation

- **The direction is robust; the magnitude is not.** Mean selects a higher
  target than CVaR on both train and test, in both 0028 and 0029.
- **A harsher regime did not stabilize the tail.** The formal block simply drew
  better episodes than the design pilot and the train block.
- **Seed-block variation dominates.** Contiguous seed ranges differ in mean,
  variance, and zero rate. A 400-episode estimate of a 20% tail is not stable
  when failures cluster by seed.
- **Two failures of the same gate are enough.** Further changes to jitter,
  capacity, tiers, or penalty would be tuning against the gate. Stop here.
- **This is a negative result about the benchmark, not about risk
  sensitivity.** The tradeoff exists; the measurement is not yet reliable.

## Caveats

- One world, one contract mechanism, one miss penalty, one alpha, one
  failure-dense regime.
- Offline selection; no online learning or context.
- The test block is contiguous seeds; no interleaving or stratification.
- 400 test episodes, but the tail is dominated by a small number of zero-score
  episodes.
- The target does not affect the world; this is a commitment decision, not
  sequential control.

## Next

The contract task should not get another regime tweak. The credible options are:

1. **Evaluation-design experiment:** interleaved or stratified seed assignment,
   many more episodes, and a pre-registered block bootstrap. This tests whether
   the task can be measured, without changing the mechanic.
2. **A different risk mechanic:** per-episode independent failures, so the tail
   is sampled within a block rather than clustered by seed.
3. **Retire the contract task as a benchmark** and keep it as a documented
   negative example.

Option 1 is the smallest change and directly addresses the diagnosed cause.
Option 2 is the better long-term mechanic if risk-sensitive control remains a
P0 goal.

## Artifacts

- Code: `experiments/risk_control/contract.py`
- Formal config: `experiments/risk_control/regime_d_formal.json`
- Raw results: `results/risk_control/contract_regime_d/` (ignored)
- Task card: `docs/tasks/power-contract.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
