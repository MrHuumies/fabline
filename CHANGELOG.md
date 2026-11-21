# Changelog

All notable changes to FABLINE are recorded here. World and benchmark versions
are pinned separately; see [`benchmarks/factory-v0.1/card.md`](benchmarks/factory-v0.1/card.md).

## [Unreleased]

- Add the model/benchmark/mechanic coverage map.

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
