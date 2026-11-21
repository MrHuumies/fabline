# Task card — throughput prediction

- **Task ID:** `factory.throughput.predict.v1`
- **Version:** 0.1.0
- **Status:** benchmark candidate (`factory-v0.1`), not a public release
- **World:** factory-0.1.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Given a factory state, predict the depot score produced over the next horizon.
The task tests whether an observation view carries enough layout and flow
information to forecast output. It is the reference task for comparing
observation adapters.

## Contract

- **Observations:** `vector` (18 features), `grid` (H×W×6), or `entities`
  (padded entity graph, flattened for tabular baselines).
- **Action:** none; offline supervised projection over shared episodes.
- **Label:** `future_score` — depot score gained over the next 50 ticks with no
  actions.
- **Sampling:** every 10 ticks after a jittered warmup (100–120 ticks).
- **Splits:** scenario-based. Train sees `ingot`, `gear`, and `extra_ingot`;
  val sees `ingot` and `gear`; test is the held-out `extra_gear` combination;
  shift is `shift_gear` (one ore patch, higher rock density).

## Data — `factory-v0.1`

- 46 episodes, 852 samples.
- Train: 30 episodes / 557 samples.
- Val: 4 episodes / 75 samples.
- Test: 6 episodes / 110 samples.
- Shift: 6 episodes / 110 samples.
- Future score: mean 19.79, std 8.89, min 10, max 30.

## Metrics

- MAE, RMSE, R² with 95% bootstrap confidence intervals.
- Reported separately for test and shift.

## Baselines

| Baseline | Notes |
|---|---|
| mean | Predict the training mean |
| persistence | Predict the last-window score; vector view only |
| linear | Least squares on flattened observations |
| GBDT | Histogram gradient boosting |
| MLP | One hidden layer, 64 units |
| graph_mp | One/two-hop message-passing features + GBDT; entity view only |

## Results — `factory-v0.1` test / shift

Test (held-out `extra_gear` combination), R²:

| view | linear | GBDT | MLP | graph_mp |
|---|---:|---:|---:|---:|
| vector | **0.778** | 0.575 | -0.282 | — |
| grid | -9.473 | -1.789 | -6.292 | — |
| entities | -5.571 | -11.111 | -3.188 | **0.348** |

Shift (`shift_gear`), R²:

| view | linear | GBDT | MLP | graph_mp |
|---|---:|---:|---:|---:|
| vector | 0.679 | **0.974** | -0.234 | — |
| grid | 0.342 | **0.997** | -0.014 | — |
| entities | 0.424 | **1.000** | 0.414 | **1.000** |

## P0 grid CNN debug result

Fixed gear line, 100 episodes, 1,600 samples, 50-tick horizon, fog radius 3:

| model | clear R² | fog R² |
|---|---:|---:|
| linear | 0.829 | 0.540 |
| GBDT | 1.000 | 0.543 |
| MLP | 0.772 | 0.544 |
| CNN | 0.997 | 0.509 |

The CNN nearly solves the clear grid but degrades more under fog than the
flattened MLP (0.488 vs 0.228). This is a debug result on a fixed line, not the
frozen `factory-v0.1` split. See
[`experiments/0026-grid-cnn`](../experiments/0026-grid-cnn/summary.md).

## P0 graph MPNN debug result

Shared `factory-v0.1` split, entity graph, 852 samples:

| model | test R² | shift R² |
|---|---:|---:|
| linear (flattened) | −5.570 | 0.424 |
| GBDT (flattened) | −11.111 | 1.000 |
| MLP (flattened) | −3.188 | 0.414 |
| `graph_mp` | 0.348 | 1.000 |
| MPNN | 0.258 | 0.690 |

Flattened views collapse on the held-out `extra_gear` combination; relational
models stay positive. The end-to-end MPNN trails the one/two-hop `graph_mp`
feature baseline by 0.09 and has seed std 0.111. See
[`experiments/0027-graph-mpnn`](../experiments/0027-graph-mpnn/summary.md).

## Known pitfalls

- **The held-out combination is hard for flattened views.** The vector view
  generalizes; grid and flattened entity views do not. This is a useful signal,
  not a broken task.
- **The test split is small** (6 episodes, 110 samples). Confidence intervals
  are wide; do not overread small differences.
- **Scenario splits are a compositional proxy**, not a formal causal test. The
  held-out `extra_gear` combines assembler and extra belt.
- **Graph flattening is not a GNN.** `graph_mp` uses pooled one/two-hop
  features; a trained GNN is future work.
- **The vector includes historical production**, so persistence is a strong
  baseline; that is intentional.
- **Phase jitter** prevents a constant label but is not a full demand process.

## Changelog

- 2026-11-21 — card created; M2 debug results added.
- 2026-11-21 — moved to shared episodes; M3 benchmark results added.
- 2026-11-21 — P0 grid CNN debug result added.
- 2026-11-21 — P0 graph MPNN debug result added.
