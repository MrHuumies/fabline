# Experiment 0026 — Grid CNN on clear and fogged views

- **Status:** complete (H1 passes; H2 fails)
- **Date:** 2026-11-21
- **Type:** P0 architecture baseline experiment
- **Task:** throughput prediction with grid views
- **Code:** `experiments/grid_vision/cnn_run.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**The CNN nearly solves the clear grid but is less fog-robust than a flattened
MLP.** Clear-grid R² is 0.997 for the CNN versus 0.772 for the flattened MLP,
so H1 passes. Under a moving fog window, the CNN falls to 0.509 while the MLP
holds at 0.544; the CNN degrades by 0.488 versus 0.228 for the MLP, so H2 fails.
GBDT remains at 1.000 clear and 0.543 fogged. The result is a genuine
spatial-inductive-bias finding: convolution exploits local layout when visible,
but loses more when the visibility window removes the spatial context it needs.

## Data

- 100 episodes; fixed gear line; 100-tick warmup; 300-tick episodes.
- 10-tick sampling; 50-tick future-score horizon.
- Grid: `(8, 16, 6)`.
- Fog: Manhattan radius 3 around a deterministic moving patrol.
- 1,600 samples; train / val / test = 1,120 / 320 / 160.
- Formal data seed 1; pilot seed 0.

## Results

Test R²:

| model | clear | fog | degradation |
|---|---:|---:|---:|
| linear | 0.829 | 0.540 | 0.289 |
| GBDT | 1.000 | 0.543 | 0.457 |
| MLP | 0.772 | 0.544 | 0.228 |
| CNN | **0.997** [0.995, 0.998] | 0.509 [0.505, 0.512] | **0.488** |

CNN: 16/32 conv channels, global average pool, five seeds, 50 epochs,
standardized targets, best validation checkpoint.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 CNN vs MLP, clear | CNN ≥ MLP + 0.05 | **pass**, +0.225 |
| H2 fog robustness | CNN degradation ≤ MLP − 0.10 | **fail**, 0.488 vs 0.228 |
| H3 CNN vs GBDT | report | clear 0.997 vs 1.000; fog 0.509 vs 0.543 |
| H4 seed consistency | CNN std ≤ 0.10 | **pass**, std ≈ 0.002 |
| H5 budget | report | 5 seeds, 50 epochs, 160 test rows |

## Interpretation

- **Spatial structure is real.** The CNN nearly matches GBDT on the clear grid
  and beats the flattened MLP by a wide margin.
- **Fog is a harder distribution for the CNN.** The moving window removes the
  local layout the convolution relies on. The MLP, which sees a global pixel
  summary, degrades less.
- **All models converge near 0.54 under fog.** The fog strips most of the
  predictive signal; the differences between models shrink.
- **GBDT is still the clear-grid tabular ceiling.** 1.000 versus 0.997 is not a
  meaningful win, but it shows the task is easy when fully visible.
- **This is one fog regime.** A larger radius, random masks, or fog-aware
  training could change the robustness ordering; that would be a new experiment.

## Caveats

- Fixed gear line; not the compositional `factory-v0.1` split.
- One fog radius and patrol schedule; no random fog.
- 160 test rows; CIs are bootstrap over rows/seeds.
- CNN is small and fully convolutional with global average pooling.
- No data augmentation or fog-aware training.
- Do not tune fog radius or epochs against this result.

## Next

1. **GNN/MPNN on the entity graph** — relational structure and variable
   entities.
2. Optional: fog-aware training or random fog, as a robustness follow-up.
3. Keep `factory-v0.1` frozen.

## Artifacts

- Task card: `docs/tasks/throughput.md` (P0 debug section)
- Dataset card: `docs/datasets/grid-view-debug-v0.1.md`
- Raw results: `results/grid_vision/` (ignored)
- Run: `PYTHONPATH=. .venv/bin/python -m experiments.grid_vision.cnn_run --data /tmp/grid.npz --out results/grid_vision --episodes 100 --data-seed 1 --epochs 50`
