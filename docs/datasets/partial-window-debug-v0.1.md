# Dataset card — partial-window-debug-v0.1

- **Status:** debug/P0 dataset
- **World version:** `factory-0.1.0`
- **License:** CC-BY-4.0 (synthetic data); code Apache-2.0
- **Generation:** `PYTHONPATH=. .venv/bin/python -m experiments.partial_observability.window_data --out experiments/partial_observability/data/window_views.npz --episodes 100 --dropout 0.6 --window 4 --seed 1`
- **Episodes:** 100
- **Samples:** 800
- **Splits:** 560 / 160 / 80 train / val / test
- **Task:** `factory.throughput.partial.v1`

## Purpose

A debug dataset for masked-feature throughput prediction. It compares a full
current frame, a single 60%-masked frame with a mask, and a window of four
masked frames.

It is not part of the frozen `factory-v0.1` benchmark.

## Contents

- `current`: 13 features (7 layout context + 6 line buffers);
- `single`: 26 features (13 masked values + 13 mask flags);
- `window`: 104 features (4 recent masked frames);
- `label`: future depot score over 50 ticks;
- split and episode id per sample.

## Generation

- fixed gear line; 150-tick warmup; 300-tick episodes;
- 10-tick sampling; 50-tick horizon;
- 60% feature dropout, masks independent of tick;
- data seed 1 (formal); pilot used seed 0.

## Results

| method | current | single masked | window |
|---|---:|---:|---:|
| linear | 0.752 | 0.164 | 0.578 |
| GBDT | 1.000 | 0.593 | 0.883 |
| MLP | 0.613 | −0.194 | 0.002 |

Test R². GBDT and linear recover about 70% of their lost R² with a window; the
MLP recovers 24% and overfits the 104-feature window.

## Caveats

- Labels take two values (20 and 30); GBDT on the full frame is at ceiling.
- Masks are independent of tick; do not seed them from time.
- 80 test rows; CIs are wide.
- One deterministic fit per model.
- Fixed periodic line; not a general partial-observability benchmark.
- Window is concatenation, not a sequence model.

## Changelog

- 2026-11-21 — card created; P0 masked-window results added.
