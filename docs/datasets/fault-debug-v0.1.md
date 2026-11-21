# Dataset card — fault-debug-v0.1

- **Status:** historical; static sensor model 0.1.0
- **License:** CC-BY-4.0 (synthetic data); code Apache-2.0
- **World version:** `factory-0.1.0`
- **Sensor model:** `sensors` / `diagnostics` 0.1.0 (stateless channels)
- **Fault config:** enabled; wear per craft 1; threshold 20; repair 30 ticks
- **Generation command:** `.venv/bin/python -m fabline fault-benchmark --out results/fault-benchmark --episodes 40`
- **Episodes:** 40
- **Samples:** 1,440 per view
- **Positive rate:** 0.306
- **Task:** `factory.fault.predict.v1` (historical 0.1.0)

## Purpose

A debug dataset for fault-within-horizon prediction. It compares the standard
vector view (no explicit wear/fault channels) against the diagnostics view
(wear, temperature, vibration, acoustic, faulted count).

It is not part of the frozen `factory-v0.1` benchmark.

## Contents

- two view datasets: `fault-vector` and `fault-diagnostics`;
- per-episode observations, labels, sample ticks, state hashes, replay;
- replay includes the fault config and the fixed `gear` scenario;
- splits by seed: 70% train / 20% val / 10% test.

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

## Caveats

- One fixed gear line and one threshold; not a general fault benchmark.
- GBDT solves both views; the diagnostics advantage is visible in the MLP.
- This card describes the historical static sensor model. The dynamic 0.2.0
  model is documented in `fault-debug-v0.2.md`.
- Small debug budgets; CIs are wide.
- Not part of `factory-v0.1`; do not compare its numbers to the frozen suite.

## Changelog

- 2026-11-21 — dataset card created.
- 2026-11-21 — marked historical after the 0.2.0 dynamic sensor mechanic; the
  card is not rewritten.
