# Dataset card — grid-view-debug-v0.1

- **Status:** debug/P0 dataset
- **World version:** `factory-0.1.0`
- **License:** CC-BY-4.0 (synthetic data); code Apache-2.0
- **Generation:** `PYTHONPATH=. .venv/bin/python -m experiments.grid_vision.data --out experiments/grid_vision/data/grid_views.npz --episodes 100 --fog-radius 3 --seed 1`
- **Episodes:** 100
- **Samples:** 1,600
- **Splits:** 1,120 / 320 / 160 train / val / test
- **Task:** `factory.throughput.predict.v1`

## Purpose

A debug dataset for clear versus fogged grid throughput prediction. It supports
the P0 CNN baseline comparison and future spatial-model work.

It is not part of the frozen `factory-v0.1` benchmark.

## Contents

- `clear`: `(8, 16, 6)` grid observation;
- `fog`: same shape, cells outside a moving Manhattan radius 3 zeroed;
- `label`: future depot score over 50 ticks;
- split and episode id per sample.

## Generation

- fixed gear line; 100-tick warmup; 300-tick episodes;
- 10-tick sampling; 50-tick horizon;
- fog patrol deterministic from tick;
- data seed 1 (formal); pilot used seed 0.

## Results

Test R²:

| model | clear | fog |
|---|---:|---:|
| linear | 0.829 | 0.540 |
| GBDT | 1.000 | 0.543 |
| MLP | 0.772 | 0.544 |
| CNN | 0.997 | 0.509 |

The CNN nearly solves the clear grid but degrades more under fog than the
flattened MLP.

## Caveats

- Fixed gear line, one fog radius and patrol; not a general spatial benchmark.
- 160 test rows; CIs are wide.
- CNN seed variance is small; do not overread small differences.
- Fog is deterministic; random fog is a future variant.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-21 — card created; P0 CNN results added.
