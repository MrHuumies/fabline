# Changelog

All notable changes to FABLINE are recorded here. World and benchmark versions
are pinned separately; see [`benchmarks/factory-v0.1/card.md`](benchmarks/factory-v0.1/card.md).

## [Unreleased]

- Add the 0.1.2 coverage review and next-slice recommendation.

## [0.1.2] — 2026-11-22

P1 wired power and preventive maintenance. The frozen `factory-v0.1` benchmark is
unchanged.

### Wired power

- opt-in wire-edge topology with loops, bridge/loop faults, and cascade-size
  prediction (0032);
- budgeted wire repair (0033) and timed repair (0034);
- preventive wire maintenance from a degradation warning (0035).

### Preventive maintenance

- machine-wear maintenance before the fault threshold (0037);
- maintenance-threshold selection (0038);
- pilot negatives for risk-score noise (0036) and contextual thresholds (0039).

### Tooling and docs

- new CLI commands: `wire-repair`, `wire-maintenance`, `preventive-fault`, and
  `preventive-threshold`;
- RFCs 0007–0009, ADRs 0017–0019, task and dataset cards.

## [0.1.1] — 2026-11-21

P0 model coverage after 0.1.0. The frozen `factory-v0.1` benchmark is unchanged.

### Prediction and calibration

- Brier, NLL, and ECE calibration metrics for the stochastic power benchmark.

### Partial observability

- deterministic feature-dropout, grid-fog, and delayed-observation adapters;
- masked feature-window throughput task with a single-frame and four-frame view.

### Architecture baselines

- sequence models on the masked-window task;
- grid CNN on clear and moving-fog views;
- end-to-end MPNN on the entity graph, against flattened and `graph_mp`
  baselines.

### Risk-sensitive control

- reliability-contract task under stochastic power;
- corrected episode sampling and a unique, interleaved evaluation design;
- replicated CVaR gain of roughly 13–17 points for a roughly 5-point mean
  premium. The task is a P0 benchmark candidate outside frozen `factory-v0.1`.

### Docs

- coverage map and P0 experiment summaries;
- Apache-2.0 code; CC-BY-4.0 docs, cards, and synthetic data.

## [0.1.0] — 2026-11-21

First public release candidate.

### Core

- deterministic factory world with fixed tick order, stable entity IDs, seeded
  generation, canonical state hashing, and exact replay validation;
- headless-first core with optional Torch, scikit-learn, and pygame extras;
- `factory-v0.1` frozen benchmark: 46 shared episodes, scenario splits,
  throughput, next-state, masked-grid, bottleneck, control, and
  control-dynamics tasks.

### Mechanics

- opt-in machine faults with wear, downtime, auto-repair, diagnostic sensors,
  fault prediction, repair, and recovery control;
- opt-in power grid with pre-placed generators, activity-gated demand,
  brownouts, power views, brownout prediction, and allocation control;
- seeded stochastic power variation for uncertain prediction and control.

### Tooling and docs

- `fabline` CLI for smoke, datasets, benchmarks, suites, rendering, demos,
  behavior cloning, faults, power, allocation, and replay validation;
- make targets for the same paths;
- task cards, dataset cards, ADRs, RFCs, and selected experiment summaries.

### License

Code: Apache-2.0. Documentation, benchmark cards, and synthetic datasets:
CC-BY-4.0. See `LICENSE`, `LICENSE-docs`, and `NOTICE`.

### Known limitations

- The frozen benchmark is small: 6 test and 6 shift episodes. CIs are wide.
- Some tasks are saturated; do not present them as hard benchmarks.
- Faults and power are opt-in and do not change `factory-v0.1`.
- The viewer is functional, not polished.
