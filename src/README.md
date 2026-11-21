# Source layout

This directory contains the `fabline` package. M1 implements the core factory,
grid/vector observations, the throughput task, replay, and the benchmark
harness. M2 adds entity/graph observations, next-state prediction, the
line-building control environment, tabular Q and behavior cloning, and the
five-task suite. M3 adds shared episode recordings, task projections, scenario
splits, masked-grid and control-dynamics tasks, counterfactual bottleneck
labels, message-passing graph features, bootstrap CIs, and the `factory-v0.1`
benchmark candidate. M4 adds the read-only pygame viewer, replay player,
playable control client, human/scripted demo writer, control replay validation,
and behavior cloning from demos. M5 adds opt-in machine faults, dynamic
diagnostic sensor views, a fault-prediction debug task, a repair action, a
two-action fault-recovery environment, the sensor view-arrival experiments, and
an opt-in power grid with brownouts, seeded load/capacity variation, a
prediction task, and a three-action allocation-control environment; the frozen
benchmark is unchanged.

The layout is documented in [`../docs/architecture.md`](../docs/architecture.md):

```text
src/fabline/
  core/          # engine: config, RNG, events, hashing, scheduler
  worlds/factory # state, systems, recipes, generator, actions, labels
  obs/           # observation adapters
  tasks/         # task adapters and splits
  env/           # reset/step facade
  record/        # recorder, replay, dataset writer
  harness/       # baselines, runners, metrics, reports
  render/        # optional viewer
  cli/           # command-line entry points
```

Keep the core headless and dependency-light. Do not add new mechanics or a
renderer before M2's exit criteria are met.
