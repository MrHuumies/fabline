# Task card — wired-power cascade prediction

- **Task ID:** `factory.power.cascade.v1`
- **Version:** 0.1.0
- **Status:** P1 debug task; cascade-size formal run complete; not in
  `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

A generator supplies a production line through a wire graph with branches and
loops. A wire fault removes one edge. If the edge is a bridge, every consumer on
the far side loses connectivity; if the edge is in a loop, power reroutes and
nothing disconnects. The task is to predict the number of disconnected
consumers from the pre-fault state and the marked fault edge.

## Contract

- **Observation:** wire graph, entity features, power state, and the marked
  fault edge.
- **Action:** none; offline supervised projection.
- **Label:** `cascade_size` — number of consumers connected before the fault and
  disconnected after it. Per-entity disconnection is a secondary diagnostic.
- **Topology:** one generator; seeded randomized spanning tree plus
  `wire_redundancy` loop edges; each consumer has one deterministic power inlet.
- **Faults:** stratified bridge and loop edges; deterministic reachability.
- **Sampling:** fixed 50-tick warmup, pre-fault state.
- **Splits:** by layout seed, 70% train / 20% val / 10% test.
- **Data:** 200 layouts × up to 10 fault wires.

## Metrics

- R² (primary);
- MAE;
- Spearman correlation (secondary).

## Baselines

| Baseline | Input |
|---|---|
| oracle | true cascade size |
| vector + GBDT/MLP | graph statistics, fault position, mean entity/wire features |
| wire-grid CNN | `(H, W, 7)` wire/fault/entity channels |
| graph_mp | message passing over the combined wire/entity graph, global pooled |
| GNN/MPNN | residual MPNN with mean/max pooling |

## Gates

| Gate | Threshold |
|---|---|
| H1 graph gain | best graph R² ≥ best non-graph + 0.05 |
| H2 graph_mp vs GNN | report |
| H3 oracle | R² 1.0 |
| H4 seed consistency | std ≤ 0.05 |
| H5 budget | report |

## Results (0032)

200 layouts, seeds 500–699; 1,936 samples; 51.3% zero-size loop faults.

| model | R² | MAE |
|---|---:|---:|
| vector GBDT | 0.264 | 0.952 |
| wire-grid CNN | 0.223 | 1.078 |
| `graph_mp` | **0.431** | **0.850** |
| GNN | 0.329 | 1.020 |
| oracle | 1.000 | 0.000 |

Paired layout-bootstrap difference (`graph_mp` − vector): +0.167 [0.048, 0.309].
H1, H3, and H4 pass; see
[`experiments/0032-wired-cascade`](../experiments/0032-wired-cascade/summary.md).

## Public reproduction (2026-11-26)

- Public harness: `src/fabline/harness/wired_cascade.py`; run with
  `python -m fabline wired-cascade --out results/wired-cascade`.
- 199 valid layouts, 1,990 samples, 52.6% zero-size loop faults.
- Test R²: vector linear 0.107, vector MLP 0.100, vector GBDT −0.034,
  `graph_mp` **0.124**, MPNN 0.037 (10 epochs/16 hidden diagnostic).
- `graph_mp` beats the best non-graph by only **+0.018**, below the +0.05 H1
  gate. This is a **public reproduction gap**, not a task failure: the private
  0032 feature encoding is not in the public tree, and the public wire-line
  graph encoding is weaker. Keep the task diagnostic until a stronger graph
  encoding or GNN closes the gap; do not lower the gate.

## Pilot note

The original per-entity label was too hard for local models at graph diameter
18. The 30-layout pilot gave vector AUPRC 0.51 and a 12-layer GNN 0.46, while
cascade size gave graph_mp R² 0.37 vs vector 0.29. The primary label was
amended before formal data generation.

## Known pitfalls

- **A single bus would be too easy.** The label would be a coordinate threshold.
- **Loop faults produce zero-size samples.** Stratify and report.
- **Long graph diameter.** Four-layer GNNs cannot propagate across it; the GNN
  uses residual layers and global pooling.
- **Single power inlet.** Adjacent redundant wires do not provide an alternate
  feed; this keeps the cut label well defined.
- **One generator and one line.** Multi-generator redundancy is a follow-up.
- **Wire capacity is not modeled.** Phase 1A is pure connectivity.
- **Not part of `factory-v0.1`.**

## Dataset

[`wired-cascade-debug-v0.1`](../datasets/wired-cascade-debug-v0.1.md).

## Changelog

- 2026-11-21 — card created; mechanic and experiment preregistered.
- 2026-11-21 — primary label amended to cascade size after the per-entity pilot.
- 2026-11-21 — formal cascade-size run: graph_mp +0.167 R² over vector.
- 2026-11-26 — public harness and CLI added; public graph gain is +0.018 R²,
  below the +0.05 gate; task remains diagnostic pending a stronger encoding.
