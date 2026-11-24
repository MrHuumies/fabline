# Testing and determinism

The simulation is the foundation. Test it directly; do not test it through the
renderer or a trained model.

## Test pyramid

| Layer | What it checks | Speed |
|---|---|---|
| Unit | One system or adapter in isolation | Fast |
| Property | Invariants over generated inputs and seeds | Fast |
| Golden | A small scenario produces an exact trace/hash | Fast |
| Integration | Core + task + recorder + replay end-to-end | Medium |
| Determinism | Same seed + actions = same hashes | Medium |
| Perf | Throughput and memory budgets | Slow, nightly |

## Core invariants

Test these for every mechanic:

- items are conserved except at miners (sources) and depots (sinks);
- a belt tile holds at most one item;
- no two entities occupy one tile;
- a machine never crafts without inputs or with a full output buffer;
- entity IDs are unique and stable;
- the depot and rock are never removed;
- actions either succeed or return a typed error with no partial mutation;
- buffers and counters stay within bounds;
- the state hash changes only when the state changes;
- the same seed and action log produce the same hash sequence;
- the renderer does not mutate state.

## Property tests

Use Hypothesis for:

- arbitrary build/remove/rotate sequences on small grids;
- arbitrary item flows through belts and machines;
- invalid actions (out of bounds, occupied tiles, wrong entity type);
- seed sweeps over the generator;
- replay round-trips.

A property test should state the invariant, not a specific expected value.

## Golden tests

Small scenarios with fixed seeds:

- a miner → belt → furnace → belt → depot line;
- a belt merge conflict;
- a full output buffer blocking a machine;
- a removed belt spilling no items;
- a replay of a 100-tick episode.

Assert the full event sequence or a state hash. When the world changes
intentionally, update the golden trace in the same commit and explain why.

## Task tests

For every task:

- label/reward is deterministic for a given state and seed;
- train/val/test splits are disjoint;
- no label leakage through observations;
- the trivial baseline runs;
- the task card matches the implementation;
- the metric is computed on the declared split only.

## Data tests

- manifest versions match the code;
- dataset card exists;
- replay validation passes on a sample;
- view shapes and masks match the observation spec;
- no NaN/Inf in materialized arrays;
- cache keys include all version components.

## Determinism

- Fixed tick order and conflict resolution.
- Seeded RNG only; no global random calls.
- Stable IDs; never index entities by list position.
- No wall-clock or environment-dependent state.
- Integer arithmetic in the factory MVP.
- State hash at a configurable interval.
- Replay failure reports the first divergent tick and both hashes.

## Performance budgets

Performance is hardware-relative:

- **Reference target:** 10k factory ticks/s headless, 32×32, 64 entities, on the
  recorded reference machine;
- **Supported floor:** 1k ticks/s on any development machine; below that, reduce
  the episode size or optimize before proceeding;
- **Regression gate:** no more than a 20% same-machine slowdown against a stored
  baseline;
- 100k-step dataset generation should be practical on the development machine;
- replay should be at least as fast as generation;
- under 100 MB memory for a 10k-step vector-observation episode.

The perf test records hardware and rate, enforces the floor and the same-machine
regression, and reports the reference target. Do not assert absolute throughput
on unknown hardware. A same-machine regression is a test failure.

## CI

- lint and type check;
- unit, property, and golden tests;
- a short headless integration run;
- replay validation;
- docs link check and card presence;
- a cheap `factory-v0.2` regression check (`--skip-planning
  --skip-diagnostics`) on every push;
- a scheduled full `factory-v0.2` check;
- nightly perf and benchmark smoke.

No GPU is required for the core test suite.

## Debugging order

1. Headless first. If it fails headless, the renderer is not the problem.
2. Check the event log around the failure.
3. Check the state hash at the last good tick.
4. Reproduce from seed + action log.
5. Reduce to a minimal scenario and add a golden test.
6. Only then inspect the renderer or a model.

## What not to test with TDD

- art and layout aesthetics;
- exact rendered pixels before the renderer is stable;
- learned model quality (use benchmark reports, not unit tests).

Those get smoke tests and manual review, not brittle assertions.
