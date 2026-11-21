# Experiment 0032 — Wired-power cascade prediction

- **Status:** complete (H1/H3/H4 pass; see [`summary.md`](summary.md))
- **Date:** 2026-11-21
- **Type:** P1 graph-mechanic experiment
- **Mechanic:** wired power topology and deterministic wire faults (RFC 0007,
  ADR 0017)
- **Task:** `factory.power.cascade.v1` (debug/P1, not in `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Amendment after pilot

The original primary label was per-entity disconnection. A 30-layout pilot
(seeds 400–429) showed the label is too hard for local models at the generated
graph diameter (mean 18): vector AUPRC 0.51, graph_mp 0.40, a 12-layer GNN 0.46.
That is a useful diagnostic, but not a tractable first benchmark.

The primary label is now **cascade size**: the number of consumers disconnected
by the marked fault (0–6). The pilot gives graph_mp R² 0.370 vs vector 0.291, so
the sample-level label carries graph signal. Per-entity disconnection is
reported as a secondary diagnostic, not a gate. This amendment was made before
generating the formal seeds.

## Question

Does explicit wire-graph structure improve prediction of how many consumers lose
power after a wire fault, compared with flattened, aggregate, and grid views?

The label is a graph cut. A single bus would make it a coordinate threshold, so
the topology includes loops: a loop-edge fault reroutes power and disconnects
nobody, while a bridge fault disconnects the component on the far side from the
generator.

## Data

- Gear line, opt-in wired power, one generator.
- 200 layout seeds; up to 10 sampled fault wires per layout.
- Fault sampling is stratified: up to 5 bridge edges and 5 loop edges per
  layout. Layouts without both kinds are retained but contribute fewer samples;
  the audit reports the bridge/loop counts.
- Split by layout seed: 70% train / 20% val / 10% test.
- Sample state: after 50 warmup ticks, before the fault is applied.
- Label: number of consumers connected before the fault and disconnected after
  it.
- The faulted edge is marked in every view.
- Formal seeds: 500–699. Pilot seeds 400–429 are not formal evidence.

## Views

| View | Contents | Model |
|---|---|---|
| `vector` | graph statistics, fault position, mean entity and wire features | GBDT, MLP |
| `wire_grid` | `(H, W, 7)` wire/fault/entity channels | CNN with global pooling |
| `graph_mp` | one/two-hop message passing over the combined wire/entity graph, global pooled | GBDT |
| `gnn` | residual MPNN on the combined graph, mean/max pooling + graph features | MPNN |
| `oracle` | true cascade size | ceiling check |

## Metrics

- R² (primary);
- MAE;
- Spearman correlation (secondary).

Five seeds for neural models; deterministic GBDT/MLP references. Report
bootstrap intervals over test layouts.

## Gates

| Gate | Threshold |
|---|---|
| H1 graph gain | best graph model R² ≥ best non-graph model + 0.05 |
| H2 graph_mp vs GNN | report; no gate |
| H3 oracle ceiling | exact cascade size R² 1.0; sanity check |
| H4 seed consistency | best graph model std ≤ 0.05 |
| H5 budget | report params, epochs, samples, and positive rate |

## Predictions

- Graph models will beat the vector and wire-grid views; the label is a
  connectivity cut, not a coordinate threshold.
- `graph_mp` will be strong because the combined graph is small and the label
  depends on multi-hop pooling.
- The GNN may need more layers than the graph diameter; a negative or weak GNN
  result is informative about long-range propagation.
- Loop faults will produce zero-size samples; report them rather than dropping
  them.

## Kill criteria

- No graph model beats the best non-graph model by 0.05 R².
- The vector baseline explains most of the variance (R² ≥ 0.8), indicating the
  label is a coordinate or aggregate artifact.
- The result is dominated by one seed or layout.
- The task requires post-hoc changes to the topology, label, or gates.

## Analysis plan

- Report the data audit before training: bridge rate, cascade-size histogram,
  zero-rate, and per-split sample counts.
- Report all views and all gates.
- Report per-seed scores and bootstrap intervals over layouts.
- Report the per-entity diagnostic separately; it is not a gate.
- Do not tune the topology, redundancy, fault sampling, or gates after the
  formal run.
- Keep wired mode opt-in and `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0007, ADR 0017
- Code: `experiments/wired_power/cascade_data.py`,
  `experiments/wired_power/cascade_size.py`
- Task card: `docs/tasks/power-cascade.md`
- Raw results: `results/wired_power/cascade_size/` (ignored)
- Summary: `docs/experiments/0032-wired-cascade/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
