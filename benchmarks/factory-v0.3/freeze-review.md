# `factory-v0.3` freeze review (draft)

- **Status:** frozen as `factory-v0.3`
- **Date:** 2026-11-26
- **Scope:** 0.4.0 benchmark candidate
- **Related:** [spec](spec.md), ADR 0042, RFC 0030, experiments 0089–0092
- **Predecessor:** `factory-v0.2` remains immutable

## Decision summary

`factory-v0.3` is proposed as a **12-task benchmark**:

1. the 10 headline tasks frozen in `factory-v0.2`;
2. **order-control**;
3. **order-planning**.

Production mix, deep/offline RL, demand calibration/causal, and generative
modeling are not headline tasks. Production mix and RL are diagnostics/baseline
results; calibration/causal and generative are deferred.

The benchmark is frozen: the `benchmark-v03` runner, expected summary, and CI
check exist. The full run matches the expected summary with zero mismatches.

## Evidence

| Candidate | Gate | Result | Decision |
|---|---|---|---|
| v0.2 core | frozen, stable | 10 tasks, 159 episodes | keep |
| production mix (0089) | schedule gap ≥10 | component 186 vs gear 150; no schedule gain | diagnostic only |
| order control (0090) | best scripted ≥ always-gear +10; Q ≥ random +10; Q success ≥0.60 | value 272.5, Q 259.5, random 243.2; all pass | freeze |
| order planning (0091) | oracle ≥ scripted +10; CEM ≥ random +10; CEM within 10 of oracle; success ≥0.60 | CEM = oracle 292.4; EDF 263.8; all pass | freeze |
| order RL (0092) | BC/PPO ≥ random +10 | BC 249.8 (+6.6), PPO 169.0 (−74.3) | baseline only; no task |
| demand calibration | skill + ECE gate | not run | defer |
| causal order/recipe | interventional gate | not run | defer |
| generative recipe | ≥20 structures, diversity ≥0.25 | current content has 7 line sequences | defer |

## Frozen task matrix (proposed)

### v0.2 core

- throughput-vector
- throughput-grid
- throughput-entities
- masked-grid
- bottleneck
- expand-control
- control-dynamics
- planning-triage
- fault-calibration
- causal-removal

### 0.4.0 additions

| Task | Kind | Observation | Headline metric |
|---|---|---|---|
| order-control | control | production + order view | fulfilled order value |
| order-planning | planning | known order set | plan value / success |

### Diagnostics / baselines (not headline)

- production mix: fixed-item effect, no schedule gap;
- BC/PPO: negative baseline track;
- demand calibration/causal: not run;
- generative recipe/layout: current content too constrained.

## Episodes and seeds

### Core

Use the v0.2 core plan unchanged: 159 episodes, 20 test and 20 shift.

### Order control

- 5 evaluation seeds: 72,000–72,004 (the formal 0090 block).
- 5 episodes per seed.
- Training data/seed budgets fixed at freeze.
- Order-control success is saturated (most baselines reach 1.00 at the 160
  threshold); **fulfilled order value is the headline**, success is reported.

### Order planning

- 5 evaluation seeds: 74,000–74,004 (the formal 0091 block).
- Five recipe blocks of six decisions; 32-plan oracle.
- CEM population 16, elites 4, iterations 4, 32 random samples.
- CEM matches the oracle on the formal block; the planner is a true-simulator
  reference, not a learned world model.

### Diagnostics

- Production mix: 5 seeds, 70,000–70,004.
- Order RL: 5 eval seeds, 77,000–77,004; BC/PPO negative.
- No demand calibration/causal or generative task.

## Baselines

- **Core:** v0.2 families (mean/persistence, linear, GBDT, MLP, graph_mp, copy,
  scripted, random, tabular Q/BC, CEM).
- **Order control:** always gear/component, EDF, value, random, tabular Q, BC,
  PPO (optional Torch).
- **Order planning:** always, EDF/value plans, random plan, CEM, oracle.
- **Cost:** report training/inference time and parameters for learned baselines.

## Runner

A new `fabline benchmark-v03` orchestrator will:

1. run the v0.2 core block unchanged;
2. run order-control and order-planning blocks;
3. run diagnostics (production mix, order RL) without including them in the
   headline expected summary;
4. write one results JSON and compact expected summary.

Planned CI:

- PR: cheap core/order regression subset;
- scheduled: full `factory-v0.3` check.

## Freeze gates

- [x] `factory-v0.2` hash and assets unchanged.
- [x] 12 headline tasks have expected summaries.
- [x] Core has 20 test and 20 shift episodes.
- [x] Order control/planning expected summaries are deterministic.
- [x] `benchmark-v03` writes a compact expected summary.
- [x] CI cheap/full regression checks exist.
- [x] Benchmark card and spec are complete.
- [x] Public export has no private references.
- [x] No production mix or RL condition is presented as a headline task.

## Risks

- **Order-control success is saturated.** Use value as the headline and report
  success as a caveat; do not tune the threshold after seeing the block.
- **Order-planning CEM is exact at 32 plans.** This is a small plan space, not a
  general planning claim.
- **Production mix is not a task alone.** Keep it as the mechanic diagnostic.
- **Deep RL is negative.** Keep it as a baseline result, not a task.
- **Benchmark scope.** `factory-v0.3` is v0.2 core plus two tasks; it does not
  claim a new world.
- **Compute.** The full runner includes the v0.2 core, which is already the
  expensive block.

## Freeze evidence

- Full run: 159 core episodes, core hash
  `5f0d54f...`, order control 289.8, order planning 292.4.
- Expected-summary check: **0 mismatches**.
- Cheap check: `benchmark-v03 --skip-v02-planning --skip-diagnostics
  --skip-production` passes.
- `factory-v0.2` assets unchanged.

## Next steps

1. Tag `factory-v0.3`.
2. Run the 0.4.0 release audit.
3. Publish the GitHub release.

## Changelog

- 2026-11-26 — draft freeze review; 12 tasks; production mix/RL diagnostics;
  calibration/causal/generative deferred.
