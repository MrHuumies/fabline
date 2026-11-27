# Task card — assembly BOM output forecast

- **Task ID:** `factory.assembly.bom.v1`
- **Version:** 0.1.0
- **Status:** frozen in `factory-v0.5`
- **World:** `factory-0.1.0` + opt-in production tree
- **Owner:** FABLINE
- **Date:** 2026-11-27
- **RFC:** [`0031-assembly-edge.md`](../rfcs/0031-assembly-edge.md)
- **Code:** `src/fabline/harness/assembly_bom.py`
- **CLI:** `python -m fabline assembly-bom`

## Phenomenon

The assembly cell converts ingots into components and components into gears.
A planner needs a short-horizon forecast of gear output from the current cell
state: buffers, craft progress, recipe, and delivered output. The task tests
whether a model can forecast the bill-of-materials-driven output when future
operator decisions are not observable.

## Contract

- **Observation:** the standard 12-feature assembly-cell state.
- **Target:** delivered gear at `t + 5` decision steps minus delivered gear at
  `t`.
- **Logging policy:** batch policy with 30% random actions. The stochastic
  future actions create irreducible decision uncertainty; without them the
  label is deterministic given the state.
- **Episode:** 500 ticks; decision interval 10; warmup 5 steps.
- **Data:** 50 episodes, seeds 0–49; 2,000 samples.
- **Split:** episode-level 60/20/20; 1,200 / 400 / 400 samples.
- **Baselines:** mean, linear, GBDT, MLP; bootstrap CIs.
- **Metric:** test R² and MAE.

## Gates

| Gate | Threshold |
|---|---|
| H1 skill | GBDT R² ≥ 0.30 |
| H2 nonlinear | GBDT ≥ linear + 0.05 |
| H3 not saturated | GBDT R² < 0.98 |
| H4 MLP skill | MLP R² ≥ 0.20 |

Frozen v0.1–v0.4 hashes are enforced by the test suite and CI, not by the task
runner.

## Results (formal pilot, 50 episodes)

| Model | Test R² | Test MAE |
|---|---:|---:|
| mean | −0.001 | 0.780 |
| linear | 0.343 | 0.632 |
| **GBDT** | **0.503** | 0.526 |
| MLP | 0.465 | 0.588 |

All four modeling gates pass. The mean baseline is near zero, linear captures
the level, and GBDT captures the nonlinear buffer/timing interactions.

## Known pitfalls

- **Stochastic logging is required.** A deterministic batch policy makes the
  label a function of the observed state and GBDT reaches R² 1.00.
- **Episodes are correlated.** Rows within an episode share a trajectory;
  episode-level splits are mandatory.
- **No demand stream.** This is output forecasting, not demand forecasting.
- **Tabular only.** Structured baselines are not integrated for this task.
- **Label scale is small.** Report MAE alongside R²; the target is a gear
  count, not a normalized score.

## Changelog

- 2026-11-27 — task card created; formal pilot positive and frozen in
  `factory-v0.5`.
