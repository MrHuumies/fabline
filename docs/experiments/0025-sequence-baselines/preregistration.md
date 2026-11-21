# Experiment 0025 — Sequence baselines on masked-window throughput

- **Status:** complete (H1/H2 fail; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P0 architecture baseline experiment
- **Task:** `factory.throughput.partial.v1`
- **Data:** same masked-window dataset as experiment 0024, formal seed 1
- **Benchmark:** none; `factory-v0.1` unchanged

## Question

Do sequence architectures recover more masked-window signal than a
same-budget flattened MLP?

The current representation is four masked frames (4 × 26 = 104 features).
Experiment 0024 showed that a window recovers about 70% of the lost R² for
linear/GBDT, while an sklearn MLP overfits. This experiment replaces the
flattened dense model with explicit sequence models.

## Data

- 100 episodes; fixed gear line; 800 samples; 560 / 160 / 80 train / val / test.
- 60% feature dropout, masks independent of tick.
- Sequence: four recent frames of 26 features (13 values + 13 mask flags).
- Label: future depot score over 50 ticks.
- Data seed 1; no new data generation.

## Conditions

| Model | Input | Notes |
|---|---|---|
| flat_mlp | 104 flattened features | 64 hidden units |
| gru | 4 × 26 | 32 hidden units, last state |
| transformer | 4 × 26 | 32 dim, 1 layer, 4 heads, FF 64 |
| temporal_cnn | 4 × 26 | 32 channels, kernel 2 |
| gbdt_reference | 104 flattened features | deterministic tabular reference |

Five seeds for neural models; 50 epochs; batch 32; Adam lr 1e-3; weight decay
1e-4; best validation checkpoint. GBDT uses 200 iterations and `random_state=0`.
Report parameter counts.

## Gates

| Gate | Threshold |
|---|---|
| H1 sequence gain | best sequence mean R² ≥ flat MLP + 0.10 |
| H2 no regression | every sequence mean R² ≥ flat MLP − 0.05 |
| H3 seed consistency | best sequence std ≤ 0.10 |
| H4 full-view context | report the full-view reference; no gate |
| H5 budget | report params, epochs, and seeds |

## Predictions

- GRU and Transformer should beat the flattened MLP; the sequence structure
  matches the data.
- The temporal CNN may be competitive with fewer parameters.
- GBDT may remain strong; small data and a two-value label favor it.
- The MLP may overfit; sequence models may be more sample-efficient.

## Analysis plan

- Report mean test R² over five seeds with 95% bootstrap intervals.
- Report per-seed scores.
- Do not tune epochs, model sizes, or dropout after the run.
- Keep the task and data fixed.

## Kill criteria

- No sequence model beats the flat MLP by 0.10.
- The best sequence model is worse than the flat MLP.
- The result is dominated by one seed (std > 0.15).
- The result requires post-hoc model or data changes.

## Artifacts

- Code: `experiments/architecture_baselines/sequence_run.py`
- Raw results: `results/architecture_baselines/sequence/` (ignored)
- Summary: `docs/experiments/0025-sequence-baselines/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
