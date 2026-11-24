# Benchmark card — factory-v0.2

- **Status:** frozen
- **Version:** 0.2.0
- **Date:** 2026-11-24
- **World:** `factory-0.1.0`
- **Plan:** `compositional-v0.2`
- **Spec:** [`benchmark.toml`](benchmark.toml)
- **Freeze review:** [`freeze-review.md`](freeze-review.md)
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Reproduce:** `.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2`
- **Check:** `.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2 --check-expected benchmarks/factory-v0.2/expected/summary.json`

The full run is compute-heavy (roughly 20–40 minutes on the development
machine); most of it is the planning value model and CEM/oracle. Use
`--skip-planning --skip-diagnostics` for a cheap regression check.

## What is frozen

- the world and tick semantics (`factory-0.1.0`);
- the `compositional-v0.2` scenario split;
- 159 shared core episodes and the 2,948-sample projection;
- the headline task set and their labels;
- the baseline families and budgets;
- the planning, calibration, and causal protocols;
- the report format and compact expected summary.

`factory-v0.1` remains frozen and unchanged. The v0.2 core config hash is the
same as v0.1 because the canonical world and shared generation config did not
change; only the episode plan and the added decision blocks differ.

## Headline tasks

| Task | Kind | Observation | Samples |
|---|---|---|---:|
| throughput-vector | regression | vector | 2,948 |
| throughput-grid | regression | grid | 2,948 |
| throughput-entities | regression | entities/graph | 2,948 |
| masked-grid | self-supervised | grid | 2,948 |
| bottleneck | classification | graph/vector | 2,948 |
| expand-control | control | control | 50 |
| control-dynamics | self-supervised action | control | 900 |
| planning-triage | planning | crew-replan state | 5 seeds |
| fault-calibration | calibration/detection | context + sensors | 3 × 40 episodes |
| causal-removal | prediction | state + intervention | 3 × 40 episodes |

`next-state` is produced as a diagnostic but is not a headline task. Fault
prediction and stochastic power are diagnostics; decentralized triage and
generative layout/recipe are deferred.

## Splits

| Split | Episodes | Samples | Scenarios |
|---|---:|---:|---|
| train | 99 | 1,836 | ingot, gear, extra_ingot |
| val | 20 | 373 | ingot, gear |
| test | 20 | 370 | extra_gear (held out) |
| shift | 20 | 369 | shift_gear |

The expected summary stores the exact totals; the per-split counts depend on
the deterministic warmup jitter.

## Baselines

- Throughput: mean, persistence (vector only), linear, GBDT, MLP, `graph_mp`
  (entities only).
- Self-supervised: copy, linear, MLP.
- Bottleneck: majority, GBDT, MLP.
- Control: scripted, random, tabular Q, behavior cloning.
- Planning: scripted greedy/aware, random, random shooting, CEM with the true
  simulator, CEM with a ridge value model, exhaustive oracle.
- Calibration: majority, GBDT, MLP; Brier, NLL, ECE.
- Causal: mean, linear, GBDT, MLP on type-only vs target views.

## Expected headline results

Test split unless noted; see [`expected/summary.json`](expected/summary.json)
for the full compact summary and per-seed values.

| Task | Headline |
|---|---|
| throughput-vector | linear R² 0.767; GBDT 0.649; MLP 0.038 |
| throughput-grid | all learned baselines negative (linear −10.05; GBDT −1.49) |
| throughput-entities | `graph_mp` R² 0.537; flattened baselines negative |
| masked-grid | MLP MSE 0.0349, cosine 0.663 |
| bottleneck | GBDT accuracy 0.965, balanced 0.949 |
| expand-control | scripted/BC success 1.00; tabular Q 0.80; random 0.02 |
| control-dynamics | linear MSE 0.0085, cosine 0.961 |
| planning-triage | CEM true 462 = oracle; random 108; scripted greedy 382; CEM learned 232 |
| fault-calibration | top-4 GBDT balanced 0.923, ECE 0.0118; base views near 0.50 |
| causal-removal | target GBDT R² 0.987; type-only −0.074 |

The planning block uses seeds 62,000–62,004; calibration uses 63,000 / 63,100 /
63,200; causal uses 64,000 / 64,100 / 64,200. These are the frozen benchmark
seeds, not the pilot seeds in experiments 0076, 0078, and 0079. The ordering is
the same; the point estimates differ slightly.

## Caveats

- The core benchmark is a compositional/shift proxy, not a causal test.
- Throughput-grid and flattened entity views fail to generalize to the held-out
  combination; that is a measured boundary, not a bug.
- Next-state is saturated by copy/linear; use masked-grid and control-dynamics
  for harder self-supervised signals.
- The control task is a fixed six-tile construction puzzle; tabular Q is
  seed-sensitive.
- The planning oracle is small (256 sequences). The ridge value model is a
  negative baseline, not a transition world model.
- Fault calibration uses pre-noise top-4 selection and 32 features; the base
  views are at majority, so low ECE there is not skill.
- Causal removal uses same-type pairs at three sample ticks and a 100-tick
  horizon; it is interventional prediction, not causal graph recovery.
- The 20 test and 20 shift episodes are larger than v0.1 but still small.
- The benchmark is a research sandbox, not a product claim or leaderboard.

## Versioning

This card, the tag `factory-v0.2`, and `expected/summary.json` freeze the
benchmark. Changes to world mechanics, scenarios, labels, splits, task set, or
baselines require a new benchmark version. Diagnostic results may improve
without changing the frozen headline.

## Changelog

- 2026-11-24 — frozen at 10 headline tasks; 159 core episodes; planning,
  calibration, and causal blocks; diagnostics separated.
