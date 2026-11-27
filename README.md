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
.venv/bin/python -m fabline wizard
.venv/bin/python -m fabline replay-browser --root datasets --limit 20
.venv/bin/python -m fabline task-cards
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
- **Wizard:** a stdlib-only interactive runner for smoke, dataset, shared-suite,
  benchmark, and result-summary workflows; it previews commands and supports
  `--dry-run`.
- **Decentralized triage (debug):** private per-crew views and tabular Q
  baselines; the task is not in the frozen benchmark.
- **Planning (debug):** true-simulator CEM and a learned transition-model CEM
  on the three-bridge triage task.
- **Orders (0.4.0):** opt-in gear/component production mix, seeded orders with
  deadlines/values, order control, and five-block order planning.
- **Assembly edge (0.6.0):** opt-in per-assembler recipe tree
  (`INGOT + COMPONENT -> 2 GEAR`), component logistics, a fixed two-feed
  assembly cell, and four frozen tasks: control, planning, BOM forecast, and
  recipe intervention.

Every mechanic is opt-in. `factory-v0.1` through `factory-v0.4` remain frozen
for provenance.

## Benchmark

The current benchmark is [`factory-v0.5`](benchmarks/factory-v0.5/card.md), the
assembly-edge release:

- four assembly tasks: control, planning, BOM forecast, and recipe intervention;
- a fixed two-feed cell with per-assembler recipes;
- public baselines and gates for each task;
- a checked-in expected summary and CI check.

```bash
.venv/bin/python -m fabline assembly-suite --out results/factory-v0.5
```

The expected summary is in
[`benchmarks/factory-v0.5/expected/summary.json`](benchmarks/factory-v0.5/expected/summary.json).
`factory-v0.4` keeps the eight-task coverage suite, `factory-v0.3` keeps the
12-task core, and the earlier benchmarks remain immutable.

The **factory-v0.4 coverage suite** is also available:

```bash
.venv/bin/python -m fabline coverage-suite --out results/factory-v0.4-coverage
```

It adds an eight-task coverage tier (`reliability-contract`,
`partial-throughput`, `wired-cascade`, `crew-schedule`, `crew-triage`,
`preventive-wire`, `recipe-choice`, `maintenance-threshold`), public structured
baselines (CNN, MPNN, GRU, Transformer), and a challenge-task list for
follow-up. The suite is **frozen** as `factory-v0.4`; wired-cascade is a
diagnostic, not a headline score. See
[`benchmarks/factory-v0.4/card.md`](benchmarks/factory-v0.4/card.md).
The current coverage map is in
[`docs/coverage-map.md`](docs/coverage-map.md); the
[0.5.0 review](docs/coverage-review-0.5.0.md) records the coverage release, and
the [`factory-v0.5` freeze review](benchmarks/factory-v0.5/freeze-review.md)
records the assembly suite. Cross-task cost is in the
[`efficiency table`](docs/efficiency.md).
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
