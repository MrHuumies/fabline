# Dataset card — fault-debug-v0.2

- **Status:** debug dataset for the opt-in fault mechanic
- **License:** CC-BY-4.0 (synthetic data); code Apache-2.0
- **World version:** `factory-0.1.0`
- **Sensor model:** `sensors` / `diagnostics` 0.2.0 (dynamic channels)
- **Fault config:** enabled; wear per craft 1; threshold 20; repair 30 ticks
- **Generation command:** `.venv/bin/python -m fabline fault-benchmark --out results/fault-benchmark --episodes 40`
- **Episodes:** 40
- **Samples:** 1,440 per view
- **Positive rate:** 0.306
- **Task:** `factory.fault.predict.v1` (0.2.0)

## Purpose

A debug dataset for fault-within-horizon prediction with the dynamic sensor
model. It compares the standard vector view (no explicit wear/fault channels)
against the diagnostics view (wear, temperature, vibration, acoustic, faulted
count).

It is not part of the frozen `factory-v0.1` benchmark.

## Contents

- two view datasets: `fault-vector` and `fault-diagnostics`;
- per-episode observations, labels, sample ticks, state hashes, replay;
- replay includes the fault config and the fixed `gear` scenario;
- splits by seed: 70% train / 20% val / 10% test.

## Sensor model

- `temperature` is a slow first-order follower of wear, crafting, and faults;
- `vibration` is a decaying impulse at craft start and miner output;
- `acoustic` is a decaying impulse at blockage and fault onset;
- all channels are normalized to `[0, 1]` in the observation views;
- sensor fields stay zero and are omitted from the hash when faults are
  disabled, so fault-free data is unchanged.

The `future_fault` labels for the 100-episode experiment dataset are identical
to the static 0.1.0 dataset; only observations changed.

## Fault mechanic

- furnaces/assemblers gain wear on each completed craft;
- at threshold 20 they fault and stop crafting;
- auto-repair after 30 ticks;
- fault events are recorded in the state event log;
- `sensors`/`diagnostics` observations expose wear and fault state.

## Results (test split)

| view | GBDT accuracy | GBDT balanced | MLP accuracy | MLP balanced |
|---|---:|---:|---:|---:|
| vector | 1.000 | 1.000 | 0.750 | 0.667 |
| diagnostics | 1.000 | 1.000 | 1.000 | 1.000 |

The dynamic channels change the data path but not the conclusion: GBDT solves
both views, and diagnostics helps the MLP.

## Caveats

- One fixed gear line and one threshold; not a general fault benchmark.
- GBDT solves both views; the diagnostics advantage is visible in the MLP.
- Prediction, not recovery; repair is a separate task.
- Small debug budgets; CIs are wide.
- Not part of `factory-v0.1`; do not compare its numbers to the frozen suite.
- The dynamic sensor parameters were fixed before experiment 0011; do not tune
  them against that experiment.

## Changelog

- 2026-11-21 — dataset card created for sensor model 0.2.0.
