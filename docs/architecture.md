# Architecture

This document describes the code architecture. M1–M4 implement the core,
factory, vector/grid/entity observations, shared episode recordings, task
projections, the line-building control environment, recorder, harness,
`factory-v0.1` benchmark candidate, read-only viewer, replay player, playable
control client, and demonstration pipeline. M5 is expansion mechanics.

## Layers

```
core/          generic engine: tick scheduler, events, RNG, hashing, config
worlds/        world content: factory state, systems, generator, recipes
obs/           observation adapters (pure functions of state)
tasks/         task adapters: labels, rewards, termination, splits, metrics
env/           Gymnasium-style environment facade
record/        recorder, replay, dataset writer, manifest
harness/       baselines, training, evaluation, cost accounting, reports
render/        viewer; reads state or replay; never mutates
cli/           command-line entry points
```

Dependency direction is one-way:

```
core <- worlds <- obs/tasks <- env <- record/harness/render/cli
```

Nothing in `core`, `worlds`, `obs`, or `tasks` imports `torch`, `pygame`, or the
harness. The core must run on a machine with only the standard library.

## Proposed repo layout

```text
src/fabline/
  core/
    config.py          # typed configs, TOML loading, unknown-key rejection
    rng.py             # seeded generator, serializable state
    events.py          # typed event records
    hashing.py         # deterministic state hash
    scheduler.py       # fixed-tick loop and phase ordering
    version.py         # version pins and compatibility checks
  worlds/
    factory/
      state.py         # WorldState, Entity, PowerSource, Tile, Item
      faults.py        # opt-in FaultConfig
      power.py         # opt-in PowerConfig and activity-gated demand
      systems.py       # machines, logistics, delivery, metrics
      recipes.py       # data-driven recipes and entity definitions
      generator.py     # procedural layouts and scenarios
      actions.py       # build/remove/rotate validation
      labels.py        # throughput, bottleneck, next-state, fault targets
  obs/
    grid.py
    entities.py
    vector.py
    sensors.py         # wear/temperature/vibration/acoustic/faulted
    power.py           # aggregate and spatial power views
    interaction.py     # fault + power control observation
    pixels.py
    text.py
    multiview.py
  tasks/
    base.py
    throughput.py
    next_state.py
    shared.py          # shared episode recording and projections
    control_dynamics.py
    fault_prediction.py
    power.py           # brownout prediction
    splits.py
  env/
    api.py             # reset/step/observe/render contract
    control.py         # line-building environment
    fault_recovery.py  # two-action noop/repair environment
    power_allocation.py # three-action power priority environment
    fault_power.py     # four-action repair + priority environment
  record/
    replay.py
    writer.py          # per-task debug datasets
    shared_writer.py   # shared episodes and dataset cards
    human.py           # human/scripted demo writer and loader
    manifest.py
  harness/
    baselines.py
    graph_models.py    # message-passing feature baseline
    metrics.py
    stats.py           # bootstrap confidence intervals
    shared_data.py     # load shared episodes and project tasks
    shared_suite.py    # factory-v0.1 benchmark runner
    human_demos.py     # scripted demos and behavior cloning
    faults.py          # fault-mechanic debug benchmark
    fault_recovery.py  # recovery policies and report
    power.py           # power-grid debug benchmark
    power_allocation.py # allocation policies and report
    fault_power.py     # fault + power policies and report
    control.py
    report.py
  render/
    factory_view.py    # read-only pygame view
    app.py             # watch, replay, play, screenshot, demos
  cli/
    main.py
```

`tests/` mirrors the layers: `unit/`, `property/`, `golden/`, `integration/`,
`perf/`.

## State and mutation

- `WorldState` is a typed dataclass with explicit fields.
- Systems mutate state only inside their phase, in the order defined in
  [`world.md`](world.md).
- Entity identity is a monotonically increasing integer; IDs are never reused.
- `WorldState.clone()` exists for counterfactual branches and planning. It must
  be cheap enough for the tasks that need it.
- The RNG is an explicit object stored in the state. Do not use module-level
  random functions.
- State hashing is deterministic and versioned. It covers all fields that affect
  future transitions.

## Configuration

- Typed dataclasses with defaults.
- TOML files; unknown keys are rejected loudly.
- Config hashes are recorded in every episode and report.
- Content (recipes, entity definitions, generator parameters) lives in data files
  where practical.

## Determinism

The factory MVP uses integer arithmetic for items, ticks, positions, and
buffers. This avoids most floating-point drift.

Rules:

- fixed tick order;
- deterministic conflict resolution by stable ID;
- no unordered iteration in systems that affect state;
- no wall-clock or environment-dependent behavior;
- seeded RNG with serializable state;
- state hash at a configurable interval;
- replay validation fails at the first divergent tick.

## Performance

Performance policy (hardware-relative, because development machines vary):

- **Reference target:** 10k factory ticks/s headless for a 32×32 world with 64
  entities on the recorded reference machine;
- **Supported floor:** 1k ticks/s on any machine used for development; if a
  machine is below the floor, reduce the episode size or optimize before
  proceeding;
- **Regression gate:** no more than a 20% same-machine slowdown against a stored
  baseline; absolute rates are recorded with hardware, not assumed;
- 100k-step dataset generation should be practical on the development machine;
- episode replay should be at least as fast as generation;
- memory under 100 MB for a 10k-step episode with vector observations.

The perf test records the machine and rate. It enforces the floor and the
same-machine regression; the 10k reference target is reported, not asserted on
unknown hardware.

Approach:

1. Keep the core pure Python and simple.
2. Vectorize only measured hot paths with NumPy.
3. Consider Numba or a Rust extension only if profiling shows a real bottleneck.
4. Keep observation materialization out of the tick loop.

Do not optimize before the perf test exists.

## Environment API

The facade should be small and stable:

```python
env = FactoryEnv(config, task)
obs, info = env.reset(seed=...)
obs, reward, terminated, truncated, info = env.step(action)
state = env.state()
env.render(mode="rgb_array")  # optional
```

The API should be compatible in spirit with Gymnasium, but the testbed's
contracts are defined in [`interface.md`](interface.md). Do not let a framework
dictate the data model.

## Extension points

- **New world** — implement the world protocol and register it. Requires an ADR.
- **New observation adapter** — pure function of state plus a spec and tests.
- **New task adapter** — a projection over episodes plus a task card.
- **New baseline** — implement the harness interface; declare compute budget.
- **New mechanic** — RFC, tests, observation impact, data impact, ADR if it
  changes the world contract.

## Dependencies

Core and factory:

- Python 3.12 standard library;
- NumPy only where arrays are genuinely useful.

Optional extras:

- `render`: Pygame-ce or a similar lightweight viewer;
- `train`: PyTorch, scikit-learn, and a plotting/reporting stack;
- `data`: PyArrow/Polars and Zarr for large datasets.

Keep optional dependencies out of the core import path.

## What not to build yet

- an ECS framework;
- a plugin system with dynamic discovery;
- a distributed simulator;
- a custom binary format;
- a web frontend;
- a Rust core.

These are legitimate later choices if a measured need appears. The first
milestone needs a small, testable loop.
