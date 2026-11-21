# Dataset card — power-debug-v0.1

- **Status:** debug dataset for the opt-in power mechanic
- **License:** CC-BY-4.0 (synthetic data); code Apache-2.0
- **World version:** `factory-0.1.0`
- **Power config:** one generator, capacity 9, radius 8
- **Generation command:** `.venv/bin/python -m fabline power-benchmark --out results/power-benchmark --episodes 40`
- **Episodes:** 40
- **Samples:** 3,200 per view
- **Positive rate:** 0.366
- **Task:** `factory.power.brownout.v1`

## Purpose

A debug dataset for brownout-within-5-ticks prediction. It compares the
standard vector view (no explicit power channels) against the power view
(load, powered ratio, brownouts, per-type power).

It is not part of the frozen `factory-v0.1` benchmark.

## Contents

- two view datasets: `power-vector` and `power-power`;
- per-episode observations, labels, sample ticks, state hashes, replay;
- replay includes the power config and the fixed `gear` scenario;
- splits by seed: 70% train / 20% val / 10% test;
- 100-tick warmup; 5-tick sampling; 5-tick label horizon; 500-tick episodes.

## Power mechanic

- generators are pre-placed infrastructure, not entities;
- one generator with capacity 9 and radius 8 for this dataset;
- demand is activity-gated: miner 2 continuously, belts 1 while carrying,
  furnace 3 while crafting, assembler 4 while crafting;
- unpowered active machines stop work and emit `power_brownout`;
- power restored emits `power_restored`;
- faulted machines demand no power.

The generator layout and power state are deterministic per seed.

## Results (test split)

| view | GBDT accuracy | GBDT balanced | MLP accuracy | MLP balanced |
|---|---:|---:|---:|---:|
| vector | 1.000 | 1.000 | 0.763 | 0.743 |
| power | 1.000 | 1.000 | 0.825 | 0.773 |

GBDT solves both views; the power view improves the MLP. The vector view's
tick and production history expose the load cycle.

## View-arrival results

The same dataset is used for the power view-arrival experiments:

- vector + line base: AP 1.0000, power gain 0.0000 (ceiling);
- vector + context base, no line buffers: base 0.6652, residual power 0.9150
  (+0.2499), exact retention; full 0.9451 (+0.2799).
- stochastic power (60/40 jitter, period 10): base 0.2362, residual power
  0.3204 (+0.0842), exact retention; full 0.3179 (+0.0817).

The line buffers determine the brownout label; remove them to measure the power
view.

## Calibration

The power benchmark reports Brier, NLL, and ECE. On the stochastic 60/40/10
variant:

- vector GBDT: Brier 0.164, NLL 0.517, ECE 0.042;
- vector MLP: Brier 0.167, NLL 0.517, ECE 0.016;
- power GBDT: Brier 0.159, NLL 0.486, ECE 0.035;
- power MLP: Brier 0.161, NLL 0.495, ECE 0.020.

The MLP is better calibrated but close to majority accuracy. Calibration and
discrimination are separate axes.

## Caveats

- One fixed gear line, generator layout, and budget; not a general power
  benchmark.
- Generators are pre-placed; they are not buildable yet.
- The label predicts a new brownout transition, not a sustained unpowered
  state.
- GBDT solves both views; the MLP is the view comparison.
- Small debug budgets; CIs are wide.
- Not part of `factory-v0.1`; do not compare its numbers to the frozen suite.

## Changelog

- 2026-11-21 — dataset card created for the power-grid debug benchmark.
- 2026-11-21 — power view-arrival results added.
- 2026-11-21 — stochastic power view-arrival results added.
- 2026-11-21 — calibration metrics added.
