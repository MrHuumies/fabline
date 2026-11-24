# Task card — counterfactual entity removal

- **Task ID:** `factory.causal.remove.v1`
- **Version:** 0.1.0
- **Status:** P3 causal task; formal positive (target GBDT R² 0.910);
  included in `factory-v0.2`
- **World:** factory-0.1.0, 16×8 gear line, no faults
- **Owner:** FABLINE
- **Date:** 2026-11-24

## Phenomenon

Given a state, remove one of two same-type entities and predict which removal
reduces future production more. Type-only features cannot distinguish the pair;
target positions and buffers can. The task tests interventional prediction, not
observational correlation.

## Contract

- **State:** 18 vector features at sample tick 150/250/350.
- **Targets:** two entities of the same type, sampled from the non-depot set.
- **Intervention:** remove each target in a clone, run 100 ticks.
- **Label:** `delta_first - delta_second` (signed score difference).
- **Views:** `type_only` = state + target type; `target` = state + both target
  feature vectors (type, position, input/output buffers).
- **Splits:** episode-grouped 70/20/10.

## Baselines

| Baseline | Rule |
|---|---|
| mean | constant label |
| linear | ridge |
| GBDT | histogram gradient boosting |
| MLP | small neural regressor |

## Metrics

R² and MAE on the test split.

## Gates

| Gate | Threshold |
|---|---|
| H1 target skill | target GBDT R² ≥ 0.30 |
| H2 causal signal | target GBDT ≥ type-only + 0.20 |
| H3 linear/MLP | report; no hard gate |
| H4 frozen benchmark | unchanged |

## Known pitfalls

- Same-type pairs; type cannot distinguish them by construction.
- Only 120 rows per block; CIs are wide.
- One sample tick set and one horizon.
- The label is a score difference, not a full counterfactual trajectory.
- Not part of `factory-v0.1`.

## Results (0079)

Three 40-episode blocks; target GBDT R² `0.986, 0.753, 0.992` (mean 0.910);
type-only GBDT `−0.234, −0.594, −0.072` (mean −0.300). H1/H2/H4 pass; linear
target 0.598, MLP 0.157. See
[`experiments/0079-causal-removal`](../experiments/0079-causal-removal/summary.md).

On the `factory-v0.2` seeds (64,000 / 64,100 / 64,200), target GBDT mean R² is
0.987 and type-only is −0.074; H1/H2 still pass. The benchmark point estimates
differ from the pilot but preserve the ordering.

## Changelog

- 2026-11-24 — task card created; pairwise intervention and gates defined.
- 2026-11-24 — formal positive; target GBDT 0.910 vs type-only −0.300.
