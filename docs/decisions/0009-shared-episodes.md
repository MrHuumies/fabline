# ADR 0009 — Shared episodes and task projections

- **Status:** accepted
- **Date:** 2026-11-21
- **Related:** ADR 0003, ADR 0005, ADR 0007

## Context

M2 generated a separate dataset for each offline task. That duplicated world
rollouts, made cross-task comparisons harder, and violated the shared-episode
principle from ADR 0005. M3 needed one recording that could feed throughput,
next-state, masked-grid, and bottleneck tasks with the same states and splits.

## Decision

1. A **shared episode** records one passive rollout with:
   - views: vector, grid, entity features, entity mask, adjacency;
   - targets: future score, next vector, counterfactual bottleneck;
   - sample ticks and state hashes.
2. Offline tasks are **projections**: a task selects a view, a target, a split,
   and a metric. The dataset is written once; tasks do not re-run the world.
3. Scenario splits are explicit: train on ingot/gear/extra-ingot; test the
   held-out extra-gear combination; shift to a harsher layout.
4. Warmup jitter creates phase variation so labels are not constant.
5. Bottleneck labels are counterfactual removals, not hand-written heuristics.
6. Confidence intervals are bootstrap intervals over the projected test or
   shift samples.

## Alternatives considered

- **Keep per-task datasets.** Rejected: duplication and weak cross-task
  comparability.
- **Store only the vector view.** Rejected: grid and entity comparisons are
  first-class.
- **Use random train/test splits.** Rejected for the benchmark: scenario
  composition is the point.
- **Hand-write bottleneck labels.** Rejected: counterfactual labels are the
  interesting object.

## Consequences

- One 46-episode recording feeds six offline projections and two control tasks.
- The dataset is larger per episode but generated once.
- Task cards must document which view and target they use.
- The shared writer and projection layer become part of the benchmark contract.
- M4 must not change the benchmark dataset format without a new benchmark
  version.
