# Dataset card — wired-cascade-debug-v0.1

- **Status:** debug/P1 dataset
- **World version:** `factory-0.1.0` with opt-in wired power
- **License:** CC-BY-4.0 (synthetic data); code Apache-2.0
- **Generation:** `PYTHONPATH=. .venv/bin/python -m experiments.wired_power.cascade_data --out experiments/wired_power/data/cascade_size.npz --layouts 200 --seed-start 500`
- **Layouts:** 200
- **Samples:** 1,936
- **Splits:** 1,359 / 380 / 197 train / val / test (by layout seed)
- **Task:** `factory.power.cascade.v1`

## Purpose

A debug dataset for wired-power cascade prediction. Each sample is one layout
plus one marked wire fault. The label is the number of consumers that are
connected before the fault and disconnected after it.

It is not part of the frozen `factory-v0.1` benchmark.

## Contents

Per sample:

- padded entity features and mask (32 × 16);
- per-entity disconnection labels and label mask;
- wire-node features and mask (64 × 5);
- post-fault wire adjacency (64 × 64);
- entity-to-wire adjacency (32 × 64);
- entity positions and source position;
- graph statistics and fault-edge position;
- split, layout seed, fault wire id, cascade size, and loop flag.

## Generation

- gear line; one generator; generator capacity 5; radius mode disabled;
- 50-tick warmup; pre-fault state;
- up to 5 bridge and 5 loop faults per layout;
- one deterministic power inlet per consumer;
- wire redundancy 2.

Cascade sizes: 0 → 993, 1 → 390, 2 → 199, 3 → 166, 4 → 108, 5 → 50, 6 → 30.
Zero rate 51.3% (loop faults reroute power).

## Results

Cascade-size R² (experiment 0032):

| model | R² |
|---|---:|
| vector GBDT | 0.264 |
| wire-grid CNN | 0.223 |
| `graph_mp` | **0.431** |
| GNN | 0.329 |
| oracle | 1.000 |

See
[`experiments/0032-wired-cascade`](../experiments/0032-wired-cascade/summary.md).

## Caveats

- Zero-inflated label; half the faults disconnect nobody.
- One generator, one line, one redundancy setting.
- No wire capacity or overload trips.
- Static connectivity label; entity buffers are context, not the label source.
- Pilot layouts 400–429 are not in the formal dataset.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-21 — card created; formal cascade-size dataset and results added.
