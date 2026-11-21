# Experiment 0027 — End-to-end MPNN on the entity graph

- **Status:** complete (H1 passes; H2 and H4 fail)
- **Date:** 2026-11-21
- **Type:** P0 architecture baseline experiment
- **Task:** `factory.throughput.predict.v1`, entity graph view
- **Code:** `experiments/graph_baselines/gnn_run.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**Relational structure transfers; the end-to-end MPNN does not yet beat the
hand-built graph feature baseline.** On the held-out `extra_gear` combination,
flattened views collapse (linear −5.57, GBDT −11.11, MLP −3.19 test R²), the
one/two-hop feature baseline `graph_mp` reaches 0.348, and the end-to-end MPNN
reaches 0.258 [0.168, 0.348] over five seeds. H1 passes by +3.45 over the
flattened MLP, H2 fails: the MPNN is 0.09 below `graph_mp`, outside the 0.05
parity margin. Seed variance is 0.111, just over the 0.10 consistency gate. The
result is a scale boundary: learned message passing recovers most of the
compositional transfer, but 557 training rows favor pooled features plus GBDT.

## Data

- Shared `factory-v0.1` audit dataset; 852 samples.
- Train / val / test / shift = 557 / 75 / 110 / 110.
- Train scenarios `ingot`, `gear`, `extra_ingot`; val `ingot`/`gear`; test
  held-out `extra_gear`; shift `shift_gear`.
- Entity graph: 16 node features, padded mask, dense adjacency.
- Label: future depot score over 50 ticks.

## Results

Test and shift R²:

| model | test R² | shift R² |
|---|---:|---:|
| linear (flattened) | −5.570 | 0.424 |
| GBDT (flattened) | −11.111 | 1.000 |
| MLP (flattened) | −3.188 | 0.414 |
| `graph_mp` | **0.348** | 1.000 |
| MPNN | 0.258 [0.168, 0.348] | 0.690 [0.623, 0.764] |

MPNN per-seed test R²: 0.163, 0.438, 0.297, 0.121, 0.271 (mean 0.258, std
0.111). 6,913 parameters; two message-passing layers, 32 hidden; five seeds, 50
epochs.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 relational gain | MPNN ≥ flattened MLP + 0.10 | **pass**, +3.45 |
| H2 graph_mp parity | MPNN ≥ `graph_mp` − 0.05 | **fail**, 0.258 vs 0.348 |
| H3 shift behavior | report | MPNN 0.690; `graph_mp` 1.000; flattened 0.41–1.00 |
| H4 seed consistency | MPNN std ≤ 0.10 | **fail**, 0.111 |
| H5 budget | report | 6,913 params, 5 seeds, 50 epochs |

## Interpretation

- **The compositional split is the real test, and it is brutal for flattened
  views.** Negative R² means the held-out combination is outside the tabular
  models' interpolation range. This reproduces the documented limitation.
- **Relational aggregation is what transfers.** Both `graph_mp` and the MPNN
  are positive on test while every flattened model is negative. The graph
  structure, not model capacity, carries the signal.
- **`graph_mp` still wins at this scale.** One/two-hop normalized aggregation
  followed by GBDT is a strong prior for 557 training rows. The end-to-end MPNN
  must learn the same aggregation, and it does not close the 0.09 gap in 50
  epochs.
- **MPNN seed variance is real.** 0.121 to 0.438 across five seeds. The 0.111
  std misses the consistency gate and means single-seed comparisons would be
  misleading.
- **Shift is saturated for `graph_mp`.** 1.000 shift R² is a ceiling, not
  evidence; do not rank models on shift.

## Caveats

- One dataset, one split, one graph encoding, one MPNN size.
- 110 test rows; bootstrap intervals are wide.
- `graph_mp` uses GBDT on pooled features; the comparison is end-to-end learned
  aggregation versus fixed aggregation plus a strong tabular head, not GNN
  versus no GNN.
- Five seeds, 50 epochs, no hyperparameter search. A tuned MPNN could close the
  gap; that would be a new experiment.
- Shift results are not informative for `graph_mp`.

## Next

- The P0 architecture slice is complete: sequence (0025), grid CNN (0026), and
  graph MPNN (0027).
- Next P0 item is risk-sensitive control; it is a different task family and
  needs its own pre-registration.
- Keep `factory-v0.1` frozen.

## Artifacts

- Code: `experiments/graph_baselines/gnn_run.py`
- Raw results: `results/graph_baselines/` (ignored)
- Task card: `docs/tasks/throughput.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
