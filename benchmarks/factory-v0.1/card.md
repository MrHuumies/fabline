# Benchmark card — factory-v0.1

- **Status:** frozen
- **Date:** 2026-11-21
- **World:** `factory-0.1.0`
- **Plan:** `compositional-v0.1`
- **Dataset:** [`docs/datasets/factory-shared-v0.1.md`](../../docs/datasets/factory-shared-v0.1.md)
- **Spec:** [`benchmark.toml`](benchmark.toml)
- **Reproduce:** `.venv/bin/python -m fabline shared-suite --out results/factory-v0.1`

## What is frozen

- the world and tick semantics;
- the scenario split plan and episode counts;
- the shared episode generation parameters;
- the task projections and label definitions;
- the baseline families and budgets;
- the report format.

The expected summary is in [`expected/summary.json`](expected/summary.json).
Small numerical differences from library versions are acceptable; the point
estimates and qualitative ordering should be stable.

## Tasks

| task | kind | observation | samples |
|---|---|---|---:|
| throughput-vector | supervised | vector | 852 |
| throughput-grid | supervised | grid | 852 |
| throughput-entities | supervised | entities | 852 |
| next-state | self-supervised | vector | 852 |
| masked-grid | self-supervised | grid | 852 |
| bottleneck | classification | vector | 852 |
| expand-control | control | control | 15 |
| control-dynamics | self-supervised action | control | ~900 |

## Splits

| split | episodes | samples | scenarios |
|---|---:|---:|---|
| train | 30 | 557 | ingot, gear, extra_ingot |
| val | 4 | 75 | ingot, gear |
| test | 6 | 110 | extra_gear (held out) |
| shift | 6 | 110 | shift_gear |

## Baselines

- Throughput: mean, persistence (vector only), linear, GBDT, MLP, graph_mp
  (entities only).
- Next-state / masked-grid / control-dynamics: copy, linear, MLP.
- Bottleneck: majority, GBDT, MLP.
- Control: scripted, random, tabular Q, behavior cloning.

## Expected headline results

Test split, unless noted:

| task | headline |
|---|---|
| throughput-vector | linear R² 0.778; GBDT 0.575 |
| throughput-grid | all learned baselines negative R² |
| throughput-entities | graph_mp R² 0.348; flattened baselines negative |
| next-state | linear cosine 0.9998 (saturated) |
| masked-grid | MLP MSE 0.0365, cosine 0.644 |
| bottleneck | GBDT accuracy 0.827, balanced 0.772 |
| expand-control | scripted/BC/Q success 1.00; random 0.07 |
| control-dynamics | linear MSE 0.0085, cosine 0.961 |

## Caveats

- The test and shift splits are small (6 episodes each).
- Scenario splits are a compositional/shift proxy, not a causal test.
- Next-state is saturated; use masked-grid and control-dynamics for harder
  self-supervised signals.
- Graph flattening is not a GNN; `graph_mp` is a message-passing feature
  baseline.
- Control is a fixed six-tile construction puzzle.
- The benchmark is a research sandbox, not a product claim.

## Versioning

This card and the tag `factory-v0.1` freeze the benchmark. Changes to world
mechanics, scenarios, labels, splits, or baselines require a new version.

## Changelog

- 2026-11-21 — benchmark created and frozen at M3.
