# Benchmark card — factory-v0.3 (draft)

- **Status:** frozen
- **Version:** 0.3.0
- **Date:** 2026-11-26
- **World:** `factory-0.1.0`
- **Plan:** `compositional-v0.3`
- **Spec:** [`benchmark.toml`](benchmark.toml)
- **Freeze review:** [`freeze-review.md`](freeze-review.md)
- **Coverage review:** [`docs/coverage-review-0.4.0.md`](../../docs/coverage-review-0.4.0.md)
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Reproduce:** `.venv/bin/python -m fabline benchmark-v03 --out results/factory-v0.3`
- **Check:** `.venv/bin/python -m fabline benchmark-v03 --out results/factory-v0.3 --check-expected benchmarks/factory-v0.3/expected/summary.json`

## What is proposed

`factory-v0.3` keeps the frozen v0.2 core and adds two order tasks:

- **order-control:** seeded gear/component orders, online recipe switching;
- **order-planning:** known order set, five-block recipe plan, CEM/oracle.

Production mix is a mechanic diagnostic. BC/PPO is a negative baseline track.
Demand calibration/causal and generative tasks are deferred.

## Tasks

| Task | Kind | Observation | Headline |
|---|---|---|---|
| throughput-vector | regression | vector | R² / MAE |
| throughput-grid | regression | grid | R² / MAE |
| throughput-entities | regression | entities | graph_mp R² |
| masked-grid | self-supervised | grid | MSE / cosine |
| bottleneck | classification | graph/vector | accuracy / balanced |
| expand-control | control | control | success / score |
| control-dynamics | self-supervised | control | MSE / cosine |
| planning-triage | planning | crew state | CEM/oracle score |
| fault-calibration | calibration | sensors | ECE / balanced |
| causal-removal | prediction | intervention | target R² |
| order-control | control | production + orders | fulfilled value |
| order-planning | planning | order set | plan value |

## Formal evidence

- Core: 159 episodes, 20 test / 20 shift.
- Order control (0090): value 289.8, Q 280.2, random 226.4; value policy 1.00,
  Q 1.00 success. Success is saturated at the 160 threshold; value is the
  headline.
- Order planning (0091): CEM = oracle 292.4, EDF 263.8; all planning gates pass.
- Production mix (0089): component 186 vs gear 150; no schedule gap. Diagnostic.
- Order RL (0092): BC 249.8, PPO 169.0 vs random 243.2 on its own comparison
  block; scripted value 272.5. Negative baseline.

## Freeze status

- Expected summary is checked in.
- Cheap check passes with zero mismatches.
- Full run on 2026-11-26 matches the expected summary with zero mismatches.
- `factory-v0.3` is frozen; `factory-v0.2` remains immutable.

## Caveats

- Order-control success is not a useful discriminator; use fulfilled value.
- Order planning is exact because the oracle is only 32 plans.
- `factory-v0.3` is v0.2 core plus two tasks, not a new world.
- `factory-v0.2` remains immutable.

## Changelog

- 2026-11-26 — draft card created with the 12-task candidate.
