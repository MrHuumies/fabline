# Experiment 0024 — Masked feature-window throughput

- **Status:** complete (all gates pass; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P0 partial-observability experiment
- **World:** factory-0.1.0; layout context + line buffers
- **Benchmark:** none; `factory-v0.1` unchanged

## Question

Does a short window of masked observations recover throughput prediction that a
single masked frame loses?

The current frame is incomplete: 60% of features are dropped and a binary mask
is provided. A single frame cannot know which dropped features were nonzero. A
window of recent masks and values may reconstruct the hidden state.

## Data

- 100 episodes; fixed gear line; 150-tick warmup; 300-tick episodes.
- 10-tick sampling; 50-tick future-score horizon.
- Observation frame: 7 layout-context features + 6 line-buffer features (13).
- Dropout: 60% per frame, independent of tick and phase, using a seeded RNG.
- Views:
  - `current`: full frame (13);
  - `single`: masked frame + mask (26);
  - `window`: last 4 masked frames + masks (104).
- Splits by episode seed: 70% train / 20% val / 10% test.
- Formal data seed: 1. The pilot used seed 0; formal uses a fresh seed.

## Baselines

- mean;
- linear;
- GBDT;
- MLP (one hidden layer, 64 units, max 500 iterations).

Test R² with 95% bootstrap CIs over test rows. One deterministic fit per model
(`random_state=0`); this is a measurement, not a seed-sweep.

## Gates

| Gate | Threshold |
|---|---|
| H1 partial damage | `single` R² is at least 0.10 below `current` for at least two baselines |
| H2 history recovery | `window` R² is at least 0.10 above `single` for at least two baselines |
| H3 no free lunch | no baseline reaches `current` R² with the window |
| H4 model split | report which models recover and which do not; no gate |
| H5 data scale | report sample counts and row-bootstrap CIs |

## Predictions

- `single` will lose substantial R² for all learned baselines.
- `window` will recover part of the loss for GBDT and linear models.
- The MLP may overfit the 104-feature window with only 800 samples; a negative
  result for the MLP is informative about sample efficiency, not a task failure.
- The label has only two values (20 and 30), so GBDT on the full view is near
  ceiling.

## Analysis plan

- Report negative results in the first paragraph.
- Report all four baselines and all three views.
- Do not tune dropout, window, or horizon after the formal run.
- Treat the pilot seed 0 as design data; formal seed 1 is the reported result.
- Keep `factory-v0.1` frozen.

## Kill criteria

- No baseline shows partial damage.
- No baseline shows history recovery.
- The result is dominated by one baseline in a way that makes the task
  uninformative.
- The task requires tuning after the formal run.

## Artifacts

- Code: `experiments/partial_observability/window_data.py`,
  `window_run.py`
- Raw results: `results/partial_observability/window/` (ignored)
- Summary: `docs/experiments/0024-masked-window/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
