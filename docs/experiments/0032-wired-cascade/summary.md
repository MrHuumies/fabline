# Experiment 0032 — Wired-power cascade prediction

- **Status:** complete (H1/H3/H4 pass)
- **Date:** 2026-11-21
- **Type:** P1 graph-mechanic experiment
- **Mechanic:** wired power topology and deterministic wire faults (RFC 0007,
  ADR 0017)
- **Task:** `factory.power.cascade.v1` (debug/P1, not in `factory-v0.1`)
- **Code:** `experiments/wired_power/cascade_data.py`,
  `experiments/wired_power/cascade_size.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Explicit wire-graph message passing predicts cascade size better than
flattened and grid views.** On 1,936 samples from 200 fresh layouts, `graph_mp`
reaches **R² 0.431**, the vector GBDT 0.264, the wire-grid CNN 0.223, and the
residual GNN 0.329. The paired layout-bootstrap difference between `graph_mp`
and vector GBDT is **+0.167 [0.048, 0.309]**, clearing the +0.05 gate at the
point estimate; the lower interval bound sits just below the gate. H1, H3, and
H4 pass. The GNN is positive over vector but trails `graph_mp`; the graph
diameter (mean ~18) still limits long-range propagation. The label is
zero-inflated (51.3% loop faults disconnect nobody), so the result is about
ranking non-zero cascades, not a balanced classifier.

## Data

- 200 layouts, seeds 500–699; up to 10 sampled fault wires per layout.
- 1,936 samples; train / val / test = 1,359 / 380 / 197.
- Cascade sizes: 0 → 993, 1 → 390, 2 → 199, 3 → 166, 4 → 108, 5 → 50, 6 → 30.
- Zero rate 51.3%; the audit retains loop faults rather than dropping them.
- Split by layout seed (70/20/10).
- 50-tick warmup; pre-fault state.

The original per-entity disconnection label was too hard for local models at the
generated graph diameter. A 30-layout pilot gave vector AUPRC 0.51 and a
12-layer GNN 0.46; that diagnostic is retained, but the formal label is cascade
size. The amendment was made before generating seeds 500–699.

## Mechanic

- One pre-placed generator.
- A seeded randomized spanning tree over free cells, pruned to the minimal
  terminal tree, plus `wire_redundancy=2` loop edges.
- Each consumer has one deterministic power inlet; adjacent redundant wires do
  not provide an alternate feed.
- A bridge fault disconnects the downstream component; a loop-edge fault
  reroutes and disconnects nobody.
- Wired mode is opt-in; radius mode and frozen `factory-v0.1` are unchanged.

## Results

| model | R² | MAE | Spearman |
|---|---:|---:|---:|
| mean | −0.014 | 1.272 | — |
| vector GBDT | 0.264 [−0.045, 0.486] | 0.952 | 0.628 |
| vector MLP | 0.111 [0.014, 0.233] | 1.093 | 0.507 |
| wire-grid CNN | 0.223 ± 0.016 | 1.078 | 0.483 |
| `graph_mp` | **0.431 [0.233, 0.580]** | **0.850** | **0.714** |
| GNN | 0.329 ± 0.052 | 1.020 | 0.586 |
| oracle | 1.000 | 0.000 | 1.000 |

Brackets are layout-bootstrap 95% intervals. Neural values are mean ± std over
five seeds.

Paired layout-bootstrap difference (`graph_mp` − vector GBDT): **+0.167
[0.048, 0.309]**, P(difference > 0) = 0.9975.

GNN per-seed R²: 0.335, 0.258, 0.281, 0.387, 0.383.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 graph gain | best graph ≥ best non-graph + 0.05 | **pass**, 0.431 vs 0.264 |
| H2 graph_mp vs GNN | report | `graph_mp` +0.102 R² |
| H3 oracle | R² 1.0 | **pass** |
| H4 seed consistency | best graph std ≤ 0.05 | **pass**, `graph_mp` deterministic |
| H5 budget | report | 1,936 samples, 50 epochs, 5 neural seeds |

The GNN’s own seed std is 0.052, just over the 0.05 threshold; the gate applies
to the best graph model, which is deterministic.

## Interpretation

- **Graph structure carries the cascade signal.** The relational view adds
  +0.167 R² over the strongest flattened baseline.
- **`graph_mp` is the strong baseline.** Global pooling over one/two-hop
  features suits a small graph and a scalar cut-size label.
- **The GNN is positive but not yet competitive.** Residual layers help, but the
  graph diameter is large and the dataset is small; the GNN learns a partial
  propagation.
- **The wire-grid CNN is weak.** Local convolution sees the fault and nearby
  wires but not the global component split.
- **The label is zero-inflated.** Half the faults are loop faults that reroute
  power; the task rewards recognizing when nothing disconnects.
- **The interval is wide.** The paired lower bound (0.048) is essentially at the
  +0.05 gate; treat the effect as suggestive, not precise.

## Caveats

- One generator, one line, one redundancy setting, one fault penalty.
- Static connectivity label; buffer and demand state are context, not the label
  source.
- No wire capacity, overload, or cascading overload trips.
- One deterministic power inlet per consumer; alternate adjacent wires do not
  feed.
- Loop faults dominate the zero class; a balanced cascade-size variant would be
  a new experiment.
- The per-entity task is a diagnostic, not a formal gate.
- Not part of frozen `factory-v0.1`.

## Next

1. **Repair control (phase 1B):** choose which failed wire to repair under a
   budget; the cascade label is now learnable enough to justify it.
2. **Wire capacity and overload trips:** a second cascade mechanism.
3. **Multi-generator redundancy:** test whether graph models use alternate
   paths.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0007, ADR 0017
- Code: `experiments/wired_power/cascade_data.py`,
  `experiments/wired_power/cascade_size.py`
- Raw results: `results/wired_power/cascade_size/` (ignored)
- Task card: `docs/tasks/power-cascade.md`
- Dataset card: `docs/datasets/wired-cascade-debug-v0.1.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
