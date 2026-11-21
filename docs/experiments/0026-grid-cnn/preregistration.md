# Experiment 0026 — Grid CNN on clear and fogged views

- **Status:** complete (H1 passes; H2 fails; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P0 architecture baseline experiment
- **Task:** `factory.throughput.predict.v1` with grid views
- **Data:** 8×16×6 grid, clear and fogged, future depot score
- **Benchmark:** none; `factory-v0.1` unchanged

## Question

Does a CNN exploit spatial grid structure better than flattened tabular
baselines, and is it more robust to a moving fog window?

The clear grid is a fixed gear line. Flattened GBDT is a strong baseline on this
small, periodic layout. The interesting comparison is therefore CNN versus a
flattened MLP, plus the relative degradation under fog. Beating GBDT is not
required to show a spatial inductive bias.

## Data

- 100 episodes; fixed gear line; 100-tick warmup; 300-tick episodes.
- 10-tick sampling; 50-tick future-score horizon.
- Grid observation: `(8, 16, 6)`.
- Fog: Manhattan radius 3 around a deterministic moving patrol; outside cells
  zeroed.
- Splits by episode seed: 70% train / 20% val / 10% test.
- Formal data seed: 1. Pilot used seed 0 with 20 episodes.

## Conditions

| Model | Input | Notes |
|---|---|---|
| linear | flattened 768 | least squares |
| GBDT | flattened 768 | 200 iterations |
| MLP | flattened 768 | 64 hidden, max 500 |
| CNN | `(6, 8, 16)` | 16/32 conv channels, global average pool |

CNN: five seeds, 50 epochs, batch 32, Adam lr 1e-3, weight decay 1e-4,
standardized targets, best validation checkpoint. GBDT/MLP are deterministic
sklearn references. Report parameter counts and bootstrap intervals.

## Gates

| Gate | Threshold |
|---|---|
| H1 CNN vs flattened MLP, clear | CNN clear R² ≥ MLP clear + 0.05 |
| H2 fog robustness | CNN degradation ≤ MLP degradation − 0.10 |
| H3 CNN vs GBDT | report; no gate |
| H4 seed consistency | CNN std ≤ 0.10 |
| H5 budget | report params, epochs, seeds, and sample counts |

“Degradation” is clear R² minus fog R² for each model.

## Predictions

- The CNN should beat the flattened MLP on the clear grid.
- Fog should hurt every model; the CNN should degrade less than the flattened
  MLP because convolution can use local spatial context.
- GBDT may remain strongest on the clear periodic layout.
- If the CNN is worse than the MLP on both views, the task does not expose a
  spatial advantage at this scale.

## Analysis plan

- Report test R² for clear and fog, with bootstrap intervals.
- Report CNN per-seed scores.
- Report degradation differences.
- Do not tune fog radius, epochs, model size, or dropout after the formal run.
- Keep `factory-v0.1` frozen.

## Kill criteria

- CNN is worse than flattened MLP on the clear grid and does not improve fog
  robustness.
- CNN is worse than flattened MLP on both views.
- The result is dominated by one seed (std > 0.15).
- The task requires post-hoc changes to show a spatial effect.

## Artifacts

- Code: `experiments/grid_vision/cnn_run.py`
- Raw results: `results/grid_vision/` (ignored)
- Summary: `docs/experiments/0026-grid-cnn/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
