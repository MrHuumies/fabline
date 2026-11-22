# FABLINE

**Factory Agent Benchmark for Learning, Interaction, and Evaluation.**

FABLINE is a deterministic, inspectable factory world. It generates reproducible
multi-view data and a method-agnostic benchmark harness for learning methods,
representations, and theories.

The world is small on purpose: a fixed-timestep factory with miners, belts,
furnaces, assemblers, depots, optional machine faults, and an optional power
grid. The same episode can be viewed as a grid, entity graph, vector, sensor
field, or power grid.

## Quickstart

```bash
git clone https://github.com/MrHuumies/fabline
cd fabline
./scripts/bootstrap.sh

.venv/bin/python -m pytest -q
.venv/bin/python -m fabline smoke --ticks 200
.venv/bin/python -m fabline shared-suite --out results/factory-v0.1
```

Generate a small dataset and run the M1 benchmark:

```bash
.venv/bin/python -m fabline dataset --episodes 10 \
  --out datasets/example
.venv/bin/python -m fabline benchmark \
  --dataset datasets/example --out results/example
```

Optional viewer:

```bash
make render-install
.venv/bin/python -m fabline render --config configs/factory_shared.toml
```

## Mechanics

- **Factory core:** miners, belts, furnaces, assemblers, depots, build/remove/
  rotate actions, scenario splits, and exact replays.
- **Faults (opt-in):** wear, downtime, repair, diagnostic sensors, fault
  prediction, and fault recovery.
- **Power (opt-in):** pre-placed generators, activity-gated demand, brownouts,
  power views, brownout prediction, allocation control, and calibration metrics
  (Brier, NLL, ECE).
- **Stochastic power:** seeded load/capacity variation for uncertain prediction
  and control.
- **Wired power (opt-in):** wire-edge graph with loops, bridge and loop faults,
  a cascade-size prediction task, budgeted wire repair with repair time, preventive wire maintenance from a degradation
  warning, preventive machine maintenance before wear faults, and maintenance-threshold
  selection.
- **Partial observability:** feature dropout, grid fog, delayed observations,
  and a masked feature-window throughput task.
- **Architecture baselines:** sequence models, grid CNN, and end-to-end MPNN
  against flattened and feature-engineering baselines.
- **Risk-sensitive contract:** choose a delivery target under stochastic power;
  mean and CVaR objectives separate; the replicated gain is +13 to +17 CVaR for
  a roughly 5-point mean premium.

Every mechanic is opt-in. The frozen `factory-v0.1` benchmark is action-free and
does not depend on faults or power.

## Benchmark

The frozen benchmark is [`factory-v0.1`](benchmarks/factory-v0.1/card.md):

- 46 shared episodes, scenario-based train/val/test/shift splits;
- throughput, next-state, masked-grid, bottleneck, control, and
  control-dynamics projections;
- baseline families with seeds, confidence intervals, and replay validation.

The expected summary is in
[`benchmarks/factory-v0.1/expected/summary.json`](benchmarks/factory-v0.1/expected/summary.json).
The current coverage review is in
[`docs/coverage-review-0.1.2.md`](docs/coverage-review-0.1.2.md).
Small library-version differences are acceptable; headline ordering should be
stable.

## Example data

A small pre-generated dataset is attached to the release. It contains a core
factory sample, a faults sample, and a power sample, each with observations,
labels, manifests, replays, and dataset cards.

You can also generate the core sample yourself:

```bash
.venv/bin/python examples/generate_data.py --out datasets/example
```

## Documentation

- [`project_intent.md`](project_intent.md) — goals and non-goals.
- [`docs/testbed.md`](docs/testbed.md) — what the testbed is for.
- [`docs/world.md`](docs/world.md) — factory mechanics.
- [`docs/coverage-map.md`](docs/coverage-map.md) — model/benchmark coverage and
  candidate mechanics.
- [`docs/interface.md`](docs/interface.md) — state, observation, and action
  contracts.
- [`docs/architecture.md`](docs/architecture.md) — code layout.
- [`docs/tasks/`](docs/tasks/) — task cards.
- [`docs/datasets/`](docs/datasets/) — dataset cards.
- [`docs/experiments/`](docs/experiments/) — selected experiment records.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — invariants and change protocol.

## Status and caveats

This is a research sandbox, not a product or a leaderboard. The benchmark is
small: 6 test and 6 shift episodes, so confidence intervals are wide. Some tasks
are saturated. Faults and power are opt-in and do not change the frozen
benchmark. See the caveats in the benchmark card and task cards.

## License

- Code: Apache-2.0 — [`LICENSE`](LICENSE).
- Documentation, cards, generated datasets, and figures: CC-BY-4.0 —
  [`LICENSE-docs`](LICENSE-docs).
- Attribution: “FABLINE by MrHuumies” is sufficient for CC-BY-4.0 material.

See [`NOTICE`](NOTICE).
