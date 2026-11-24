# `factory-v0.2` freeze review (draft)

- **Status:** draft freeze review; **not frozen**
- **Date:** 2026-11-24
- **Scope:** 0.3.0 benchmark candidate
- **Related:** [spec](spec.md), RFC 0029, ADR 0041, P3 reviews

## Decision summary

`factory-v0.2` will be an **extended, runnable benchmark** built from three
blocks:

1. **Core block:** 160 shared episodes of the v0.1 task family, with more test
   and shift episodes.
2. **Fault/power block:** 40 episodes each for fault prediction and power
   brownout.
3. **Decision block:** planning-triage, fault calibration, and causal removal.

This is a scope cut from the draft spec (180 episodes plus a separate 20-episode
layout split). The layout split and decentralized multi-agent task are deferred:
the shared-suite API does not yet support a fifth split, and the decentralized
Q success gate is open.

## Task list

### Core block (frozen candidate)

- throughput-vector
- throughput-grid
- throughput-entities
- masked-grid
- bottleneck
- expand-control
- control-dynamics

`next-state` is excluded: copy/linear saturates it.

### Fault/power block

- fault prediction (existing fault benchmark)
- power brownout (stochastic power)

### Decision block

- triage planning: true CEM and scripted/oracle baselines; the learned value
  model is a negative baseline.
- fault calibration: top-4 view, Brier/NLL/ECE.
- counterfactual removal: same-type pairs, target vs type-only.

### Not frozen

- decentralized private-view triage: debug task; Q success 0.47, below 0.60.
- generative layout/recipe: optional pilot, not run.
- next-state: retired headline.
- all P2/P3 debug tasks not listed above.

## Episode and seed plan

Core:

| split | episodes |
|---|---:|
| train | ~100 total (34/33/33 across ingot/gear/extra_ingot) |
| val | 20 (10/10 across ingot/gear) |
| test | 20 (extra_gear) |
| shift | 20 (shift_gear) |
| **total** | **160** |

Fault/power: 40 episodes each, seed blocks fixed at freeze.

Decision:

- planning: 5 evaluation seeds, 5 seeds × 20? Use the 5-seed formal block.
- calibration: 3 × 40-episode blocks.
- causal: 3 × 40-episode blocks.

## Runner

A new `fabline benchmark-v02` orchestrator will:

1. run `shared-suite` with the v0.2 plan;
2. run the fault and power benchmarks;
3. run planning, calibration, and causal harnesses;
4. write one `factory_v02_results.json` and a report.

The benchmark is not frozen until this runner produces an expected summary and
a CI regression check.

## Freeze gates

- `factory-v0.1` hash and assets unchanged.
- 160 core episodes; 20 test and 20 shift.
- Fault/power/decision blocks complete.
- Expected summary generated once and checked into
  `benchmarks/factory-v0.2/expected/`.
- CI runs a reduced or full benchmark and compares key metrics.
- Benchmark card, spec, and task cards complete.
- No private consumer references.

## Why not include decentralized now

The task is a valid local/global benchmark, but:
- local scripted success is 0.40;
- private Q success is 0.47;
- the 0.60 gate is open.

Freezing it would freeze a task whose local baselines are unreliable. Keep it
as a debug task and revisit after a compact-state or centralized-training
follow-up.

## Why not include generative now

The optional generative pilot has not run. It is not release-blocking.

## Next steps

1. Implement `benchmark-v02`.
2. Generate expected summaries for the three blocks.
3. Write the benchmark card and freeze tag `factory-v0.2`.
4. Build the wizard/viewer.
5. Release audit for 0.3.0.

## Changelog

- 2026-11-24 — draft freeze review; core + fault/power + decision blocks;
  decentralized/generative deferred.
