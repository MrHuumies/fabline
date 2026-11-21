# Experiment 0027 — End-to-end MPNN on the entity graph

- **Status:** complete (H1 passes; H2/H4 fail; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P0 architecture baseline experiment
- **Task:** `factory.throughput.predict.v1`, entity graph view
- **Data:** shared `factory-v0.1` audit dataset (852 samples; compositional split)
- **Benchmark:** none; `factory-v0.1` unchanged

## Question

Does an end-to-end message-passing network generalize to the held-out
`extra_gear` combination better than flattened tabular views, and does it match
the existing `graph_mp` feature baseline?

The known limitation is that flattened entity views fail to generalize to the
held-out combination while `graph_mp` reaches 0.348 test R². An end-to-end MPNN
is the natural test of whether learned relational structure closes that gap.

## Data

- Shared dataset `results/fabline-audit/factory-v0.1/dataset`.
- 852 samples; train / val / test / shift = 557 / 75 / 110 / 110.
- Scenario split: train `ingot`/`gear`/`extra_ingot`; val `ingot`/`gear`;
  test held-out `extra_gear`; shift `shift_gear`.
- Entity graph: 16 node features, padded mask, dense adjacency.
- Label: future depot score over 50 ticks.

## Conditions

| Model | Input | Notes |
|---|---|---|
| linear | flattened entities | least squares |
| GBDT | flattened entities | 200 iterations |
| MLP | flattened entities | 64 hidden, max 500 |
| graph_mp | message-passing features | one/two-hop aggregation + GBDT |
| MPNN | entity graph | 2 message-passing layers, 32 hidden |

MPNN: five seeds, 50 epochs, batch 32, Adam lr 1e-3, weight decay 1e-4,
standardized targets, best validation checkpoint, mean-pooled node states.
Report parameter counts and bootstrap intervals. `graph_mp` is deterministic.

## Gates

| Gate | Threshold |
|---|---|
| H1 relational gain | MPNN test R² ≥ flattened MLP test R² + 0.10 |
| H2 graph_mp parity | MPNN test R² ≥ `graph_mp` test R² − 0.05 |
| H3 shift behavior | report shift R² for every model; no gate |
| H4 seed consistency | MPNN test std ≤ 0.10 |
| H5 budget | report params, epochs, seeds, and sample counts |

## Predictions

- Flattened views will fail on the held-out combination (negative R²), matching
  the documented limitation.
- MPNN will beat the flattened MLP by a wide margin; the relational structure is
  the only thing that transfers.
- MPNN may trail `graph_mp`: `graph_mp` pools one/two-hop aggregates and hands
  them to GBDT, which is strong on 557 training rows. An end-to-end model must
  learn the same aggregation from scratch.
- Shift is likely saturated; do not use it to rank models.

## Analysis plan

- Report test and shift R² with bootstrap intervals.
- Report per-seed MPNN scores.
- Compare against flattened and `graph_mp` baselines on the same split.
- Do not tune layers, hidden size, epochs, or lr after the formal run.
- Keep `factory-v0.1` frozen.

## Kill criteria

- MPNN does not beat the flattened MLP by 0.10.
- MPNN is more than 0.05 below `graph_mp`.
- The result is dominated by one seed (std > 0.15).
- The result requires post-hoc changes to the graph representation or split.

## Artifacts

- Code: `experiments/graph_baselines/gnn_run.py`
- Raw results: `results/graph_baselines/` (ignored)
- Summary: `docs/experiments/0027-graph-mpnn/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
